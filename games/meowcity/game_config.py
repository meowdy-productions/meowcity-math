"""
MeowCity - Game Configuration
5-reel, 3-row, 20-payline slot game with cat/city theme.
"""

# ============================================================================
# SYMBOL DEFINITIONS
# ============================================================================

SYMBOLS = {
    "H1": {"name": "Golden Cat",    "index": 0},
    "H2": {"name": "Black Cat",     "index": 1},
    "H3": {"name": "Tabby Cat",     "index": 2},
    "H4": {"name": "Siamese Cat",   "index": 3},
    "H5": {"name": "Calico Kitten", "index": 4},
    "L1": {"name": "Fish",          "index": 5},
    "L2": {"name": "Yarn Ball",     "index": 6},
    "L3": {"name": "Milk Bottle",   "index": 7},
    "L4": {"name": "Paw Print",     "index": 8},
    "WD": {"name": "Wild",          "index": 9},
    "SC": {"name": "Scatter",       "index": 10},
}

SYMBOL_LIST = ["H1", "H2", "H3", "H4", "H5", "L1", "L2", "L3", "L4", "WD", "SC"]

WILD_SYMBOL = "WD"
SCATTER_SYMBOL = "SC"

# ============================================================================
# PAYTABLE (multiplier values per bet-line for N-of-a-kind)
# ============================================================================

PAYTABLE = {
    #          3-Kind  4-Kind  5-Kind
    "WD":   [  100,    400,    2000  ],
    "H1":   [  75,     200,    1000  ],
    "H2":   [  40,     100,    500   ],
    "H3":   [  25,     75,     300   ],
    "H4":   [  20,     50,     200   ],
    "H5":   [  15,     35,     150   ],
    "L1":   [  5,      15,     60    ],
    "L2":   [  5,      12,     50    ],
    "L3":   [  5,      10,     40    ],
    "L4":   [  2,      5,      25    ],
}

# ============================================================================
# SCATTER AWARDS (freespin triggers)
# ============================================================================

SCATTER_FREESPINS = {
    3: 10,
    4: 15,
    5: 20,
}

SCATTER_RETRIGGER = {
    2: 5,
    3: 5,
    4: 10,
    5: 10,
}

# ============================================================================
# PAYLINES (20 lines, each maps reel -> row index 0=top, 1=mid, 2=bot)
# ============================================================================

PAYLINES = [
    [1, 1, 1, 1, 1],   # Line  1: middle
    [0, 0, 0, 0, 0],   # Line  2: top
    [2, 2, 2, 2, 2],   # Line  3: bottom
    [0, 1, 2, 1, 0],   # Line  4: V
    [2, 1, 0, 1, 2],   # Line  5: inverted V
    [0, 0, 1, 0, 0],   # Line  6
    [2, 2, 1, 2, 2],   # Line  7
    [1, 2, 2, 2, 1],   # Line  8
    [1, 0, 0, 0, 1],   # Line  9
    [0, 1, 1, 1, 0],   # Line 10
    [2, 1, 1, 1, 2],   # Line 11
    [1, 0, 1, 0, 1],   # Line 12
    [1, 2, 1, 2, 1],   # Line 13
    [0, 1, 0, 1, 0],   # Line 14
    [2, 1, 2, 1, 2],   # Line 15
    [0, 2, 0, 2, 0],   # Line 16
    [2, 0, 2, 0, 2],   # Line 17
    [1, 0, 2, 0, 1],   # Line 18
    [1, 2, 0, 2, 1],   # Line 19
    [0, 2, 2, 2, 0],   # Line 20
]

NUM_REELS = 5
NUM_ROWS = 3
NUM_LINES = 20

# ============================================================================
# REEL STRIPS - BASEGAME
# ============================================================================

