# PyXon

## Project Description

- **Game Genre:** Arcade, Territory Capture

PyXon is a 2D territory-capture arcade game built with Python and Pygame, inspired by the classic *Xonix / Qix* genre. You control a ship moving across a grid, drawing trails through empty space to claim territory. Close a loop by reconnecting to a wall and the enclosed area gets captured. Capture **80% of the grid** to clear the sector and advance.

Nine ghost types stand in your way — each with its own behavior. Some bounce unpredictably, some follow wall edges, some freeze or curse you on contact, and some lurk inside territory you already captured. If a ghost touches your active trail, it starts an infection crawling toward you. Six power-up items drop onto the grid to help even the odds. The game runs across 20 sectors with escalating ghost combinations.

A built-in statistics system logs every trail attempt and death to a CSV file, viewable as five interactive charts from the main menu.

---

## Installation

Clone this project:
```sh
git clone https://github.com/pakhind-blip/pacxon.git
cd pacxon
```

Create and activate a Python virtual environment:

**Windows:**
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Mac:**
```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Running the Game

After activating the Python environment:

**Windows:**
```bat
python main.py
```

**Mac:**
```sh
python3 main.py
```

---

## Gameplay

### Main Menu
![Main Menu](descript/gameplay/1.png)

### Index / Navigation Screen
![Index Screen](descript/gameplay/2.png)

### Level Index
![Level Index](descript/gameplay/3.png)

### How to Play
![How to Play](descript/gameplay/4.png)

### Sector Start
![Sector Start](descript/gameplay/5.png)

### In-Game (Territory Capture)
![In-Game Gameplay](descript/gameplay/6.png)

### Active Gameplay (Balls in Motion)
![Active Gameplay](descript/gameplay/7.png)

### Game Over Screen
![Game Over](descript/gameplay/8.png)

---

## Tutorial / Usage

### Controls

| Key | Action |
|-----|--------|
| `Arrow Keys` / `WASD` | Move the player |
| `Space` / `Enter` | Confirm / launch sector |
| `ESC` | Pause → quit to menu |
| `F11` / `Alt + Enter` | Toggle fullscreen |

### How to Play

1. Launch the game and select **Play** from the main menu
2. Move onto empty space to start drawing a trail
3. Reconnect to any wall to capture the enclosed area
4. Avoid ghosts — contact loses a life, and ghosts that cross your trail start an infection
5. Collect power-up items for temporary advantages
6. Capture **80%** of the grid to clear the sector and advance to the next one

### Tips

- You cannot reverse direction while trailing — plan your path before stepping off the wall
- The infection crawls along your trail toward you — get back to a wall fast to close it before it arrives
- Snow freezes all ghosts, Sword lets you kill them on contact — use them when surrounded
- The Gatekeeper blocks the border while you have an active trail — watch for it before stepping out

---

## Game Features

- **9 ghost types** with distinct AI behaviors
- **6 power-up items** — Lightning, Snow, Sword, Slime, Heart, Star
- **20 hand-crafted sectors** with escalating ghost combinations
- **Trail infection mechanic** — ghosts corrupt the active trail toward the player
- **Freeze and curse status effects**
- **Sector briefing screen** — shows the ghost lineup before each sector starts
- **Ghost and item index** — in-game encyclopedia accessible from the main menu
- **Statistics system** — CSV logging with 5 interactive chart tabs
- **Sound system** — background music, SFX, and mute toggle

---

## Data Visualization

From the main menu, select **Graph** to open the statistics window. It reads `stats.csv` and displays five tabbed charts.

### Overall Summary Dashboard
![Overall Summary](descript/graphview/overall.png)

### Capture Efficiency (Bar Chart)
![Capture Efficiency](descript/graphview/capture.png)

### Territory Density (Donut Chart)
![Territory Density](descript/graphview/density.png)

### Risk Duration (Line Chart)
![Risk Duration](descript/graphview/risk.png)

### Survival Time (Histogram)
![Survival Time](descript/graphview/survival.png)

| Tab | Content |
|-----|---------|
| 1 Summary | Session overview — trails, deaths, levels, averages |
| 2 Capture | Capture efficiency per trail with trend line |
| 3 Risk | Time spent outside safe territory per level |
| 4 Density | Input complexity donut chart |
| 5 Survival | Time-between-events histogram |

---

## Known Bugs

None known at this time.

---

## Unfinished Works

All planned features have been implemented.

---

## External Sources

- **Sound effects and music** — Generated using Gemini AI
- **Item icons** (lightning, snow, sword, slime, heart, star) — Generated using Gemini AI