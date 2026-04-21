"""
MeowCity - Gamestate
Main simulation entry point. run_spin() is called by create_books() for each simulation.
Follows the Stake Engine SDK gamestate pattern.
"""

import random
from game_config import GameConfig
from game_executables import execute_basegame_spin, execute_bonus_buy_spin


class GameState:
    """
    Manages the state of a single simulation run.
    Each call to run_spin() produces one complete game round result.
    """

    def __init__(self, config: GameConfig, mode: str, sim_id: int, criteria: str = "basegame"):
        self.config = config
        self.mode = mode
        self.sim_id = sim_id
        self.criteria = criteria
        self.book = Book(sim_id)

    def run_spin(self):
        """
        Execute a single simulation.
        This is the main entry point called by the simulation engine.
        Returns the book (simulation result) for this round.
        """
        if self.mode == "base":
            return self._run_base_spin()
        elif self.mode == "bonus":
            return self._run_bonus_spin()
        elif self.mode.startswith("buy_"):
            return self._run_buybuy_spin()
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

    def _run_base_spin(self):
        """Execute a complete basegame round (may include freegame)."""
        events, total_win, base_wins, free_wins = execute_basegame_spin(self.config)

        for event in events:
            self.book.add_event(event)

        max_payout = self.config.max_win_multiplier * 100
        self.book.set_payout(min(total_win, max_payout))
        self.book.base_game_wins = base_wins / 100.0 if base_wins else 0.0
        self.book.free_game_wins = free_wins / 100.0 if free_wins else 0.0

        return self.book.to_dict()

    def _run_bonus_spin(self):
        """
        Execute a bonus-only simulation.
        For the bonus mode, we simulate a direct freegame entry.
        This mode is used for optimizing the freegame RTP independently.
        """
        from game_executables import execute_freegame
        from game_events import (
            freespin_start_event,
            set_total_win_event,
            final_win_event,
        )

        # Award a forced number of freespins based on criteria
        if self.criteria == "max_win":
            total_spins = 20  # Max scatter award
        else:
            total_spins = random.choice([10, 10, 10, 15, 15, 20])

        idx = 0
        self.book.add_event(freespin_start_event(idx, total_spins))
        idx += 1

        free_win, free_events, idx = execute_freegame(self.config, total_spins, idx)
        for event in free_events:
            self.book.add_event(event)

        self.book.add_event(set_total_win_event(idx, free_win))
        idx += 1
        self.book.add_event(final_win_event(idx, free_win))

        self.book.set_payout(free_win)
        self.book.base_game_wins = 0.0
        self.book.free_game_wins = free_win / 100.0 if free_win else 0.0

        return self.book.to_dict()

    def _run_buybuy_spin(self):
        """
        Execute a bonus buy simulation.
        This mode costs N x bet and goes straight into freegame
        with boosted reels and optional starting multiplier.
        """
        events, total_win, base_wins, free_wins = execute_bonus_buy_spin(
            self.config, self.mode
        )

        for event in events:
            self.book.add_event(event)

        max_payout = self.config.max_win_multiplier * 100
        capped_win = min(total_win, max_payout)
        self.book.set_payout(capped_win)
        self.book.base_game_wins = 0.0
        self.book.free_game_wins = free_wins / 100.0 if free_wins else 0.0

        return self.book.to_dict()


class Book:
    """
    Stores simulation results in the format required by the RGS.
    Each book entry must contain: id, events, payoutMultiplier
    """

    def __init__(self, sim_id: int):
        self.sim_id = sim_id
        self.events = []
        self.payout_multiplier = 0
        self.base_game_wins = 0.0
        self.free_game_wins = 0.0

    def add_event(self, event: dict):
        self.events.append(event)

    def set_payout(self, multiplier: int):
        self.payout_multiplier = multiplier

    def to_dict(self):
        """
        Return the required format for RGS books.
        Three key fields are mandatory: id, events, payoutMultiplier
        """
        return {
            "id": self.sim_id,
            "payoutMultiplier": self.payout_multiplier,
            "events": self.events,
            "criteria": "basegame" if self.base_game_wins > 0 or self.free_game_wins == 0 else "freegame",
            "baseGameWins": self.base_game_wins,
            "freeGameWins": self.free_game_wins,
        }
