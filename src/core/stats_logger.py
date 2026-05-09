"""
StatsLogger — collects gameplay metrics and writes them to a CSV file.

Tracked metrics
---------------
capture_efficiency : % of map captured per successful trail closure
risk_duration      : seconds spent outside safe territory per trail
ghost_proximity    : nearest-ghost distance at trail close (in grid units)
input_density      : direction changes made during a trail attempt
survival_time      : seconds between deaths / trail completions
"""

import csv
import os
import math
import time

_FIELDNAMES = [
    "event",              # "trail_close" | "player_death"
    "level",
    "capture_efficiency", # float  (%)
    "risk_duration",      # float  (seconds)
    "ghost_proximity",    # float  (grid units)
    "input_density",      # int    (direction changes)
    "survival_time",      # float  (seconds since last event)
    "timestamp",          # float  (epoch)
]


class StatsLogger:
    def __init__(self, filepath: str = "stats.csv"):
        self.filepath = filepath
        self._ensure_file()
        self._trail_start_time: float | None = None
        self._input_changes: int = 0
        self._last_direction = None
        self._last_event_time: float = time.time()

    # ── file helpers ──────────────────────────────────────────────────────
    def _ensure_file(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", newline="") as f:
                csv.DictWriter(f, fieldnames=_FIELDNAMES).writeheader()
            return
        # File exists but may have been written without a header — fix it
        with open(self.filepath, "r", newline="", encoding="utf-8") as f:
            first = f.readline().split(",")[0].strip()
        if first != "event":
            with open(self.filepath, "r", newline="", encoding="utf-8") as f:
                existing = f.read()
            with open(self.filepath, "w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=_FIELDNAMES).writeheader()
                f.write(existing)

    def _write_row(self, row: dict):
        with open(self.filepath, "a", newline="") as f:
            csv.DictWriter(f, fieldnames=_FIELDNAMES).writerow(row)

    # ── trail lifecycle hooks ─────────────────────────────────────────────
    def on_trail_start(self, direction):
        self._trail_start_time = time.time()
        self._input_changes    = 0
        self._last_direction   = direction

    def on_direction_change(self, new_direction):
        if self._trail_start_time is None:
            return
        if new_direction != self._last_direction:
            self._input_changes    += 1
            self._last_direction    = new_direction

    def on_trail_close(self, level: int, capture_pct: float,
                       player_pos: tuple, ghosts: list, block_size: int):
        now           = time.time()
        risk_duration = (now - self._trail_start_time) if self._trail_start_time else 0.0
        survival_time = now - self._last_event_time
        proximity     = self._nearest_ghost_distance(player_pos, ghosts)
        self._write_row({
            "event":              "trail_close",
            "level":              level,
            "capture_efficiency": round(capture_pct, 2),
            "risk_duration":      round(risk_duration, 3),
            "ghost_proximity":    round(proximity / block_size, 2),
            "input_density":      self._input_changes,
            "survival_time":      round(survival_time, 3),
            "timestamp":          round(now, 3),
        })
        self._trail_start_time = None
        self._input_changes    = 0
        self._last_event_time  = now

    def on_player_death(self, level: int, capture_pct: float,
                        player_pos: tuple, ghosts: list, block_size: int):
        now           = time.time()
        risk_duration = (now - self._trail_start_time) if self._trail_start_time else 0.0
        survival_time = now - self._last_event_time
        proximity     = self._nearest_ghost_distance(player_pos, ghosts)
        self._write_row({
            "event":              "player_death",
            "level":              level,
            "capture_efficiency": round(capture_pct, 2),
            "risk_duration":      round(risk_duration, 3),
            "ghost_proximity":    round(proximity / block_size, 2),
            "input_density":      self._input_changes,
            "survival_time":      round(survival_time, 3),
            "timestamp":          round(now, 3),
        })
        self._trail_start_time = None
        self._input_changes    = 0
        self._last_event_time  = now

    # ── helpers ───────────────────────────────────────────────────────────
    @staticmethod
    def _nearest_ghost_distance(player_pos: tuple, ghosts: list) -> float:
        if not ghosts:
            return 9999.0
        px, py = player_pos
        return min(math.hypot(g.x - px, g.y - py) for g in ghosts)