import pygame
import sys
import math
import random
import os
from core.grid_manager import GridManager
from components.player import Player
from components.ghosts import (GhostBouncer, GhostClimberCW, GhostClimberCCW,
                                GhostInsider, GhostDasher, GhostFreezer,
                                GhostReverser, GhostWatcher, GhostGatekeeper, GhostDecoy)
from core.menu import Menu
from core.sound_manager import SoundManager
from core.item_manager import ItemManager
from core.stats_logger import StatsLogger

MENU, PLAY, GAME_OVER, COMPLETE, READY = 0, 1, 2, 3, 4

# Inverted-key mapping for the Reverser curse — built once at module level
_CURSE_SWAP = {
    pygame.K_LEFT: pygame.K_RIGHT, pygame.K_RIGHT: pygame.K_LEFT,
    pygame.K_UP:   pygame.K_DOWN,  pygame.K_DOWN:  pygame.K_UP,
    pygame.K_a:    pygame.K_d,     pygame.K_d:     pygame.K_a,
    pygame.K_w:    pygame.K_s,     pygame.K_s:     pygame.K_w,
}

class _InvertedKeys:
    __slots__ = ("_k",)
    def __init__(self, k): self._k = k
    def __getitem__(self, key): return self._k[_CURSE_SWAP.get(key, key)]

_ITEM_FLASH_COLORS = {
    'lightning': (255, 230,   0),
    'snow':      (160, 220, 255),
    'sword':     (210, 160, 255),
    'slime':     ( 80, 220,  80),
    'heart':     (255,  80, 120),
    'star':      (255, 255, 200),
}