REELS_BASE = [
    # Reel 1 (32 stops)
    ["L4","L3","H5","L2","L1","H4","L3","L4","H3","L2","H5","L1","L4","H2","L3","L2",
     "H1","L4","L1","H5","L3","L2","H4","L1","SC","L4","H3","L2","L3","H5","L1","L4"],
    # Reel 2 (32 stops)
    ["L1","H4","L3","L2","WD","L4","H5","L1","H3","L2","L4","H2","L3","L1","H5","L4",
     "L2","H1","L3","L4","H4","L1","L2","SC","L3","H5","L4","L1","H3","L2","L3","L4"],
    # Reel 3 (32 stops)
    ["H5","L2","L4","H3","L1","L3","WD","L4","H4","L2","H2","L1","L3","H5","L4","L2",
     "H1","L1","L3","L4","SC","L2","H4","L1","L4","H3","L3","L2","H5","L1","L4","L3"],
    # Reel 4 (32 stops)
    ["L3","H5","L1","L4","H4","L2","WD","L3","H3","L1","L4","H2","L2","L3","H5","L4",
     "L1","H1","L2","L4","H4","L3","SC","L1","L4","H3","L2","H5","L3","L1","L4","L2"],
    # Reel 5 (32 stops)
    ["L2","H4","L4","L1","H5","L3","L4","H3","L2","L1","H2","L4","L3","H5","L2","L1",
     "H1","L4","L3","H4","L2","L4","SC","L1","H3","L3","L4","H5","L2","L1","L3","L4"],
]

# ============================================================================
# REEL STRIPS - FREEGAME (higher Wild frequency, Scatters on reels 2-4 only)
# ============================================================================

REELS_FREE = [
    # Reel 1 (28 stops) - Wild cluster at positions 5-7, no Scatter
    ["L4","H5","L2","L1","H4","WD","WD","WD","L2","H2","L1","H5","L3","L4",
     "H1","L2","L1","H4","L3","H5","L4","L1","H3","L2","H2","L3","L4","L1"],
    # Reel 2 (28 stops) - Wild cluster at positions 0-2, singles at 6/12/20, Scatter
    ["WD","WD","WD","L3","H5","L2","WD","L4","H3","L1","H2","L3","WD","L2",
     "H1","L4","SC","L1","H4","L3","WD","H5","L2","L4","H3","L1","L3","L2"],
    # Reel 3 (28 stops) - Wild cluster at positions 1-3, singles at 8/12/20, Scatter
    ["H5","WD","WD","WD","H4","L3","H3","L4","WD","L2","H2","L1","WD","L3",
     "H1","L4","L2","SC","H5","L1","WD","L3","H4","L2","L4","H3","L1","L3"],
    # Reel 4 (28 stops) - Wild cluster at positions 0-2, singles at 6/12/20, Scatter
    ["WD","WD","WD","L1","H4","L2","WD","L4","H3","L1","H2","L3","WD","L2",
     "H1","L4","L1","SC","H4","L3","WD","H5","L2","L4","H3","L1","L3","L2"],
    # Reel 5 (28 stops) - Wild cluster at positions 0-2, singles at 6/12/19, no Scatter
    ["WD","WD","WD","L1","H5","L3","WD","L4","H3","L2","H2","L1","WD","L3",
     "H1","L4","L2","H4","L1","WD","H5","L3","L4","H3","L2","L1","L3","L4"],
]

# Wild multipliers in freegame (applied multiplicatively per wild on a winning line)
WILD_MULTIPLIERS_FREE = [2, 2, 3, 3, 5, 10]

# ============================================================================
# BET MODE CONFIGURATION
# ============================================================================

BET_MODES = {
    "base": {
        "name": "base",
        "cost": 1.0,
        "description": "Base game - 20 lines",
        "auto_close_disabled": False,
        "is_feature": False,
        "is_buybonus": False,
    },
    "bonus": {
        "name": "bonus",
        "cost": 0.0,
        "description": "Free spins mode (triggered from base)",
        "auto_close_disabled": True,
        "is_feature": False,
        "is_buybonus": False,
    },
    "buy_10": {
        "name": "buy_10",
        "cost": 25.0,
        "description": "Buy 10 Free Spins (25x bet)",
        "auto_close_disabled": False,
        "is_feature": False,
        "is_buybonus": True,
        "guaranteed_freespins": 10,
        "scatter_force": 3,
    },
    "buy_15": {
        "name": "buy_15",
        "cost": 40.0,
        "description": "Buy 15 Free Spins (40x bet)",
        "auto_close_disabled": False,
        "is_feature": False,
        "is_buybonus": True,
        "guaranteed_freespins": 15,
        "scatter_force": 4,
    },
    "buy_20": {
        "name": "buy_20",
        "cost": 100.0,
        "description": "Buy 20 Free Spins + Starting 2x Multiplier (100x bet)",
        "auto_close_disabled": False,
        "is_feature": False,
        "is_buybonus": True,
        "guaranteed_freespins": 20,
        "scatter_force": 5,
        "starting_multiplier": 2,
    },
}

