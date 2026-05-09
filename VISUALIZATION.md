# PyXon — Data Visualization

Every trail closure and player death is recorded as one row in `stats.csv`. A typical session produces roughly **30–50 rows**. This raw data drives all five tabs in the statistics window, opened from the main menu via **Graph**.

---

## Data Recording

All data is saved to `stats.csv` in the project root in append mode — rows accumulate across sessions without overwriting previous runs.

### CSV Fields

| Field | Type | Description |
|-------|------|-------------|
| `event` | string | Type of event (`trail_close` or `player_death`) |
| `level` | int | Sector number when the event occurred |
| `capture_efficiency` | float (%) | Share of playable area captured by this single trail |
| `risk_duration` | float (s) | Time spent outside safe territory during the trail |
| `ghost_proximity` | float (grid units) | Distance to the nearest ghost when the trail ended |
| `input_density` | int | Direction changes made while the trail was active |
| `survival_time` | float (s) | Time elapsed since the previous event |
| `timestamp` | float | Unix epoch time of the event |

### Event Types

| Event | Trigger |
|-------|---------|
| `trail_close` | Player reconnects trail to a wall and captures an area |
| `player_death` | Player loses a life from ghost contact or trail infection |

---

## Stats Window

Open from the main menu by selecting **Graph**. Navigate between tabs by clicking the buttons at the top or pressing keys **1–5**.

**Tabs:** `Summary` → `Capture` → `Risk` → `Density` → `Survival`

---

## 1. Summary

![Summary Tab](descript/graphview/overall.png)

A session overview displayed as six stat cards:

| Card | Description |
|------|-------------|
| TRAILS | Total number of successfully closed trails |
| DEATHS | Total lives lost |
| LEVELS | Number of distinct sectors reached |
| AVG CAPTURE | Mean capture efficiency per trail (%) |
| AVG RISK | Mean time spent exposed per event (s) |
| DEATH RATE | Percentage of all trail attempts that ended in death |

A high death rate combined with low average capture indicates aggressive play that is not paying off. A low death rate with high average capture means the player is taking efficient, well-timed cuts.

> **Source:** All rows in `stats.csv`. Trails from `trail_close` events, deaths from `player_death` events.

---

## 2. Capture Efficiency

![Capture Efficiency](descript/graphview/capture.png)

A bar chart showing how much territory each trail claimed, in chronological order.

- **X-Axis:** Trail attempt number
- **Y-Axis:** Area captured (% of playable grid)
- **Bar colors:** Green (≥ 15%), yellow (5–14%), red (< 5%)
- **Teal line:** Rolling average trend
- **Dashed line:** Session average

High early bars followed by smaller ones typically mean the player captured easy open areas first, then was forced into smaller riskier cuts. An upward trend line suggests improving strategy over the session.

> **Source:** `capture_efficiency` column from `trail_close` rows. Logged in `GridManager.flood_fill()`.

---

## 3. Risk Duration

![Risk Duration](descript/graphview/risk.png)

A line chart showing how long the player stayed outside safe territory for each trail attempt, grouped by sector level.

- **X-Axis:** Trail attempt number within the level
- **Y-Axis:** Seconds spent outside safe territory
- **Each line = one level**, color-coded
- **Dotted line:** Overall session average

Longer risk durations generally correlate with larger captures but also more deaths. Comparing lines across levels shows whether the player becomes bolder or more cautious as ghost difficulty increases.

> **Source:** `risk_duration` column from all events. Logged by `StatsLogger` using `on_trail_start` and `on_trail_close` hooks in `Player`.

---

## 4. Input Density

![Input Density](descript/graphview/density.png)

A donut chart showing the proportion of trail attempts broken into three movement complexity categories:

| Segment | Direction Changes | Meaning |
|---------|------------------|---------|
| Straight | 0–2 | Simple straight or single-turn cuts |
| Moderate | 3–5 | Some mid-trail adjustments |
| Complex | 6+ | Highly evasive, agile paths |

The centre shows the total number of trail attempts. A large Complex slice means the player is actively dodging ghosts mid-trail. A dominant Straight slice suggests confident, direct play or a preference for safe predictable routes.

> **Source:** `input_density` column from all events. Logged by `StatsLogger.on_direction_change()` called from `Player`.

---

## 5. Survival Time

![Survival Time](descript/graphview/survival.png)

A histogram showing the distribution of time between consecutive events (trail closures and deaths).

- **X-Axis:** Seconds between events
- **Y-Axis:** Number of occurrences
- **Bar colors:** Interpolated from red (low count) to blue (high count)
- **Dashed line:** Mean
- **Dotted line:** Median
- Outliers above the 99th percentile are excluded to keep the chart readable

A left-skewed distribution (many short intervals) suggests fast, frequent small captures or frequent deaths. A wider spread with a long tail means the player occasionally takes very long ambitious trails mixed with quick routine ones.

> **Source:** `survival_time` column from all events. Logged as the time delta between consecutive events in `StatsLogger`.

---

## Implementation Reference

All visualization logic lives in `core/graph_viewer.py`, launched as a subprocess from `GameEngine._handle_input()`.

| Function | Purpose |
|----------|---------|
| `show_graphs()` | Main entry point — loads CSV and renders the tabbed window |
| `_load_csv()` | Reads `stats.csv`, auto-detects header, casts all field types |
| `_draw_summary()` | Renders the six summary stat cards |
| `_plot_capture()` | Renders the capture efficiency bar chart with trend line |
| `_plot_risk()` | Renders the risk duration line chart per level |
| `_plot_density()` | Renders the input density donut chart |
| `_plot_survival()` | Renders the survival time histogram |