class GameEngine:
    SECTOR_DEFS = [
        ("GHOST ALLEY",        [GhostBouncer]),
        ("BORDERLINE",         [GhostBouncer, GhostClimberCW]),
        ("CROSSFIRE",          [GhostBouncer, GhostBouncer, GhostClimberCCW]),
        ("INCOMING",           [GhostBouncer, GhostClimberCW, GhostDasher]),
        ("DOUBLE ORBIT",       [GhostClimberCW, GhostClimberCCW, GhostBouncer, GhostBouncer]),
        ("BREACH",             [GhostBouncer, GhostBouncer, GhostDasher, GhostInsider]),
        ("FEEDBACK LOOP",      [GhostBouncer, GhostClimberCW, GhostDasher, GhostReverser]),
        ("SHADOW PROTOCOL",    [GhostBouncer, GhostBouncer, GhostClimberCCW, GhostDecoy]),
        ("COLD FRONT",         [GhostBouncer, GhostDasher, GhostFreezer, GhostInsider]),
        ("LOCKDOWN",           [GhostBouncer, GhostClimberCW, GhostDasher, GhostFreezer, GhostGatekeeper]),
        ("ALL EYES ON YOU",    [GhostBouncer, GhostBouncer, GhostWatcher, GhostReverser, GhostDecoy]),
        ("BLITZ",              [GhostDasher, GhostDasher, GhostClimberCW, GhostInsider, GhostBouncer]),
        ("DISORIENTED",        [GhostClimberCW, GhostClimberCCW, GhostReverser, GhostDecoy, GhostBouncer]),
        ("PARALYSIS",          [GhostFreezer, GhostWatcher, GhostDasher, GhostBouncer, GhostBouncer]),
        ("PERIMETER BREACH",   [GhostGatekeeper, GhostGatekeeper, GhostBouncer, GhostBouncer, GhostDasher]),
        ("PANDEMONIUM",        [GhostBouncer, GhostClimberCW, GhostDasher, GhostReverser, GhostFreezer, GhostInsider]),
        ("SURVEILLANCE",       [GhostWatcher, GhostWatcher, GhostDasher, GhostDecoy, GhostDecoy, GhostBouncer]),
        ("INFILTRATION",       [GhostInsider, GhostInsider, GhostDecoy, GhostGatekeeper, GhostClimberCW, GhostClimberCCW]),
        ("SYSTEM CRITICAL",    [GhostReverser, GhostFreezer, GhostWatcher, GhostGatekeeper, GhostDasher, GhostBouncer, GhostDecoy]),
        ("TOTAL ANNIHILATION", [GhostBouncer, GhostClimberCW, GhostClimberCCW, GhostDasher, GhostReverser,
                                 GhostFreezer, GhostInsider, GhostWatcher, GhostGatekeeper, GhostDecoy]),
    ]

    def __init__(self):
        self.game_state = MENU
        self.score = 0
        self.player = self.grid_manager = None
        self.ghosts: list = []
        self.screen = self.clock = None
        self.screen_width = self.screen_height = 800
        self.screen_height = 600
        self.block_size  = 20
        self.HUD_HEIGHT  = 50
        self.menu_system = None
        self.level = 1
        self._tick = 0
        self._score_pops: list = []
        self._infection = None
        self.sfx = None
        self.item_manager = None
        self._confirm_quit = False
        self._screen_flash: list = []
        self._complete_sfx_played = False
        self._gameover_sfx_played = False
        self._insider_count = self._insiders_spawned = 0
        self._decoy_count   = self._decoys_spawned   = 0
        self.stats: StatsLogger | None = None
        # Cached font objects — populated on first use
        self._fonts: dict = {}

    # ── font cache ────────────────────────────────────────────────────────
    def _font(self, size: int) -> pygame.font.Font:
        if size not in self._fonts:
            self._fonts[size] = pygame.font.Font(None, size)
        return self._fonts[size]

    def get_sector_name(self) -> str:
        return self.SECTOR_DEFS[min(self.level - 1, len(self.SECTOR_DEFS) - 1)][0]

    # ── ghost generation ──────────────────────────────────────────────────
    def _generate_ghosts(self) -> list:
        gw = self.screen_width  // self.block_size
        gh = (self.screen_height - self.HUD_HEIGHT) // self.block_size
        idx        = min(self.level - 1, len(self.SECTOR_DEFS) - 1)
        ghost_list = self.SECTOR_DEFS[idx][1]

        self._insider_count = self._insiders_spawned = 0
        self._decoy_count   = self._decoys_spawned   = 0

        captured_candidates = [
            (x, y)
            for y in range(2, gh - 2)
            for x in range(2, gw - 2)
            if self.grid_manager and self.grid_manager.grid[y][x] == 1
        ]
        border_cells = (
            [(x, 0)      for x in range(gw)] +
            [(x, gh - 1) for x in range(gw)] +
            [(0, y)      for y in range(1, gh - 1)] +
            [(gw - 1, y) for y in range(1, gh - 1)]
        )

        ghosts = []
        for ghost_cls in ghost_list:
            if ghost_cls in (GhostInsider, GhostDecoy):
                if captured_candidates:
                    gx, gy = random.choice(captured_candidates)
                    ghosts.append(ghost_cls(gx, gy, self.block_size))
                else:
                    if ghost_cls is GhostDecoy:   self._decoy_count   += 1
                    else:                          self._insider_count += 1
            elif ghost_cls is GhostGatekeeper:
                gx, gy = random.choice(border_cells)
                ghosts.append(GhostGatekeeper(gx, gy, self.block_size, gw, gh))
            else:
                gx = random.randint(5, gw - 2)
                gy = random.randint(5, gh - 2)
                ghosts.append(ghost_cls(gx, gy, self.block_size))
        return ghosts

    # ── resize / fullscreen ───────────────────────────────────────────────
    def _apply_resize(self, w: int, h: int) -> None:
        self.window_width = w; self.window_height = h
        self.menu_system.screen_width  = w
        self.menu_system.screen_height = h
        self.menu_system.on_resize(w, h)

    def _toggle_fullscreen(self) -> None:
        self._is_fullscreen = not self._is_fullscreen
        if self._is_fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self._windowed_size, pygame.RESIZABLE)
        w, h = self.screen.get_size()
        self.menu_system.screen = self.screen
        self._apply_resize(w, h)

    # ── main loop ─────────────────────────────────────────────────────────
    def run(self, screen, clock, screen_width: int, screen_height: int) -> None:
        self.screen, self.clock = screen, clock
        self.screen_width  = screen_width
        self.screen_height = screen_height
        self.window_width  = screen_width
        self.window_height = screen_height
        self._game_surface   = pygame.Surface((screen_width, screen_height))
        self._is_fullscreen  = False
        self._windowed_size  = (screen_width, screen_height)
        self.menu_system     = Menu(screen, screen_width, screen_height)

        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sfx   = SoundManager(sounds_dir=os.path.join(root, "sound"), volume=0.7)
        self.stats = StatsLogger(filepath=os.path.join(root, "stats.csv"))
        self.sfx.play_menu_theme()

        running = True
        while running:
            self._tick += 1
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.VIDEORESIZE and not self._is_fullscreen:
                    self._windowed_size = (event.w, event.h)
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    self.menu_system.screen = self.screen
                    self._apply_resize(event.w, event.h)

                elif event.type == pygame.KEYDOWN:
                    alt = pygame.key.get_mods() & pygame.KMOD_ALT
                    if event.key == pygame.K_F11 or (alt and event.key == pygame.K_RETURN):
                        self._toggle_fullscreen()
                        continue

                    if self._confirm_quit:
                        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            self._confirm_quit = False
                            self.game_state = MENU
                            self.sfx.play_ui_click(); self.sfx.play_menu_theme()
                        elif event.key == pygame.K_ESCAPE:
                            self._confirm_quit = False
                            self.sfx.play_ui_click()
                        continue

                    if event.key == pygame.K_ESCAPE and self.game_state != MENU:
                        if self.game_state in (PLAY, READY):
                            self._confirm_quit = True
                            self.sfx.play_ui_click()
                        else:
                            self.game_state = MENU
                            self.sfx.play_ui_click(); self.sfx.play_menu_theme()
                        continue
                    self._handle_input(event)

            self.menu_system.screen = self.screen

            if self.game_state == MENU:
                self.menu_system.screen_width  = self.window_width
                self.menu_system.screen_height = self.window_height
                self.menu_system.draw()
            else:
                _win = self.screen
                self.screen = self._game_surface

                if   self.game_state == READY:     self._ready_mode()
                elif self.game_state == PLAY:       self._play_mode()
                elif self.game_state == GAME_OVER:  self._game_over_mode()
                elif self.game_state == COMPLETE:   self._game_complete_mode()

                self.screen = _win
                cw, ch = self.screen_width, self.screen_height
                ww, wh = self.window_width, self.window_height
                scale    = min(ww / cw, wh / ch)
                sw, sh   = int(cw * scale), int(ch * scale)
                ox, oy   = (ww - sw) // 2, (wh - sh) // 2
                self.screen.fill((0, 0, 0))
                self.screen.blit(pygame.transform.smoothscale(self._game_surface, (sw, sh)), (ox, oy))

            pygame.display.flip()
            self.clock.tick(60)

    # ── input dispatch ────────────────────────────────────────────────────
    def _handle_input(self, event) -> None:
        gs = self.game_state
        if gs == MENU:
            res = self.menu_system.handle_input(event)
            if event.type == pygame.KEYDOWN:
                self.sfx.play_ui_click()
            if   res == "start": self._start_game()
            elif res == "quit":  pygame.quit(); sys.exit()
            elif res == "graph":
                import subprocess
                csv_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stats.csv"
                )
                viewer = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), "graph_viewer.py"
                )
                subprocess.Popen(
                    [sys.executable, viewer, csv_path],
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
                )
        elif gs == READY and event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
            self.sfx.play_ui_click(); self.sfx.play_game_theme()
            self.update_game_state(PLAY)
        elif gs == PLAY and event.key == pygame.K_r:
            self._reset_game()
        elif gs == PLAY and event.key == pygame.K_m:
            self.sfx.toggle()
        elif gs == GAME_OVER and event.key == pygame.K_SPACE:
            self.sfx.play_ui_click(); self._start_game()
        elif gs == COMPLETE and event.key == pygame.K_SPACE:
            self.sfx.play_ui_click(); self._start_game()

    # ── game lifecycle ────────────────────────────────────────────────────
    def _start_game(self) -> None:
        self.score = self.level = 1
        self.score = 0
        self._complete_sfx_played  = False
        self._gameover_sfx_played  = False
        self._init_game()
        self.update_game_state(READY)

    def _init_game(self) -> None:
        bs = self.block_size
        gw = self.screen_width  // bs
        gh = (self.screen_height - self.HUD_HEIGHT) // bs
        self.player       = Player(width=bs, height=bs, block_size=bs)
        self.player.set_position(0, 0)
        self.grid_manager = GridManager(gw, gh, self.player, self, bs)
        self.player.stats = self.stats
        self.ghosts       = self._generate_ghosts()
        self._score_pops  = []
        self.item_manager = ItemManager(bs)
        self.player.is_iframe    = True
        self.player.iframe_timer = self.player.iframe_duration

    def _reset_game(self) -> None:
        self._infection = None
        self.player.set_position(0, 0)
        self.player.lives = 3
        self.player.is_trailing = self.player.is_iframe = False
        if self.item_manager:
            self.item_manager._restore_player_speed(self.player)
        self.item_manager = ItemManager(self.block_size)
        self.grid_manager.reset()

    # ── screen flash ──────────────────────────────────────────────────────
    def _add_flash(self, color, alpha=55, life=30):
        self._screen_flash.append({'color': color, 'alpha': alpha, 'life': life, 'max_life': life})

    def _draw_screen_flash(self):
        if not self._screen_flash:
            return
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        still   = []
        for f in self._screen_flash:
            frac = f['life'] / f['max_life']
            r, g, b = f['color']
            overlay.fill((r, g, b, int(f['alpha'] * frac)))
            self.screen.blit(overlay, (0, 0))
            f['life'] -= 1
            if f['life'] > 0:
                still.append(f)
        self._screen_flash = still

    # ── HUD ───────────────────────────────────────────────────────────────
    def _draw_hud(self) -> None:
        sw = self.screen_width
        pygame.draw.rect(self.screen, (15, 15, 25), (0, 0, sw, self.HUD_HEIGHT))
        pygame.draw.line(self.screen, (0, 150, 100), (0, self.HUD_HEIGHT - 1), (sw, self.HUD_HEIGHT - 1), 1)

        f24  = self._font(24)
        f18  = self._font(18)
        f22  = self._font(22)

        # Score + level
        self.screen.blit(f24.render(f"SCORE: {self.score}", True, (0, 220, 160)), (10, 8))
        sector = self.get_sector_name()
        self.screen.blit(f18.render(f"LVL {self.level}/{len(self.SECTOR_DEFS)}  {sector}", True, (180, 180, 255)), (10, 30))

        # Capture bar
        bw, bh, bx, by = 160, 10, 200, 10
        pct  = self.grid_manager.captured_area if self.grid_manager else 0
        fill = int((min(pct, 80.0) / 80.0) * bw)
        pygame.draw.rect(self.screen, (40, 40, 60),    (bx, by, bw, bh))
        if fill > 0:
            pygame.draw.rect(self.screen, (0, 200, 130), (bx, by, fill, bh))
        pygame.draw.rect(self.screen, (0, 100, 70),    (bx, by, bw, bh), 1)
        self.screen.blit(f18.render(f"{pct:.1f}% / 80%", True, (160, 220, 200)), (bx, by + 13))

        # Lives
        lx = sw - 10
        for i in range(3):
            col = (220, 60, 80) if i < self.player.lives else (50, 30, 35)
            pygame.draw.circle(self.screen, col, (lx - (3 - i) * 22, 25), 8)

        # Score pops
        still = []
        for pop in self._score_pops:
            pop['life'] -= 1
            pop['y']    -= 0.8
            if pop['life'] > 0:
                label = pop.get('label') or f"+{pop['val']}"
                ts    = f22.render(label, True, pop.get('color', (0, 255, 180)))
                self.screen.blit(ts, (pop['x'], int(pop['y'])))
                still.append(pop)
        self._score_pops = still

        # Status badges
        freeze_timer = getattr(self.player, 'freeze_timer', 0)
        curse_timer  = getattr(self.player, 'curse_timer',  0)
        all_badges   = []
        if freeze_timer > 0: all_badges.append(("FROZEN", (80,  140, 255), freeze_timer, 300))
        if curse_timer  > 0: all_badges.append(("CURSED", (160, 255,   0), curse_timer,  240))
        if self.item_manager:
            im = self.item_manager
            if im.star_active:
                all_badges.append(("STAR", (255, 255, 80), im.star_timer, 480))
            else:
                if im.lightning_active: all_badges.append(("SPEED",  (255, 230,   0), im.lightning_timer, 240))
                if im.snow_active:      all_badges.append(("FREEZE", (160, 220, 255), im.snow_timer,       240))
                if im.sword_active:     all_badges.append(("SWORD",  (210, 160, 255), im.sword_timer,      210))
                if im.banana_active:    all_badges.append(("SLIME",  ( 80, 220,  80), im.banana_timer,     480))

        if all_badges:
            BADGE_W, BADGE_H, gap = 90, 20, 4
            lx_edge  = sw - 10 - 3 * 22 - 8
            total_w  = len(all_badges) * BADGE_W + (len(all_badges) - 1) * gap
            bx0 = lx_edge - total_w - 8
            by0 = (self.HUD_HEIGHT - BADGE_H) // 2
            f15 = self._font(15); f17 = self._font(17)
            for i, (label, col, timer, max_dur) in enumerate(all_badges):
                rx   = bx0 + i * (BADGE_W + gap)
                ry   = by0
                frac = max(0.0, min(1.0, timer / max_dur))
                secs = timer // 60 + 1
                pygame.draw.rect(self.screen, (15, 15, 25), (rx, ry, BADGE_W, BADGE_H))
                pygame.draw.rect(self.screen, col,           (rx, ry, BADGE_W, BADGE_H), 1)
                pygame.draw.circle(self.screen, col, (rx + 9, ry + BADGE_H // 2), 4)
                self.screen.blit(f15.render(label, True, col), (rx + 17, ry + 2))
                bar_x, bar_y, bar_w = rx + 17, ry + BADGE_H - 6, BADGE_W - 42
                pygame.draw.rect(self.screen, (30, 30, 40),
                                 (bar_x, bar_y, bar_w, 3))
                fill_w = max(1, int(bar_w * frac))
                pygame.draw.rect(self.screen, (int((1 - frac) * 255), int(frac * 200 + 55), 40),
                                 (bar_x, bar_y, fill_w, 3))
                ss = f17.render(f"{secs}s", True, col)
                self.screen.blit(ss, (rx + BADGE_W - ss.get_width() - 3,
                                      ry + BADGE_H // 2 - ss.get_height() // 2))

    # ── READY ─────────────────────────────────────────────────────────────
    def _ready_mode(self) -> None:
        if self.sfx and self.sfx._current_theme is not None:
            self.sfx.stop_theme()

        self.screen.fill((10, 10, 20))
        self.grid_manager.draw(self.screen, offset_y=self.HUD_HEIGHT)
        self.player.draw(self.screen, offset_y=self.HUD_HEIGHT)
        for g in self.ghosts:
            g.draw(self.screen, offset_y=self.HUD_HEIGHT)
        self._draw_hud()

        cx, cy = self.screen_width // 2, self.screen_height // 2
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(160); overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        def cb(surf, y): self.screen.blit(surf, (cx - surf.get_width() // 2, y))

        f56, f30, f22 = self._font(56), self._font(30), self._font(22)
        y = cy - 130
        cb(f22.render("MISSION BRIEFING",  True, (0, 180, 130)),   y); y += 28
        cb(f56.render(f"SECTOR {self.level}", True, (0, 255, 200)), y); y += 54
        cb(f30.render(self.get_sector_name(), True, (255, 215, 60)), y); y += 38

        idx2       = min(self.level - 1, len(self.SECTOR_DEFS) - 1)
        ghost_list = self.SECTOR_DEFS[idx2][1]
        counts: dict = {}
        for cls in ghost_list:
            counts[cls.__name__] = counts.get(cls.__name__, 0) + 1

        total_ghosts = len(self.ghosts) + self._insider_count + self._decoy_count
        cb(f22.render(f"{total_ghosts} HOSTILES DETECTED", True, (220, 80, 100)), y); y += 22

        _LABELS = {
            "GhostBouncer": "BOUNCER",    "GhostClimberCW": "CLIMBER",
            "GhostClimberCCW": "CLIMBER", "GhostDasher": "DASHER",
            "GhostReverser": "REVERSER",  "GhostFreezer": "FREEZER",
            "GhostInsider": "INSIDER",    "GhostWatcher": "WATCHER",
            "GhostGatekeeper": "GATEKEEPER", "GhostDecoy": "DECOY",
        }
        merged: dict = {}
        for cls_name, cnt in counts.items():
            lbl = _LABELS.get(cls_name, cls_name)
            merged[lbl] = merged.get(lbl, 0) + cnt
        for lbl, cnt in merged.items():
            cb(f22.render(f"  x{cnt}  {lbl}", True, (160, 160, 200)), y); y += 18

        y += 10
        cb(f22.render("OBJECTIVE: CAPTURE 80% OF TERRITORY", True, (80, 180, 120)), y); y += 30
        if (self._tick // 22) % 2 == 0:
            cb(f30.render("SPACE / ENTER  —  LAUNCH", True, (0, 255, 180)), y)

        if self._confirm_quit:
            self._draw_confirm_quit()

    # ── PLAY ──────────────────────────────────────────────────────────────
    def _play_mode(self) -> None:
        if self._confirm_quit:
            self.screen.fill((10, 10, 20))
            self.grid_manager.draw(self.screen, offset_y=self.HUD_HEIGHT, infection=self._infection)
            self.player.draw(self.screen, offset_y=self.HUD_HEIGHT)
            for g in self.ghosts: g.draw(self.screen, offset_y=self.HUD_HEIGHT)
            self._draw_hud()
            self._draw_confirm_quit()
            return

        if self._infection:
            self._tick_infection()

        p = self.player
        if getattr(p, 'is_frozen', False):
            p.freeze_timer -= 1
            if p.freeze_timer <= 0:
                p.is_frozen = False

        if getattr(p, 'is_cursed', False):
            p.curse_timer -= 1
            if p.curse_timer <= 0:
                p.is_cursed = False

        if not getattr(p, 'is_frozen', False):
            raw = pygame.key.get_pressed()
            keys = _InvertedKeys(raw) if getattr(p, 'is_cursed', False) else raw
            item_pos = None
            if self.item_manager and self.item_manager._item is not None:
                itm = self.item_manager._item
                item_pos = (itm.grid_x, itm.grid_y)
            p.move_with_collision(keys, self.grid_manager, item_pos=item_pos)

        p.clamp_to_bounds(self.screen_width, self.screen_height - self.HUD_HEIGHT)
        self.screen.fill((10, 10, 20))
        self.grid_manager.update_grid()
        self.grid_manager.draw(self.screen, offset_y=self.HUD_HEIGHT, infection=self._infection)
        p.draw(self.screen, offset_y=self.HUD_HEIGHT)
        for g in self.ghosts:
            g.update(self.grid_manager)
            g.draw(self.screen, offset_y=self.HUD_HEIGHT)
        self.handle_collisions()
        self._try_spawn_insider()

        if self.item_manager:
            if self.item_manager.banana_active:
                self.item_manager.tick_slime(self.ghosts)
            self.item_manager.update(p, self.ghosts, self.grid_manager, self.level, sfx=self.sfx)
            collected = self.item_manager.last_collected
            if collected:
                self.item_manager.last_collected = None
                flash_col = _ITEM_FLASH_COLORS.get(collected)
                if flash_col:
                    self._add_flash(flash_col, alpha=65, life=45)
                if collected == 'heart':
                    px, py = p.get_position()
                    self._score_pops.append({
                        'x': int(px), 'y': int(py) + self.HUD_HEIGHT,
                        'val': None, 'label': '+1', 'color': (255, 80, 120),
                        'life': 70, 'max_life': 70,
                    })
            if self.item_manager.sword_active:
                self.ghosts = self._sword_kill_check()
            self.item_manager.draw(self.screen, offset_y=self.HUD_HEIGHT)

        self._draw_hud()
        if self.item_manager:
            self.item_manager.draw_hud_effect(self.screen, self.screen_width, self.HUD_HEIGHT)

        # Screen tint overlays
        tint = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        freeze_timer = getattr(p, 'freeze_timer', 0)
        curse_timer  = getattr(p, 'curse_timer',  0)
        im = self.item_manager
        if im and im.star_active:
            t = self._tick
            sr = int(127 + 127 * math.sin(t * 0.07))
            sg = int(127 + 127 * math.sin(t * 0.07 + 2.1))
            sb = int(127 + 127 * math.sin(t * 0.07 + 4.2))
            tint.fill((sr, sg, sb, 35)); self.screen.blit(tint, (0, 0))
        else:
            if im and im.lightning_active: tint.fill((255, 230,   0, 28)); self.screen.blit(tint, (0, 0))
            if im and im.snow_active:      tint.fill((160, 220, 255, 32)); self.screen.blit(tint, (0, 0))
            if im and im.sword_active:     tint.fill((210, 160, 255, 28)); self.screen.blit(tint, (0, 0))
            if im and im.banana_active:    tint.fill(( 80, 220,  80, 28)); self.screen.blit(tint, (0, 0))
        if freeze_timer > 0: tint.fill(( 30, 100, 220, 40)); self.screen.blit(tint, (0, 0))
        if curse_timer  > 0: tint.fill((160, 255,   0, 35)); self.screen.blit(tint, (0, 0))
        self._draw_screen_flash()

        if self.grid_manager.calculate_coverage() >= 80.0:
            self.change_level()
        if p.lives <= 0:
            self.update_game_state(GAME_OVER)

    # ── GAME OVER ─────────────────────────────────────────────────────────
    def _game_over_mode(self) -> None:
        if not self._gameover_sfx_played:
            self._gameover_sfx_played = True
            self._add_flash((220, 40, 55), alpha=90, life=60)

        self.screen.fill((20, 5, 8))
        cx, cy = self.screen_width // 2, self.screen_height // 2
        def cb(surf, y): self.screen.blit(surf, (cx - surf.get_width() // 2, y))

        f64 = self._font(64); f32 = self._font(32); f22 = self._font(22)
        y = cy - 120
        cb(f22.render("MISSION FAILED",       True, (180,  50,  60)), y); y += 30
        pygame.draw.line(self.screen, (80, 20, 25),  (cx - 200, y), (cx + 200, y), 1); y += 14
        cb(f64.render("GAME OVER",             True, (220,  40,  55)), y); y += 58
        pygame.draw.line(self.screen, (60, 15, 20),  (cx - 180, y), (cx + 180, y), 1); y += 18
        cb(f32.render(f"SCORE:  {self.score}", True, (200, 140, 145)), y); y += 34
        cb(f32.render(f"SECTOR: {self.level}", True, (200, 140, 145)), y); y += 40
        pygame.draw.line(self.screen, (60, 15, 20),  (cx - 180, y), (cx + 180, y), 1); y += 16
        if (self._tick // 28) % 2 == 0:
            cb(f32.render("SPACE — TRY AGAIN",     True, (220, 60, 75)), y)
        y += 34
        cb(f22.render("ESC — RETURN TO MENU",       True, (100, 40, 50)), y)
        self._draw_screen_flash()

    # ── COMPLETE ──────────────────────────────────────────────────────────
    def _game_complete_mode(self) -> None:
        if not self._complete_sfx_played:
            self._complete_sfx_played = True
            self.sfx.play_level_complete()
            self._add_flash((100, 255, 120), alpha=90, life=60)

        self.screen.fill((4, 16, 10))
        cx, cy = self.screen_width // 2, self.screen_height // 2
        def cb(surf, y): self.screen.blit(surf, (cx - surf.get_width() // 2, y))

        f64 = self._font(64); f32 = self._font(32); f22 = self._font(22)
        y = cy - 120
        cb(f22.render("ALL SECTORS SECURED",          True, (0,  180, 100)),  y); y += 30
        pygame.draw.line(self.screen, (0, 80, 50),    (cx - 200, y), (cx + 200, y), 1); y += 14
        cb(f64.render("YOU WIN!",                     True, (100, 255, 120)), y); y += 58
        pygame.draw.line(self.screen, (0, 70, 40),    (cx - 180, y), (cx + 180, y), 1); y += 18
        cb(f32.render(f"FINAL SCORE:  {self.score}",  True, (140, 210, 145)), y); y += 34
        cb(f32.render(f"SECTORS: {len(self.SECTOR_DEFS)}", True, (140, 210, 145)), y); y += 40
        pygame.draw.line(self.screen, (0, 70, 40),    (cx - 180, y), (cx + 180, y), 1); y += 16
        if (self._tick // 28) % 2 == 0:
            cb(f32.render("SPACE — PLAY AGAIN",        True, ( 80, 220, 100)), y)
        y += 34
        cb(f22.render("ESC — RETURN TO MENU",          True, ( 40, 100,  60)), y)
        self._draw_screen_flash()

    # ── CONFIRM QUIT ──────────────────────────────────────────────────────
    def _draw_confirm_quit(self) -> None:
        cx, cy = self.screen_width // 2, self.screen_height // 2
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(140); overlay.fill((0, 0, 10))
        self.screen.blit(overlay, (0, 0))

        pw, ph = 360, 180
        px, py = cx - pw // 2, cy - ph // 2
        pygame.draw.rect(self.screen, (10, 18, 30),   (px, py, pw, ph))
        pygame.draw.rect(self.screen, (0, 150, 110),  (px, py, pw, ph), 2)

        def cb(surf, y): self.screen.blit(surf, (cx - surf.get_width() // 2, y))
        cb(self._font(38).render("ABANDON MISSION?",              True, (220, 230, 255)), py + 22)
        cb(self._font(22).render("All unsaved progress will be lost.", True, (100, 120, 115)), py + 62)
        pygame.draw.line(self.screen, (0, 80, 60), (px + 20, py + 90), (px + pw - 20, py + 90), 1)
        cb(self._font(24).render("ENTER — LEAVE    ESC — STAY",   True, (0, 200, 150)), py + 104)

    # ── collision handling ────────────────────────────────────────────────
    def handle_collisions(self) -> None:
        p = self.player
        if p.is_iframe or getattr(p, 'sword_immune', False):
            return

        can_infect = (self._infection is None)
        px, py     = p.get_position()
        margin     = self.block_size * 0.35
        inner_size = self.block_size - margin * 2
        pgx, pgy   = p.get_grid_position()
        pcx = px + self.block_size / 2
        pcy = py + self.block_size / 2

        def _overlaps(g):
            return (abs(g.x + self.block_size / 2 - pcx) < inner_size and
                    abs(g.y + self.block_size / 2 - pcy) < inner_size)

        def _on_trail(g):
            gx = int((g.x + self.block_size / 2) // self.block_size)
            gy = int((g.y + self.block_size / 2) // self.block_size)
            return (gx, gy) in set(self.grid_manager.trail), gx, gy

        # Insider + gatekeeper pass
        for g in self.ghosts:
            is_insider    = getattr(g, 'is_insider',    False)
            is_gatekeeper = getattr(g, 'is_gatekeeper', False)
            if not (is_insider or is_gatekeeper):
                continue
            if getattr(g, 'is_decoy', False):
                continue
            if _overlaps(g):
                self._player_hit(); return
            if is_gatekeeper and g.is_border_blocked(pgx, pgy):
                self._player_hit(); return

        # General ghost pass
        cursed = getattr(p, 'is_cursed', False)
        trail_set = set(self.grid_manager.trail)

        for g in self.ghosts:
            if getattr(g, 'is_insider', False) or getattr(g, 'is_gatekeeper', False):
                continue
            if getattr(g, 'is_decoy', False):
                dgx = int(g.x // self.block_size)
                dgy = int(g.y // self.block_size)
                if self.grid_manager.get_cell(dgx, dgy) == 1:
                    continue

            ov = _overlaps(g)
            trail_hit, gx, gy = _on_trail(g)
            on_trail = trail_hit and not ov

            if getattr(g, 'is_freezer', False):
                cooldown = getattr(g, '_freeze_cooldown', 0)
                if cooldown > 0:
                    g._freeze_cooldown = cooldown - 1
                    continue
                # Use a generous hitbox for the freezer (full block size)
                freeze_hit = (abs(g.x + self.block_size / 2 - pcx) < self.block_size and
                              abs(g.y + self.block_size / 2 - pcy) < self.block_size)
                if freeze_hit:
                    if not getattr(p, 'is_frozen', False):
                        # Only freeze when player is outside safe territory
                        cell = self.grid_manager.get_cell(pgx, pgy)
                        if cell != 1:
                            p.is_frozen = True; p.freeze_timer = 300
                            g._freeze_cooldown = 360
                            self._add_flash((30, 100, 220), alpha=65, life=45)
                    else:
                        self._player_hit(); return
                    continue
                if on_trail and can_infect:
                    self._start_infection(gx, gy); return
                continue

            if getattr(g, 'is_reverser', False):
                cooldown = getattr(g, '_curse_cooldown', 0)
                if cooldown > 0:
                    g._curse_cooldown = cooldown - 1
                    continue
                if ov or trail_hit:
                    if not cursed:
                        p.is_cursed = True; p.curse_timer = 240
                        g._curse_cooldown = 240
                        self._add_flash((160, 255, 0), alpha=65, life=45)
                    else:
                        self._player_hit(); return
                continue

            if getattr(g, 'is_dasher', False) or getattr(g, 'is_watcher', False):
                if ov:
                    self._player_hit(); return
                if on_trail and can_infect:
                    self._start_infection(gx, gy); return
                continue

            if on_trail and can_infect:
                self._start_infection(gx, gy); return
            if ov:
                self._player_hit(); return

    # ── infection ─────────────────────────────────────────────────────────
    def _start_infection(self, hit_gx, hit_gy):
        trail = self.grid_manager.trail
        if not trail:
            self._player_hit(); return
        hit_idx = next((i for i, (tx, ty) in enumerate(trail) if tx == hit_gx and ty == hit_gy), 0)
        self._infection = {'cells': trail[hit_idx:], 'front': 0, 'timer': 0, 'speed': 2}

    def _tick_infection(self):
        inf = self._infection
        if not inf or not isinstance(inf, dict):   # safety guard
            self._infection = None
            return
        inf['timer'] += 1
        if inf['timer'] < inf['speed']:
            return
        inf['timer'] = 0
        inf['front'] += 1
        if self.sfx: self.sfx.play_infection_tick()
        pgx, pgy = self.player.get_grid_position()
        cells    = inf['cells']
        if inf['front'] >= len(cells):
            self._infection = None; self._player_hit(); return
        fx, fy = cells[inf['front']]
        if (fx, fy) == (pgx, pgy):
            self._infection = None; self._player_hit()

    # ── player hit ────────────────────────────────────────────────────────
    def _player_hit(self):
        self._infection = None
        self._screen_flash = []
        p = self.player
        p.is_frozen = False; p.freeze_timer = 0
        p.is_cursed = False; p.curse_timer  = 0
        p.sword_immune = False
        # Reset per-ghost cooldowns so freezers/reversers don't get permanently locked
        for g in self.ghosts:
            if getattr(g, 'is_freezer', False):
                g._freeze_cooldown = 0
            if getattr(g, 'is_reverser', False):
                g._curse_cooldown = 0
        if self.item_manager:
            im = self.item_manager
            im._restore_player_speed(p)
            im._restore_player_immunity(p)
            im._restore_ghost_speeds(self.ghosts, 'snow')
            im._restore_ghost_speeds(self.ghosts, 'banana')
            im.lightning_timer = im.snow_timer = im.sword_timer = im.banana_timer = im.star_timer = 0
        if self.stats and self.grid_manager:
            self.stats.on_player_death(
                level=self.level, capture_pct=self.grid_manager.captured_area,
                player_pos=p.get_position(), ghosts=self.ghosts, block_size=self.block_size,
            )
        if p.lose_life() > 0:
            if self.sfx: self.sfx.play_death()
            p.set_position(0, 0); p.reset_movement()
            self.grid_manager.trail.clear()
            self.grid_manager.start_position = (-1, -1)
            for row in self.grid_manager.grid:
                for xi in range(len(row)):
                    if row[xi] == 2: row[xi] = 0
        else:
            if self.sfx: self.sfx.play_death(); self.sfx.play_game_over()
            self.update_game_state(GAME_OVER)

    # ── insider/decoy deferred spawn ──────────────────────────────────────
    def _try_spawn_insider(self) -> None:
        if self.grid_manager.captured_area < 15.0:
            return
        gw, gh = self.grid_manager.width, self.grid_manager.height
        candidates = [
            (x, y)
            for y in range(2, gh - 2)
            for x in range(2, gw - 2)
            if self.grid_manager.grid[y][x] == 1
        ]
        if not candidates:
            return
        if self._insiders_spawned < self._insider_count:
            gx, gy = random.choice(candidates)
            self.ghosts.append(GhostInsider(gx, gy, self.block_size))
            self._insiders_spawned += 1
        if self._decoys_spawned < self._decoy_count:
            gx, gy = random.choice(candidates)
            self.ghosts.append(GhostDecoy(gx, gy, self.block_size))
            self._decoys_spawned += 1

    # ── sword kill ────────────────────────────────────────────────────────
    def _sword_kill_check(self) -> list:
        bs   = self.block_size
        px   = self.player.x; py = self.player.y
        ts   = set(self.grid_manager.trail)
        out  = []
        for g in self.ghosts:
            body_hit  = abs(g.x - px) < bs and abs(g.y - py) < bs
            trail_hit = (int(g.x // bs), int(g.y // bs)) in ts
            if body_hit or trail_hit:
                self.score += 50
                self.add_score_pop(int(g.x), int(g.y) + self.HUD_HEIGHT, 50)
            else:
                out.append(g)
        return out

    # ── misc helpers ──────────────────────────────────────────────────────
    def add_score_pop(self, x, y, val):
        self._score_pops.append({'x': x, 'y': y + self.HUD_HEIGHT, 'val': val, 'life': 60})

    def update_game_state(self, ns): self.game_state = ns

    def change_level(self):
        self._infection = None
        self.level += 1
        if self.level > len(self.SECTOR_DEFS):
            self.update_game_state(COMPLETE); return
        if self.sfx: self.sfx.play_level_complete()
        p = self.player
        p.set_position(0, 0); p.lives = 3
        p.is_trailing = p.is_frozen = p.is_cursed = p.sword_immune = False
        p.freeze_timer = p.curse_timer = 0
        p.is_iframe = True; p.iframe_timer = p.iframe_duration
        if self.item_manager:
            self.item_manager._restore_player_speed(p)
        self.item_manager = ItemManager(self.block_size)
        self.grid_manager.reset()
        self.ghosts = self._generate_ghosts()
        self.update_game_state(READY)