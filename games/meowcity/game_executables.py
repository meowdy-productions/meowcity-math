"""
MeowCity - Game Executables
High-level game flow functions called by the gamestate.
Handles board generation, win evaluation, scatter checks, and event emission.
"""

import random
from game_config import GameConfig
from game_calculations import (
    evaluate_line_wins,
    count_scatters,
    get_win_level,
    generate_board_with_stops,
    generate_padding_positions,
    generate_anticipation,
)
from game_events import (
    reveal_event,
    win_info_event,
    set_win_event,
    set_total_win_event,
    final_win_event,
    scatter_win_event,
    freespin_start_event,
    freespin_update_event,
    freespin_retrigger_event,
    freespin_end_event,
    wild_multiplier_event,
    bonus_buy_event,
    global_multiplier_event,
)


def execute_base_reveal(config: GameConfig):
    """
    Generate a basegame board and return reveal data.
    """
    board, stops = generate_board_with_stops(config.reels_base, config.num_rows)
    padding = generate_padding_positions(config.reels_base, stops, config.num_rows)
    anticipation = generate_anticipation(board, config)
    return board, padding, anticipation


def execute_free_reveal(config: GameConfig):
    """
    Generate a freegame board and return reveal data.
    """
    board, stops = generate_board_with_stops(config.reels_free, config.num_rows)
    padding = generate_padding_positions(config.reels_free, stops, config.num_rows)
    anticipation = generate_anticipation(board, config)
    return board, padding, anticipation


def execute_basegame_spin(config: GameConfig):
    """
    Execute a complete basegame spin.
    Returns: (events_list, total_payout_multiplier, base_wins, free_wins)
    """
    events = []
    idx = 0

    # 1. Generate board
    board, padding, anticipation = execute_base_reveal(config)

    # 2. Reveal event
    events.append(reveal_event(idx, board, padding, "basegame", anticipation))
    idx += 1

    # 3. Evaluate line wins
    wins = evaluate_line_wins(board, config, is_freegame=False)
    total_line_win = sum(w["win"] for w in wins)

    if wins:
        events.append(win_info_event(idx, total_line_win, wins))
        idx += 1

    # 4. Check for scatter trigger
    scatter_count, scatter_positions = count_scatters(board, config)
    freespins_awarded = 0

    if scatter_count >= 3:
        freespins_awarded = config.scatter_freespins.get(scatter_count, 10)
        events.append(scatter_win_event(idx, scatter_count, scatter_positions, freespins_awarded))
        idx += 1

    # 5. Basegame win
    base_win = total_line_win
    win_level = get_win_level(base_win, config)

    events.append(set_win_event(idx, base_win, win_level))
    idx += 1

    # 6. If freespins triggered, run freegame
    free_win = 0
    if freespins_awarded > 0:
        events.append(freespin_start_event(idx, freespins_awarded))
        idx += 1

        free_win, free_events, idx = execute_freegame(config, freespins_awarded, idx)
        events.extend(free_events)

    # 7. Total win
    total_win = base_win + free_win
    events.append(set_total_win_event(idx, total_win))
    idx += 1

    events.append(final_win_event(idx, total_win))

    return events, total_win, base_win, free_win


def execute_freegame(config: GameConfig, total_spins, start_idx):
    """
    Execute the complete freegame sequence.
    Returns: (total_free_win, events_list, final_event_index)
    """
    events = []
    idx = start_idx
    cumulative_win = 0
    current_spin = 0
    remaining_spins = total_spins

    while current_spin < remaining_spins:
        current_spin += 1

        # Update freespin counter
        events.append(freespin_update_event(idx, current_spin, remaining_spins, cumulative_win))
        idx += 1

        # Generate freegame board
        board, padding, anticipation = execute_free_reveal(config)

        # Reveal
        events.append(reveal_event(idx, board, padding, "freegame", anticipation))
        idx += 1

        # Check for wild multipliers and emit event
        wild_positions = find_wild_positions(board, config)
        if wild_positions:
            wilds_with_mult = []
            for wp in wild_positions:
                m = random.choice(config.wild_multipliers_free)
                wilds_with_mult.append({
                    "reel": wp["reel"],
                    "row": wp["row"],
                    "multiplier": m,
                })
            events.append(wild_multiplier_event(idx, wilds_with_mult))
            idx += 1

        # Evaluate line wins (freegame mode)
        wins = evaluate_line_wins(board, config, is_freegame=True)
        spin_win = sum(w["win"] for w in wins)

        if wins:
            events.append(win_info_event(idx, spin_win, wins))
            idx += 1

        cumulative_win += spin_win
        win_level = get_win_level(spin_win, config)

        events.append(set_win_event(idx, spin_win, win_level))
        idx += 1

        # Check for retrigger (scatters on reels 2,3,4)
        scatter_count, scatter_positions = count_scatters(board, config, reels_to_check=[1, 2, 3])
        if scatter_count >= 2:
            additional = config.scatter_retrigger.get(scatter_count, 5)
            remaining_spins += additional
            events.append(scatter_win_event(idx, scatter_count, scatter_positions, additional))
            idx += 1
            events.append(freespin_retrigger_event(idx, additional, remaining_spins))
            idx += 1

    # End freegame
    events.append(freespin_end_event(idx, cumulative_win))
    idx += 1

    return cumulative_win, events, idx


