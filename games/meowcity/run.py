"""
MeowCity - Run File
Main entry point for generating all math files required by the Stake Engine RGS.

Usage:
    python3 run.py
"""

import json
import os
import sys
import time
import random
import csv
import shutil
from concurrent.futures import ThreadPoolExecutor

from game_config import GameConfig
from gamestate import GameState

# ============================================================================
# SIMULATION PARAMETERS
# ============================================================================

num_threads = 10
rust_threads = 10
batching_size = 1000
compression = True
profiling = False

num_sim_args = {
    "base": int(1e4),
    "buy_10": int(1e4),
    "buy_15": int(1e4),
    "buy_20": int(1e4),
}

run_conditions = {
    "run_sims": True,
    "run_optimization": True,
    "run_analysis": True,
    "upload_data": False,
}

CRITERIA_DISTRIBUTION = {
    "base": {"basegame": 0.85, "zero_win": 0.05, "freegame_entry": 0.08, "max_win": 0.02},
    "bonus": {"freegame": 0.90, "max_win": 0.10},
}


def assign_criteria(mode, sim_id, total_sims):
    dist = CRITERIA_DISTRIBUTION.get(mode, {"basegame": 1.0})
    cumulative = 0.0
    ratio = sim_id / total_sims
    for criteria, pct in dist.items():
        cumulative += pct
        if ratio < cumulative:
            return criteria
    return list(dist.keys())[-1]


def run_simulation_batch(mode, start_id, count, config):
    results = []
    for i in range(count):
        sim_id = start_id + i
        criteria = assign_criteria(mode, sim_id, num_sim_args[mode])
        gs = GameState(config, mode, sim_id, criteria)
        result = gs.run_spin()
        results.append(result)
    return results


