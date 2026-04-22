"""
StatsLogger
-----------
Collects gameplay metrics and writes them to a CSV file.

Metrics tracked:
  - Capture Efficiency  : % of map captured per successful trail closure
  - Risk Duration       : seconds spent outside safe territory per trail
  - Ghost Proximity     : nearest-ghost distance at moment of trail close
  - Input Density       : direction changes made during a trail attempt
  - Survival Time       : seconds between deaths / trail completions 
"""

import csv
import os
import math
import time


_FIELDNAMES = [
    "event",          # "trail_close" | "player_death"
    "level",
    "capture_efficiency",   # float  (%)
    "risk_duration",        # float  (seconds)
    "ghost_proximity",      # float  (pixels or grid units)
    "input_density",        # int    (direction changes)
    "survival_time",        # float  (seconds since last event)
    "timestamp",            # float  (epoch)
]


class StatsLogger:
    def __init__(self, filepath: str = "stats.csv"):
        self.filepath = filepath
        self._ensure_file()

        # ── live-trail accumulators (reset at trail start) ──────────────────
        self._trail_start_time: float | None = None   # when trail started
        self._input_changes: int = 0
        self._last_direction = None

        # ── between-event timer ─────────────────────────────────────────────
        self._last_event_time: float = time.time()

    # ── File helpers ────────────────────────────────────────────────────────

    def _ensure_file(self):
        """Create the CSV with a header row if it doesn't exist yet."""
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=_FIELDNAMES)
                writer.writeheader()

    def _write_row(self, row: dict):
        with open(self.filepath, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=_FIELDNAMES)
            writer.writerow(row)

    # ── Trail lifecycle hooks (called by GameEngine / Player) ───────────────

    def on_trail_start(self, direction):
        """Call when the player first steps onto empty space."""
        self._trail_start_time = time.time()
        self._input_changes = 0
        self._last_direction = direction

    def on_direction_change(self, new_direction):
        """Call every time the player changes direction while trailing."""
        if self._trail_start_time is None:
            return
        if new_direction != self._last_direction:
            self._input_changes += 1
            self._last_direction = new_direction

    def on_trail_close(self, level: int, capture_pct: float,
                       player_pos: tuple, ghosts: list, block_size: int):
        """
        Call when the player reconnects to a wall and the trail is closed.

        Parameters
        ----------
        level          : current level number
        capture_pct    : grid coverage % AFTER the fill (from grid_manager)
        player_pos     : (px, py) pixel position of the player
        ghosts         : list of ghost objects (each has .x, .y)
        block_size     : pixels per grid cell (used to convert proximity)
        """
        now = time.time()
        risk_duration = (now - self._trail_start_time) if self._trail_start_time else 0.0
        survival_time = now - self._last_event_time

        proximity = self._nearest_ghost_distance(player_pos, ghosts)

        self._write_row({
            "event":               "trail_close",
            "level":               level,
            "capture_efficiency":  round(capture_pct, 2),
            "risk_duration":       round(risk_duration, 3),
            "ghost_proximity":     round(proximity / block_size, 2),  # in grid units
            "input_density":       self._input_changes,
            "survival_time":       round(survival_time, 3),
            "timestamp":           round(now, 3),
        })

        self._trail_start_time = None
        self._input_changes = 0
        self._last_event_time = now

    def on_player_death(self, level: int, capture_pct: float,
                        player_pos: tuple, ghosts: list, block_size: int):
        """Call when the player loses a life."""
        now = time.time()
        risk_duration = (now - self._trail_start_time) if self._trail_start_time else 0.0
        survival_time = now - self._last_event_time

        proximity = self._nearest_ghost_distance(player_pos, ghosts)

        self._write_row({
            "event":               "player_death",
            "level":               level,
            "capture_efficiency":  round(capture_pct, 2),
            "risk_duration":       round(risk_duration, 3),
            "ghost_proximity":     round(proximity / block_size, 2),
            "input_density":       self._input_changes,
            "survival_time":       round(survival_time, 3),
            "timestamp":           round(now, 3),
        })

        self._trail_start_time = None
        self._input_changes = 0
        self._last_event_time = now

    # ── Internal helpers ────────────────────────────────────────────────────

    @staticmethod
    def _nearest_ghost_distance(player_pos: tuple, ghosts: list) -> float:
        if not ghosts:
            return 9999.0
        px, py = player_pos
        return min(
            math.hypot(g.x - px, g.y - py)
            for g in ghosts
        )