"""
MeowCity - Game Calculations
Handles line-win evaluation, scatter counting, and wild multiplier logic.
"""

import random
from game_config import GameConfig


def evaluate_line_wins(board, config: GameConfig, is_freegame=False, wild_multipliers=None):
    """
    Evaluate all 20 paylines for winning combinations.
    wild_multipliers: optional list of multipliers to use; defaults to config's wild_multipliers_free
    Returns list of win dicts: {symbol, kind, win, positions, multiplier, meta}
    """
    wins = []
    mults = wild_multipliers if wild_multipliers is not None else config.wild_multipliers_free

    for line_idx, payline in enumerate(config.paylines):
        # Get symbols on this payline
        line_symbols = []
        line_positions = []
        for reel in range(config.num_reels):
            row = payline[reel]
            sym = board[reel][row]
            line_symbols.append(sym)
            line_positions.append({"reel": reel, "row": row})

        # Evaluate left-to-right
        win_info = evaluate_single_line(line_symbols, line_positions, config, is_freegame, mults)
        if win_info:
            win_info["lineIndex"] = line_idx
            wins.append(win_info)

    return wins


def evaluate_single_line(line_symbols, line_positions, config: GameConfig, is_freegame=False, wild_multipliers=None):
    """
    Evaluate a single payline for the best winning combination (left to right).
    Wild substitutes for all symbols except Scatter.
    In freegame, wilds carry multipliers that stack multiplicatively.
    wild_multipliers: optional list of multipliers; defaults to config's wild_multipliers_free
    """
    mults = wild_multipliers if wild_multipliers is not None else config.wild_multipliers_free

    # Determine the paying symbol (first non-wild from left)
    pay_symbol = None
    kind = 0
    wild_multiplier_product = 1
    winning_positions = []

    for i in range(config.num_reels):
        sym = line_symbols[i]

        if sym == config.scatter_symbol:
            break  # Scatter breaks the line

        if sym == config.wild_symbol:
            kind += 1
            winning_positions.append(line_positions[i])
            if is_freegame:
                m = random.choice(mults)
                wild_multiplier_product *= m  # multiplicative stacking
        elif pay_symbol is None:
            pay_symbol = sym
            kind += 1
            winning_positions.append(line_positions[i])
        elif sym == pay_symbol:
            kind += 1
            winning_positions.append(line_positions[i])
        else:
            break  # Different symbol breaks the chain

    if kind < 3:
        return None

    # If all wilds, pay as wild
    if pay_symbol is None:
        pay_symbol = config.wild_symbol

    # Look up paytable
    if pay_symbol not in config.paytable:
        return None

    pay_entry = config.paytable[pay_symbol]
    kind_index = kind - 3  # 3-kind=0, 4-kind=1, 5-kind=2

    if kind_index < 0 or kind_index >= len(pay_entry):
        return None

    base_win = pay_entry[kind_index]

    # Apply multiplicative wild multiplier in freegame
    multiplier = wild_multiplier_product if is_freegame else 1

    total_win = base_win * multiplier

    return {
        "symbol": pay_symbol,
        "kind": kind,
        "win": total_win,
        "positions": winning_positions,
        "multiplier": multiplier,
        "meta": {}
    }


def count_scatters(board, config: GameConfig, reels_to_check=None):
    """
    Count scatter symbols on the board.
    reels_to_check: list of reel indices to check (None = all reels)
    Returns: (count, positions)
    """
    count = 0
    positions = []

    check_reels = reels_to_check if reels_to_check else range(config.num_reels)

    for reel in check_reels:
        for row in range(config.num_rows):
            if board[reel][row] == config.scatter_symbol:
                count += 1
                positions.append({"reel": reel, "row": row})

    return count, positions


def get_win_level(total_win_multiplier, config: GameConfig):
    """
    Determine win level based on payout multiplier thresholds.
    """
    level = 0
    for lvl, threshold in sorted(config.win_levels.items()):
        if total_win_multiplier >= threshold:
            level = lvl
    return level


def generate_board(reels, num_rows):
    """
    Generate a random board by picking a random stop on each reel strip.
    Returns board as list of columns: board[reel][row]
    """
    board = []
    for reel_strip in reels:
        stop = random.randint(0, len(reel_strip) - 1)
        column = []
        for r in range(num_rows):
            idx = (stop + r) % len(reel_strip)
            column.append(reel_strip[idx])
        board.append(column)
    return board


def generate_padding_positions(reels, board_stops, num_rows):
    """
    Generate padding symbols above/below the visible board for reel animation.
    Returns list of padding symbols per reel.
    """
    padding = []
    for reel_idx, reel_strip in enumerate(reels):
        stop = board_stops[reel_idx] if board_stops else 0
        above = reel_strip[(stop - 1) % len(reel_strip)]
        below = reel_strip[(stop + num_rows) % len(reel_strip)]
        padding.append({"above": above, "below": below})
    return padding


def generate_board_with_stops(reels, num_rows):
    """
    Generate board and return stops for padding calculation.
    Returns (board, stops)
    """
    board = []
    stops = []
    for reel_strip in reels:
        stop = random.randint(0, len(reel_strip) - 1)
        stops.append(stop)
        column = []
        for r in range(num_rows):
            idx = (stop + r) % len(reel_strip)
            column.append(reel_strip[idx])
        board.append(column)
    return board, stops


def generate_anticipation(board, config: GameConfig):
    """
    Generate anticipation flags per reel (True if scatter appears on previous reels,
    building excitement for potential freegame trigger).
    """
    anticipation = [False] * config.num_reels
    scatter_count = 0
    for reel in range(config.num_reels):
        for row in range(config.num_rows):
            if board[reel][row] == config.scatter_symbol:
                scatter_count += 1
                break
        if scatter_count >= 2 and reel < config.num_reels - 1:
            anticipation[reel + 1] = True
    return anticipation