# ============================================================================
# BONUS BUY REELS (moderately boosted vs free reels — one wild cluster per reel)
# Wild density ~17% (down from 27%), H:L ratio ~0.85 (down from 1.44).
# Rebalanced so raw RTP stays in optimizer range after the 5000x win cap.
# ============================================================================

REELS_BUYBUY = [
    # Reel 1 (28 stops) - Wild cluster at positions 4-6, single at 17, no Scatter
    ["H1","L2","L3","H5","WD","WD","WD","L4","H2","L1","H3","L2","H4","L3",
     "H5","L1","H1","WD","L4","H3","L2","H4","L1","H2","L3","H1","L4","L1"],
    # Reel 2 (28 stops) - Wild cluster at positions 0-2, singles at 6/20, Scatter at 16
    ["WD","WD","WD","H3","L2","H5","WD","L3","H2","L1","H1","L4","H3","L2",
     "H4","L3","SC","H5","L1","H1","WD","L2","H2","L4","H4","L1","H3","L3"],
    # Reel 3 (28 stops) - Wild cluster at positions 1-3, singles at 8/20, Scatter at 17
    ["H5","WD","WD","WD","H4","L3","H3","L4","WD","L2","H2","L1","H3","L2",
     "H1","L4","H4","SC","H5","L3","WD","H2","L1","H3","L2","H1","L4","L3"],
    # Reel 4 (28 stops) - Wild cluster at positions 0-2, singles at 6/20, Scatter at 17
    ["WD","WD","WD","H1","L2","H4","WD","L4","H3","L1","H2","L3","H5","L2",
     "H1","L4","H4","SC","H3","L1","WD","H5","L3","H2","L4","H3","L2","L1"],
    # Reel 5 (28 stops) - Wild cluster at positions 0-2, singles at 6/19, no Scatter
    ["WD","WD","WD","H1","L2","H5","WD","L4","H3","L2","H2","L1","H4","L3",
     "H1","L4","H5","L2","H3","WD","L1","H4","L3","H2","L4","H1","L3","L1"],
]

# Wild multipliers for bonus-buy freegame (lower ceiling than triggered free game
# so the 5000x cap is the binding constraint rather than multiplier explosion).
WILD_MULTIPLIERS_BUYBUY = [2, 2, 2, 3, 3, 5]

# ============================================================================
# GAME PARAMETERS
# ============================================================================

TARGET_RTP = 0.965
MAX_WIN_MULTIPLIER = 5000
GAME_NAME = "meowcity"
GAME_TITLE = "MeowCity"

# Win level thresholds (multiplier of total bet)
WIN_LEVELS = {
    0: 0,       # No win
    1: 0.01,    # Small win
    2: 5,       # Medium win
    3: 15,      # Big win
    4: 50,      # Mega win
    5: 200,     # Super win
}


class GameConfig:
    """
    Main configuration class for MeowCity, following Stake Engine SDK conventions.
    Inherits pattern from src.Config.Config for use with the math engine.
    """

    def __init__(self):
        self.game_name = GAME_NAME
        self.game_title = GAME_TITLE
        self.num_reels = NUM_REELS
        self.num_rows = NUM_ROWS
        self.num_lines = NUM_LINES
        self.symbols = SYMBOLS
        self.symbol_list = SYMBOL_LIST
        self.wild_symbol = WILD_SYMBOL
        self.scatter_symbol = SCATTER_SYMBOL
        self.paytable = PAYTABLE
        self.paylines = PAYLINES
        self.reels_base = REELS_BASE
        self.reels_free = REELS_FREE
        self.reels_buybuy = REELS_BUYBUY
        self.scatter_freespins = SCATTER_FREESPINS
        self.scatter_retrigger = SCATTER_RETRIGGER
        self.wild_multipliers_free = WILD_MULTIPLIERS_FREE
        self.wild_multipliers_buybuy = WILD_MULTIPLIERS_BUYBUY
        self.bet_modes = BET_MODES
        self.target_rtp = TARGET_RTP
        self.max_win_multiplier = MAX_WIN_MULTIPLIER
        self.win_levels = WIN_LEVELS