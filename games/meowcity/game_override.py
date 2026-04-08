"""
MeowCity - Game Overrides
Override hooks for customizing engine behavior.
Currently MeowCity uses standard lines evaluation with no special overrides.
"""


def override_win_evaluation(wins, board, config):
    """
    Optional override for post-processing win evaluation.
    Can be used to cap wins, apply special multipliers, etc.
    
    For MeowCity: Cap total win at MAX_WIN_MULTIPLIER.
    """
    total = sum(w["win"] for w in wins)
    if total > config.max_win_multiplier:
        # Scale down proportionally
        scale = config.max_win_multiplier / total
        for w in wins:
            w["win"] = int(w["win"] * scale)
    return wins


def override_scatter_check(scatter_count, config, is_freegame=False):
    """
    Optional override for scatter trigger conditions.
    MeowCity uses standard: 3+ in base, 2+ on reels 2-4 in freegame.
    """
    if is_freegame:
        return scatter_count >= 2
    return scatter_count >= 3


def override_board_generation(board, config, game_type):
    """
    Optional override for post-processing board generation.
    Can be used to enforce constraints like max scatters per reel, etc.
    MeowCity: No additional constraints needed.
    """
    return board
