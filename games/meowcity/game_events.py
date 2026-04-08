"""
MeowCity - Game Events
Event structures returned via the RGS play/ API.
Each event has: index, type, and type-specific fields.
"""


def reveal_event(index, board, padding_positions, game_type, anticipation):
    """Board reveal event - shows which symbols appear."""
    return {
        "index": index,
        "type": "reveal",
        "board": board,
        "paddingPositions": padding_positions,
        "gameType": game_type,
        "anticipation": anticipation,
    }


def win_info_event(index, total_win, wins):
    """Win information event - details of all winning combinations."""
    return {
        "index": index,
        "type": "winInfo",
        "totalWin": total_win,
        "wins": wins,
    }


def set_win_event(index, amount, win_level):
    """Set current spin win amount."""
    return {
        "index": index,
        "type": "setWin",
        "amount": amount,
        "winLevel": win_level,
    }


def set_total_win_event(index, amount):
    """Set cumulative win amount for the entire round."""
    return {
        "index": index,
        "type": "setTotalWin",
        "amount": amount,
    }


def final_win_event(index, amount):
    """Final win event - concludes the round."""
    return {
        "index": index,
        "type": "finalWin",
        "amount": amount,
    }


def scatter_win_event(index, count, positions, freespins_awarded):
    """Scatter trigger event - freegame entry."""
    return {
        "index": index,
        "type": "scatterWin",
        "scatterCount": count,
        "positions": positions,
        "freespinsAwarded": freespins_awarded,
    }


def freespin_start_event(index, total_freespins):
    """Marks the start of free spins mode."""
    return {
        "index": index,
        "type": "freespinStart",
        "totalFreespins": total_freespins,
    }


def freespin_update_event(index, current_spin, total_spins, cumulative_win):
    """Update freespin counter during free spins mode."""
    return {
        "index": index,
        "type": "freespinUpdate",
        "currentSpin": current_spin,
        "totalSpins": total_spins,
        "cumulativeWin": cumulative_win,
    }


def freespin_retrigger_event(index, additional_spins, new_total):
    """Retrigger event - additional free spins awarded."""
    return {
        "index": index,
        "type": "freespinRetrigger",
        "additionalSpins": additional_spins,
        "newTotalSpins": new_total,
    }


def freespin_end_event(index, total_win):
    """Marks the end of free spins mode."""
    return {
        "index": index,
        "type": "freespinEnd",
        "totalWin": total_win,
    }


def wild_multiplier_event(index, positions_with_multipliers):
    """
    Wild multiplier reveal in freegame.
    positions_with_multipliers: list of {reel, row, multiplier}
    """
    return {
        "index": index,
        "type": "wildMultiplier",
        "wilds": positions_with_multipliers,
    }


def bonus_buy_event(index, buy_mode, cost_multiplier, freespins, starting_multiplier=1):
    """
    Bonus buy activation event - player purchased direct entry to freegame.
    """
    return {
        "index": index,
        "type": "bonusBuy",
        "buyMode": buy_mode,
        "costMultiplier": cost_multiplier,
        "freespinsAwarded": freespins,
        "startingMultiplier": starting_multiplier,
    }


def global_multiplier_event(index, multiplier):
    """
    Global multiplier update event (used in buy_20 mode and during freegame).
    """
    return {
        "index": index,
        "type": "globalMultiplier",
        "multiplier": multiplier,
    }