def create_books(config, mode, num_sims):
    print(f"\n{'='*60}")
    print(f"  Simulating mode: {mode} ({num_sims:,} simulations)")
    print(f"{'='*60}")

    all_results = []
    batch_size = max(1, num_sims // num_threads)
    start_time = time.time()

    futures = []
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for t in range(num_threads):
            start_id = t * batch_size + 1
            count = batch_size if t < num_threads - 1 else (num_sims - t * batch_size)
            if count <= 0:
                continue
            future = executor.submit(run_simulation_batch, mode, start_id, count, config)
            futures.append((t, future))

        for thread_id, future in futures:
            batch_results = future.result()
            all_results.extend(batch_results)
            total_payout = sum(r["payoutMultiplier"] for r in batch_results)
            base_w = sum(r.get("baseGameWins", 0) for r in batch_results)
            free_w = sum(r.get("freeGameWins", 0) for r in batch_results)
            thread_rtp = total_payout / (len(batch_results) * 100) if batch_results else 0
            print(f"  Thread {thread_id} finished with {thread_rtp:.3f} RTP. "
                  f"[baseGame: {base_w:.3f}, freeGame: {free_w:.3f}]")

    elapsed = time.time() - start_time
    print(f"\n  Completed {len(all_results):,} simulations in {elapsed:.1f}s")

    all_results.sort(key=lambda x: x["id"])
    write_books(all_results, mode)
    write_lookup_table(all_results, mode)
    write_criteria_table(all_results, mode)
    return all_results


def write_books(results, mode):
    books_dir = os.path.join("library", "books")
    os.makedirs(books_dir, exist_ok=True)
    filepath = os.path.join(books_dir, f"books_{mode}.jsonl")
    with open(filepath, "w") as f:
        for result in results:
            f.write(json.dumps(result, separators=(",", ":")) + "\n")
    print(f"  Written: {filepath}")

    if compression:
        compressed_dir = os.path.join("library", "books_compressed")
        os.makedirs(compressed_dir, exist_ok=True)
        zst_path = os.path.join(compressed_dir, f"books_{mode}.jsonl.zst")
        try:
            import zstandard as zstd
            cctx = zstd.ZstdCompressor(level=3)
            with open(filepath, "rb") as f_in, open(zst_path, "wb") as f_out:
                cctx.copy_stream(f_in, f_out)
            print(f"  Written: {zst_path}")
        except ImportError:
            print(f"  WARNING: zstandard not installed. pip install zstandard")


def write_lookup_table(results, mode):
    lt_dir = os.path.join("library", "lookup_tables")
    os.makedirs(lt_dir, exist_ok=True)
    filepath = os.path.join(lt_dir, f"lookUpTable_{mode}.csv")
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        for result in results:
            writer.writerow([result["id"], 1, result["payoutMultiplier"]])
    print(f"  Written: {filepath}")


def write_criteria_table(results, mode):
    lt_dir = os.path.join("library", "lookup_tables")
    os.makedirs(lt_dir, exist_ok=True)
    filepath = os.path.join(lt_dir, f"lookUpTableIdToCriteria_{mode}.csv")
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        for result in results:
            writer.writerow([result["id"], result.get("criteria", "basegame")])
    print(f"  Written: {filepath}")


def run_optimization(config, mode, results):
    """
    Optimize lookup table weights to hit target RTP of 96.5%.
    
    RGS RTP formula:
      RTP = sum(weight[i] * payoutMultiplier[i]) / (sum(weight[i]) * cost_multiplier * 100)
    
    payoutMultiplier values are in units where 100 = 1.00x the base bet.
    cost_multiplier is 1.0 for base, 50.0 for buy_10, etc.
    
    So for base (cost=1): a payoutMultiplier of 500 means 5.00x win.
    For buy_10 (cost=50): the player pays 50x bet, so RTP = total_return / (50 * 100).
    
    We use binary search on a parameter 'alpha' to adjust weights:
      w[i] = 1 / (1 + alpha * payoutMultiplier[i])   (to lower RTP)
      w[i] = 1 + alpha * payoutMultiplier[i]           (to raise RTP)
    """
    print(f"\n  Optimizing mode: {mode}")
    cost = config.bet_modes[mode]["cost"]
    target = config.target_rtp  # 0.965
    
    payouts = [r["payoutMultiplier"] for r in results]
    n = len(payouts)
    
    # Compute RTP given weights
    def rtp_from_weights(weights):
        tw = sum(weights)
        wp = sum(w * p for w, p in zip(weights, payouts))
        return wp / (tw * cost * 100.0)
    
    # Uniform RTP
    raw_rtp = rtp_from_weights([1.0] * n)
    print(f"  Raw RTP (uniform): {raw_rtp*100:.4f}%")
    print(f"  Target RTP: {target*100:.2f}%")
    
    if abs(raw_rtp - target) < 0.0001:
        print(f"  Already at target, using uniform weights.")
        int_weights = [1000000000] * n
    elif raw_rtp > target:
        # RTP too high -> suppress high-payout sims
        # w[i] = 1 / (1 + alpha * p[i])
        def rtp_suppress(alpha):
            ws = [1.0 / (1.0 + alpha * max(p, 0)) for p in payouts]
            return rtp_from_weights(ws)
        
        lo, hi = 0.0, 1.0
        while rtp_suppress(hi) > target:
            hi *= 10.0
            if hi > 1e15:
                break
        
        for _ in range(500):
            mid = (lo + hi) / 2.0
            r = rtp_suppress(mid)
            if abs(r - target) < 1e-9:
                break
            if r > target:
                lo = mid
            else:
                hi = mid
        
        alpha = (lo + hi) / 2.0
        float_weights = [1.0 / (1.0 + alpha * max(p, 0)) for p in payouts]
    else:
        # RTP too low -> boost high-payout sims
        # w[i] = 1 + alpha * p[i]
        def rtp_boost(alpha):
            ws = [1.0 + alpha * max(p, 0) for p in payouts]
            return rtp_from_weights(ws)
        
        lo, hi = 0.0, 1.0
        while rtp_boost(hi) < target:
            hi *= 10.0
            if hi > 1e15:
                break
        
        for _ in range(500):
            mid = (lo + hi) / 2.0
            r = rtp_boost(mid)
            if abs(r - target) < 1e-9:
                break
            if r < target:
                lo = mid
            else:
                hi = mid
        
        alpha = (lo + hi) / 2.0
        float_weights = [1.0 + alpha * max(p, 0) for p in payouts]
    
    if abs(raw_rtp - target) >= 0.0001:
        # Scale to uint64 range
        max_w = max(float_weights)
        min_w = min(float_weights)
        scale = 1e9 / max_w if max_w > 0 else 1
        int_weights = [max(1, int(w * scale)) for w in float_weights]
    
    # Verify final RTP
    verified_rtp = rtp_from_weights(int_weights)
    print(f"  Optimized RTP: {verified_rtp*100:.4f}%")
    
    diff = abs(verified_rtp - target) * 100
    if diff > 0.5:
        print(f"  WARNING: RTP deviation {diff:.2f}% from target!")
    else:
        print(f"  OK: RTP within {diff:.4f}% of target")
    
    # Write optimized lookup table
    lt_dir = os.path.join("library", "lookup_tables")
    filepath = os.path.join(lt_dir, f"lookUpTable_{mode}_0.csv")
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        for i, r in enumerate(results):
            writer.writerow([r["id"], int_weights[i], r["payoutMultiplier"]])
    print(f"  Written: {filepath}")


def generate_configs(config):
    configs_dir = os.path.join("library", "configs")
    os.makedirs(configs_dir, exist_ok=True)

    config_fe = {
        "gameName": config.game_name, "gameTitle": config.game_title,
        "numReels": config.num_reels, "numRows": config.num_rows, "numLines": config.num_lines,
        "symbols": config.symbol_list,
        "symbolInfo": {s: {"name": d["name"], "index": d["index"]} for s, d in config.symbols.items()},
        "wildSymbol": config.wild_symbol, "scatterSymbol": config.scatter_symbol,
        "paytable": config.paytable, "paylines": config.paylines,
        "scatterFreespins": {str(k): v for k, v in config.scatter_freespins.items()},
        "winLevels": {str(k): v for k, v in config.win_levels.items()},
        "maxWin": config.max_win_multiplier,
        "betModes": {
            name: {
                "name": info["name"],
                "cost": info["cost"],
                "description": info["description"],
                "isBuybonus": info.get("is_buybonus", False),
                "guaranteedFreespins": info.get("guaranteed_freespins", 0),
                "startingMultiplier": info.get("starting_multiplier", 1),
            }
            for name, info in config.bet_modes.items()
        },
    }
    with open(os.path.join(configs_dir, "config_fe.json"), "w") as f:
        json.dump(config_fe, f, indent=2)

    config_be = {
        "gameName": config.game_name,
        "modes": [{"name": m["name"], "cost": m["cost"]} for m in config.bet_modes.values()],
        "targetRtp": config.target_rtp, "maxWin": config.max_win_multiplier,
    }
    with open(os.path.join(configs_dir, "config.json"), "w") as f:
        json.dump(config_be, f, indent=2)

    config_math = {
        "gameName": config.game_name, "targetRtp": config.target_rtp,
        "modes": {n: {"cost": m["cost"], "numSimulations": num_sim_args.get(n, 0)} for n, m in config.bet_modes.items()},
    }
    with open(os.path.join(configs_dir, "config_math.json"), "w") as f:
        json.dump(config_math, f, indent=2)

    print("  Written: config_fe.json, config.json, config_math.json")


def generate_index_file():
    publish_dir = os.path.join("library", "publish_files")
    os.makedirs(publish_dir, exist_ok=True)
    config = GameConfig()
    modes = []
    for name, info in config.bet_modes.items():
        # Skip bonus mode (cost 0) - it's triggered from base, not a standalone RGS mode
        if info["cost"] < 1.0:
            continue
        modes.append({
            "name": name,
            "cost": info["cost"],
            "events": f"books_{name}.jsonl.zst",
            "weights": f"lookUpTable_{name}_0.csv",
        })
    index = {"modes": modes}
    filepath = os.path.join(publish_dir, "index.json")
    with open(filepath, "w") as f:
        json.dump(index, f, indent=2)
    print(f"  Written: {filepath}")


def copy_publish_files():
    publish_dir = os.path.join("library", "publish_files")
    os.makedirs(publish_dir, exist_ok=True)
    config = GameConfig()
    for name in config.bet_modes:
        for src, dst in [
            (f"library/books_compressed/books_{name}.jsonl.zst", f"books_{name}.jsonl.zst"),
            (f"library/lookup_tables/lookUpTable_{name}_0.csv", f"lookUpTable_{name}_0.csv"),
        ]:
            dst_path = os.path.join(publish_dir, dst)
            if os.path.exists(src):
                shutil.copy2(src, dst_path)
                print(f"  Copied: {src} -> {dst_path}")
            else:
                print(f"  WARNING: Source not found: {src}")


def run_analysis(config, mode, results):
    print(f"\n  PAR Sheet - Mode: {mode}")
    payouts = [r["payoutMultiplier"] for r in results]
    n = len(payouts)
    zero_wins = sum(1 for p in payouts if p == 0)
    any_wins = n - zero_wins
    total_payout = sum(payouts)
    avg_payout = total_payout / n if n else 0
    max_payout = max(payouts) if payouts else 0
    hit_rate = any_wins / n if n else 0

    brackets = {"0x": 0, "0.01-1x": 0, "1-5x": 0, "5-15x": 0, "15-50x": 0, "50-200x": 0, "200-1000x": 0, "1000x+": 0}
    for p in payouts:
        m = p / 100.0
        if m == 0: brackets["0x"] += 1
        elif m <= 1: brackets["0.01-1x"] += 1
        elif m <= 5: brackets["1-5x"] += 1
        elif m <= 15: brackets["5-15x"] += 1
        elif m <= 50: brackets["15-50x"] += 1
        elif m <= 200: brackets["50-200x"] += 1
        elif m <= 1000: brackets["200-1000x"] += 1
        else: brackets["1000x+"] += 1

    lines = [
        f"{'='*50}", f"  MeowCity PAR Sheet - Mode: {mode}", f"{'='*50}",
        f"  Simulations:  {n:,}", f"  Hit Rate:     {hit_rate:.4f} ({hit_rate*100:.2f}%)",
        f"  Avg Payout:   {avg_payout:.2f} ({avg_payout/100:.4f}x)",
        f"  Max Payout:   {max_payout} ({max_payout/100:.1f}x)",
        f"  Raw RTP:      {total_payout/(n*100):.4f}", "",
        "  Win Distribution:",
    ]
    for bracket, count in brackets.items():
        pct = count / n * 100 if n else 0
        lines.append(f"    {bracket:>12s}: {count:>6,} ({pct:>6.2f}%)")

    report = "\n".join(lines)
    print(report)

    configs_dir = os.path.join("library", "configs")
    os.makedirs(configs_dir, exist_ok=True)
    with open(os.path.join(configs_dir, f"par_sheet_{mode}.txt"), "w") as f:
        f.write(report)


def main():
    print("\n" + "="*60)
    print("  MeowCity - Stake Engine Math SDK")
    print("="*60)

    config = GameConfig()
    all_mode_results = {}

    if run_conditions["run_sims"]:
        for mode, num_sims in num_sim_args.items():
            results = create_books(config, mode, num_sims)
            all_mode_results[mode] = results

    print("\n  Generating configs...")
    generate_configs(config)

    if run_conditions["run_optimization"]:
        for mode, results in all_mode_results.items():
            run_optimization(config, mode, results)

    if run_conditions["run_analysis"]:
        for mode, results in all_mode_results.items():
            run_analysis(config, mode, results)

    print("\n  Generating index.json...")
    generate_index_file()

    print("\n  Preparing publish files...")
    copy_publish_files()

    print("\n" + "="*60)
    print("  Done! Upload library/publish_files/ to Stake Engine ACP.")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