def find_wild_positions(board, config: GameConfig):
    """Find all wild symbol positions on the board."""
    positions = []
    for reel in range(config.num_reels):
        for row in range(config.num_rows):
            if board[reel][row] == config.wild_symbol:
                positions.append({"reel": reel, "row": row})
    return positions


def execute_buybuy_reveal(config: GameConfig):
    """
    Generate a bonus-buy board using the boosted reel strips.
    """
    board, stops = generate_board_with_stops(config.reels_buybuy, config.num_rows)
    padding = generate_padding_positions(config.reels_buybuy, stops, config.num_rows)
    anticipation = [False] * config.num_reels
    return board, padding, anticipation


def execute_bonus_buy_spin(config: GameConfig, buy_mode_name):
    """
    Execute a complete bonus buy round.
    Skips the basegame entirely and goes straight to freegame.
    The buy_mode config specifies freespin count, cost, and optional starting multiplier.
    Returns: (events_list, total_payout_multiplier, base_wins, free_wins)
    """
    mode_info = config.bet_modes[buy_mode_name]
    guaranteed_spins = mode_info.get("guaranteed_freespins", 10)
    starting_mult = mode_info.get("starting_multiplier", 1)
    cost = mode_info["cost"]

    events = []
    idx = 0

    # 1. Emit bonus buy activation event
    events.append(bonus_buy_event(idx, buy_mode_name, cost, guaranteed_spins, starting_mult))
    idx += 1

    # 2. If starting multiplier > 1, emit global multiplier event
    if starting_mult > 1:
        events.append(global_multiplier_event(idx, starting_mult))
        idx += 1

    # 3. Start freegame
    events.append(freespin_start_event(idx, guaranteed_spins))
    idx += 1

    # 4. Run freegame with boosted reels and optional global multiplier
    free_win, free_events, idx = execute_buybuy_freegame(
        config, guaranteed_spins, idx, starting_mult
    )
    events.extend(free_events)

    # 5. Total win
    total_win = free_win
    events.append(set_total_win_event(idx, total_win))
    idx += 1
    events.append(final_win_event(idx, total_win))

    return events, total_win, 0, free_win


def execute_buybuy_freegame(config: GameConfig, total_spins, start_idx, global_mult=1):
    """
    Execute the freegame sequence for bonus buy mode.
    Uses the boosted REELS_BUYBUY for reveals, applies optional global multiplier.
    Returns: (total_free_win, events_list, final_event_index)
    """
    events = []
    idx = start_idx
    cumulative_win = 0
    current_spin = 0
    remaining_spins = total_spins
    current_global_mult = global_mult
    max_payout = config.max_win_multiplier * 100

    # Use buy-mode specific multipliers (lower ceiling than triggered free game)
    buy_wild_mults = getattr(config, 'wild_multipliers_buybuy', config.wild_multipliers_free)

    while current_spin < remaining_spins:
        current_spin += 1

        # Update freespin counter
        events.append(freespin_update_event(idx, current_spin, remaining_spins, cumulative_win))
        idx += 1

        # Generate board from boosted reels
        board, padding, anticipation = execute_buybuy_reveal(config)

        # Reveal
        events.append(reveal_event(idx, board, padding, "freegame_buybuy", anticipation))
        idx += 1

        # Check for wild multipliers
        wild_positions = find_wild_positions(board, config)
        if wild_positions:
            wilds_with_mult = []
            for wp in wild_positions:
                m = random.choice(buy_wild_mults)
                wilds_with_mult.append({
                    "reel": wp["reel"],
                    "row": wp["row"],
                    "multiplier": m,
                })
            events.append(wild_multiplier_event(idx, wilds_with_mult))
            idx += 1

        # Evaluate line wins (freegame mode with wild multipliers)
        wins = evaluate_line_wins(board, config, is_freegame=True)
        spin_win = sum(w["win"] for w in wins)

        # Apply global multiplier
        spin_win = spin_win * current_global_mult

        if wins:
            # Update win amounts in the wins list to reflect global mult
            for w in wins:
                w["win"] = w["win"] * current_global_mult
                w["meta"]["globalMultiplier"] = current_global_mult
            events.append(win_info_event(idx, spin_win, wins))
            idx += 1

        # Hard cap: stop accumulating once the round max win is reached
        remaining_cap = max(0, max_payout - cumulative_win)
        spin_win = min(spin_win, remaining_cap)
        cumulative_win += spin_win

        win_level = get_win_level(spin_win, config)
        events.append(set_win_event(idx, spin_win, win_level))
        idx += 1

        # Check for retrigger (scatters on reels 2,3,4)
        scatter_count, scatter_positions = count_scatters(board, config, reels_to_check=[1, 2, 3])
        if scatter_count >= 2:
            additional = config.scatter_retrigger.get(scatter_count, 5)
            remaining_spins += additional
            events.append(scatter_win_event(idx, scatter_count, scatter_positions, additional))
            idx += 1
            events.append(freespin_retrigger_event(idx, additional, remaining_spins))
            idx += 1

    # End freegame
    events.append(freespin_end_event(idx, cumulative_win))
    idx += 1

    return cumulative_win, events, idx
