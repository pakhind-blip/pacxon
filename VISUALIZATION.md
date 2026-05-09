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

## Overall Look

![Overall Dashboard](descript/graphview/overall.png)

The statistics window is a standalone Matplotlib application launched as a subprocess from the main menu. It contains five tabs at the top — Summary, Capture, Risk, Density, and Survival — each displaying a different aspect of the player's recorded gameplay data. The window reads all rows from `stats.csv` automatically on launch and renders each tab on demand when the player clicks or presses the corresponding key (1–5).

---

## Page 1 — Summary

### Component 1: Summary Stat Cards

![Summary Tab](descript/graphview/overall.png)

The Summary tab displays six stat cards giving a session-level overview of the player's performance. The cards show total trails closed, total deaths, number of distinct levels reached, average capture efficiency per trail, average risk duration per event, and overall death rate. A high death rate combined with low average capture points to aggressive play that is not paying off, while a low death rate with high average capture indicates efficient, well-timed cuts through the grid.

---

## Page 2 — Capture Efficiency

### Component 1: Capture Efficiency Bar Chart

![Capture Efficiency](descript/graphview/capture.png)

The Capture tab shows a bar chart of how much territory each trail claimed, plotted in chronological order. Bars are color-coded green for high captures (≥ 15%), yellow for moderate (5–14%), and red for low (< 5%), with a teal rolling average line and a dashed session average overlay. High early bars followed by smaller ones typically indicate the player cleared easy open areas first and was then forced into smaller, riskier cuts, while an upward trend line across the session suggests improving strategy.

---

## Page 3 — Risk Duration

### Component 1: Risk Duration Line Chart

![Risk Duration](descript/graphview/risk.png)

The Risk tab displays a line chart of how long the player stayed outside safe territory for each trail attempt, with each sector level drawn as a separate color-coded line and a dotted overall session average for reference. Longer risk durations generally correlate with larger territory captures but also more deaths. Comparing lines across levels shows whether the player becomes bolder or more cautious as ghost combinations grow more difficult in later sectors.

---

## Page 4 — Input Density

### Component 1: Input Density Donut Chart

![Input Density](descript/graphview/density.png)

The Density tab presents a donut chart that categorizes every trail attempt by movement complexity — Straight (0–2 direction changes), Moderate (3–5), or Complex (6+) — with the total trail count shown at the centre. A large Complex slice means the player is actively dodging ghosts mid-trail and taking winding paths, while a dominant Straight slice suggests confident, direct play or a preference for safe, predictable routes along the grid edges.

---

## Page 5 — Survival Time

### Component 1: Survival Time Histogram

![Survival Time](descript/graphview/survival.png)

The Survival tab shows a histogram of the time elapsed between consecutive events (trail closures and deaths), with bar colors interpolated from red at low counts to blue at high counts, and dashed mean and dotted median reference lines. Outliers above the 99th percentile are excluded to keep the chart readable. A left-skewed distribution with many short intervals suggests fast, frequent small captures or frequent deaths, while a wider spread with a long right tail means the player occasionally takes very long, ambitious trails alongside quick routine ones.

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