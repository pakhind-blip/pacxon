# PyXon

## Project Description

- **Project by:** Pakhin Daonan 6810545859
- **Game Genre:** Arcade, Territory Capture

PyXon is a 2D territory-capture arcade game built with Python and Pygame, inspired by the classic *Xonix / Qix* genre. You control a ship moving across a grid, drawing trails through empty space to claim territory. Close a loop by reconnecting to a wall and the enclosed area gets captured. Capture **80% of the grid** to clear the sector and advance.

Nine ghost types stand in your way — each with its own behavior. Some bounce unpredictably, some follow wall edges, some freeze or curse you on contact, and some lurk inside territory you already captured. If a ghost touches your active trail, it starts an infection crawling toward you. Six power-up items drop onto the grid to help even the odds. The game runs across 20 sectors with escalating ghost combinations.

**Statistics** window that graphs your performance after each session.

---

## Installation

To clone this project:

```sh
git clone https://github.com/pakhind-blip/pacxon.git
```

To create and run a Python environment for this project:

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

> **requirements.txt** contents:
> ```
> pygame==2.6.1
> matplotlib==3.10.8
> ```

Project folder structure:

```
pacxon-main/
├── DESCRIPTION.md
├── LICENSE
├── README.md
├── requirements.txt
├── VISUALIZATION.md
│
├── src/                         (main source folder)
│   ├── main.py
│   ├── stats.csv
│   │
│   ├── core/                    (core engine modules)
│   │   ├── collision.py
│   │   ├── game_engine.py
│   │   ├── game_object.py
│   │   ├── graph_viewer.py
│   │   ├── grid_manager.py
│   │   ├── item_manager.py
│   │   ├── menu.py
│   │   ├── sound_manager.py
│   │   └── stats_logger.py
│   │
│   ├── components/              (player and ghost classes)
│   │   ├── ghosts.py
│   │   └── player.py
│   │
│   ├── items/                   (power-up icons)
│   │   ├── heart.png
│   │   ├── lightning.png
│   │   ├── slime.png
│   │   ├── snow.png
│   │   ├── star.png
│   │   └── sword.png
│   │
│   └── sound/                   (audio files)
│       ├── capture.wav
│       ├── death.wav
│       ├── game_over.wav
│       ├── game_theme.wav
│       ├── infection_tick.wav
│       ├── item_heart.wav
│       ├── item_lightning.wav
│       ├── item_slime.wav
│       ├── item_snow.wav
│       ├── item_spawn.wav
│       ├── item_star.wav
│       ├── item_sword.wav
│       ├── level_complete.wav
│       ├── theme.wav
│       ├── trail.wav
│       └── ui_click.wav
│
└── descript/                    (documentation assets)
    ├── proposal.pdf
    ├── uml.pdf
    ├── gameplay/
    │   ├── 1.png
    │   ├── 2.png
    │   ├── 3.png
    │   ├── 4.png
    │   ├── 5.png
    │   ├── 6.png
    │   ├── 7.png
    │   └── 8.png
    └── graphview/
        ├── capture.png
        ├── density.png
        ├── overall.png
        ├── risk.png
        └── survival.png
```

---

## Running Guide

After activating the Python environment, run the game with:

**Windows:**
```bat
python main.py
```

**Mac:**
```sh
python3 main.py
```

---

## Tutorial / Usage

### Playing the game

1. Run `main.py` — the main menu opens automatically.
2. Use **↑ ↓** to navigate options, **Space / Enter** to select.
3. Select **Play** to start — a sector briefing screen shows before each level.
4. Move the ship across the grid to capture territory:

| Action | How |
|--------|-----|
| **Move** | Arrow Keys or WASD |
| **Start trail** | Move onto empty space |
| **Capture area** | Reconnect trail back to any wall |
| **Confirm / Launch** | Space or Enter |
| **Fullscreen** | F11 or Alt + Enter |
| **Back to menu** | ESC |

5. Press **ESC** during gameplay to return to the main menu.
6. Select **Graph** on the main menu to open the statistics window.

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

## Known Bugs

None known at this time.

---

## Unfinished Works

All planned features have been implemented.

---

## External Sources

Acknowledge to:

1. **Pygame** — game loop, rendering, input, audio playback
   https://www.pygame.org — LGPL 2.1

2. **Matplotlib** — all 5 statistics charts (bar, line, donut, histogram, summary cards)
   https://matplotlib.org — PSF / BSD

3. **Sound effects and music** — Generated using Gemini AI

4. **Item icons** (lightning, snow, sword, slime, heart, star) — Generated using Gemini AI