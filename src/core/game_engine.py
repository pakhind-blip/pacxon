import pygame
import sys
import random
import os
from core.grid_manager import GridManager
from components.player import Player
from components.ghosts import GhostBouncer, GhostClimberCW, GhostClimberCCW, GhostInsider, GhostDasher, GhostFreezer, GhostReverser, GhostWatcher, GhostGatekeeper, GhostDecoy
from core.menu import Menu
from core.sound_manager import SoundManager
from core.item_manager import ItemManager
from core.stats_logger import StatsLogger

MENU, PLAY, GAME_OVER, COMPLETE, READY = 0, 1, 2, 3, 4

class GameEngine:
    def __init__(self):
        self.game_state = MENU
        self.score = 0
        self.player, self.grid_manager = None, None
        self.ghosts = []
        self.screen, self.clock = None, None
        self.screen_width, self.screen_height = 800, 600
        self.block_size = 20
        self.HUD_HEIGHT = 50
        self.menu_system = None
        self.level = 1
        self._tick = 0
        self._score_pops = []
        self._infection = None
        self.sfx = None
        self.item_manager = None
        self._confirm_quit = False
        self._screen_flash = []
        self._complete_sfx_played = False   # list of {color, alpha, life, max_life}
        self._insider_count = 0
        self._insiders_spawned = 0
        self._decoy_count = 0
        self._decoys_spawned = 0
        self.stats: StatsLogger | None = None

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
        ("TOTAL ANNIHILATION", [GhostBouncer, GhostClimberCW, GhostClimberCCW, GhostDasher, GhostReverser, GhostFreezer, GhostInsider, GhostWatcher, GhostGatekeeper, GhostDecoy]),
    ]

    def get_sector_name(self) -> str:
        idx = min(self.level - 1, len(self.SECTOR_DEFS) - 1)
        return self.SECTOR_DEFS[idx][0]

    def _generate_ghosts(self) -> list:
        ghosts = []
        grid_width  = self.screen_width  // self.block_size
        grid_height = (self.screen_height - self.HUD_HEIGHT) // self.block_size

        idx        = min(self.level - 1, len(self.SECTOR_DEFS) - 1)
        ghost_list = self.SECTOR_DEFS[idx][1]

        self._insider_count    = 0
        self._insiders_spawned = 0
        self._decoy_count      = 0
        self._decoys_spawned   = 0

        captured_candidates = [
            (x, y)
            for y in range(2, grid_height - 2)
            for x in range(2, grid_width  - 2)
            if self.grid_manager and self.grid_manager.grid[y][x] == 1
        ]

        border_cells = (
            [(x, 0) for x in range(grid_width)] +
            [(x, grid_height - 1) for x in range(grid_width)] +
            [(0, y) for y in range(1, grid_height - 1)] +
            [(grid_width - 1, y) for y in range(1, grid_height - 1)]
        )

        for ghost_cls in ghost_list:
            if ghost_cls in (GhostInsider, GhostDecoy):
                if captured_candidates:
                    gx, gy = random.choice(captured_candidates)
                    ghosts.append(ghost_cls(gx, gy, self.block_size))
                else:
                    if ghost_cls is GhostDecoy:
                        self._decoy_count += 1
                    else:
                        self._insider_count += 1
            elif ghost_cls is GhostGatekeeper:
                gx, gy = random.choice(border_cells)
                ghosts.append(GhostGatekeeper(gx, gy, self.block_size, grid_width, grid_height))
            else:
                gx = random.randint(5, grid_width  - 2)
                gy = random.randint(5, grid_height - 2)
                ghosts.append(ghost_cls(gx, gy, self.block_size))

        return ghosts

    def _apply_resize(self, new_width: int, new_height: int) -> None:
        self.window_width  = new_width
        self.window_height = new_height
        self.menu_system.screen_width  = new_width
        self.menu_system.screen_height = new_height
        self.menu_system.on_resize(new_width, new_height)

    def _toggle_fullscreen(self) -> None:
        self._is_fullscreen = not self._is_fullscreen
        if self._is_fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(self._windowed_size, pygame.RESIZABLE)
        w, h = self.screen.get_size()
        self.menu_system.screen = self.screen
        self._apply_resize(w, h)

    def run(self, screen, clock, screen_width: int, screen_height: int) -> None:
        self.screen, self.clock = screen, clock
        self.screen_width, self.screen_height = screen_width, screen_height
        self.window_width, self.window_height = screen_width, screen_height
        self._game_surface = pygame.Surface((screen_width, screen_height))
        self._is_fullscreen = False
        self._windowed_size  = (screen_width, screen_height)
        self.menu_system = Menu(screen, screen_width, screen_height)
        sounds_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sound")
        self.sfx = SoundManager(sounds_dir=sounds_path, volume=0.7)
        self.sfx.play_menu_theme()
        self.stats = StatsLogger(filepath=os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stats.csv"
        ))
        running = True
        while running:
            self._tick += 1
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.VIDEORESIZE:
                    if not self._is_fullscreen:
                        self._windowed_size = (event.w, event.h)
                        self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                        self.menu_system.screen = self.screen
                        self._apply_resize(event.w, event.h)

                elif event.type == pygame.KEYDOWN:
                    alt_held = pygame.key.get_mods() & pygame.KMOD_ALT
                    if event.key == pygame.K_F11 or (alt_held and event.key == pygame.K_RETURN):
                        self._toggle_fullscreen()
                        continue

                    if self._confirm_quit:
                        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                            self._confirm_quit = False
                            self.game_state = MENU
                            if self.sfx: self.sfx.play_ui_click()
                            if self.sfx: self.sfx.play_menu_theme()
                        elif event.key == pygame.K_ESCAPE:
                            self._confirm_quit = False
                            if self.sfx: self.sfx.play_ui_click()
                        continue

                    if event.key == pygame.K_ESCAPE and self.game_state != MENU:
                        if self.game_state in (PLAY, READY):
                            self._confirm_quit = True
                            if self.sfx: self.sfx.play_ui_click()
                        else:
                            self.game_state = MENU
                            if self.sfx: self.sfx.play_ui_click()
                            if self.sfx: self.sfx.play_menu_theme()
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

                if self.game_state == READY:       self._ready_mode()
                elif self.game_state == PLAY:      self._play_mode()
                elif self.game_state == GAME_OVER: self._game_over_mode()
                elif self.game_state == COMPLETE:  self._game_complete_mode()

                self.screen = _win

                canvas_w, canvas_h = self.screen_width, self.screen_height
                win_w, win_h = self.window_width, self.window_height
                scale = min(win_w / canvas_w, win_h / canvas_h)
                scaled_w = int(canvas_w * scale)
                scaled_h = int(canvas_h * scale)
                ox = (win_w - scaled_w) // 2
                oy = (win_h - scaled_h) // 2
                scaled_surface = pygame.transform.smoothscale(self._game_surface, (scaled_w, scaled_h))
                self.screen.fill((0, 0, 0))
                self.screen.blit(scaled_surface, (ox, oy))

            pygame.display.flip()
            self.clock.tick(60)

    def _handle_input(self, event) -> None:
        if self.game_state == MENU:
            res = self.menu_system.handle_input(event)
            if event.type == pygame.KEYDOWN:
                if self.sfx: self.sfx.play_ui_click()
            if res == "start": self._start_game()
            elif res == "quit": pygame.quit(); sys.exit()
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
        elif self.game_state == READY and event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.sfx: self.sfx.play_ui_click()
            if self.sfx: self.sfx.play_game_theme()
            self.update_game_state(PLAY)
        elif self.game_state == PLAY and event.key == pygame.K_r:
            self._reset_game()
        elif self.game_state == PLAY and event.key == pygame.K_m:
            self.sfx.toggle()
        elif self.game_state == GAME_OVER and event.key == pygame.K_SPACE:
            if self.sfx: self.sfx.play_ui_click()
            self._start_game()
        elif self.game_state == COMPLETE and event.key == pygame.K_SPACE:
            if self.sfx: self.sfx.play_ui_click()
            self._start_game()

    def _start_game(self) -> None:
        self.score, self.level = 0, 1
        self._complete_sfx_played = False
        self._gameover_sfx_played = False
        self._init_game()
        self.update_game_state(READY)

    def _init_game(self) -> None:
        gw = self.screen_width  // self.block_size
        gh = (self.screen_height - self.HUD_HEIGHT) // self.block_size
        self.player = Player(width=self.block_size, height=self.block_size, block_size=self.block_size)
        self.player.set_position(0, 0)
        self.grid_manager = GridManager(gw, gh, self.player, self, self.block_size)
        self.player.stats = self.stats  # give player access to logger
        self.ghosts = self._generate_ghosts()
        self._score_pops = []
        self.item_manager = ItemManager(self.block_size)
        self.player.is_iframe = True
        self.player.iframe_timer = self.player.iframe_duration

    def _reset_game(self) -> None:
        self._infection = None
        self.player.set_position(0, 0)
        self.player.lives, self.player.is_trailing, self.player.is_iframe = 3, False, False
        if self.item_manager:
            self.item_manager._restore_player_speed(self.player)
        self.item_manager = ItemManager(self.block_size)
        self.grid_manager.reset()

    def _add_flash(self, color, alpha=55, life=30):
        """Queue a colored screen overlay flash."""
        self._screen_flash.append({'color': color, 'alpha': alpha, 'life': life, 'max_life': life})

    def _draw_screen_flash(self):
        """Draw and tick all active screen flashes."""
        if not self._screen_flash:
            return
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        still_alive = []
        for f in self._screen_flash:
            frac = f['life'] / f['max_life']
            a = int(f['alpha'] * frac)
            r, g, b = f['color']
            overlay.fill((r, g, b, a))
            self.screen.blit(overlay, (0, 0))
            f['life'] -= 1
            if f['life'] > 0:
                still_alive.append(f)
        self._screen_flash = still_alive

    # ── HUD ──────────────────────────────────────────────────────────────────

    def _draw_hud(self) -> None:
        pygame.draw.rect(self.screen, (15, 15, 25), (0, 0, self.screen_width, self.HUD_HEIGHT))
        pygame.draw.line(self.screen, (0, 150, 100), (0, self.HUD_HEIGHT - 1), (self.screen_width, self.HUD_HEIGHT - 1), 1)

        font = pygame.font.Font(None, 24)
        small = pygame.font.Font(None, 18)

        # Score
        self.screen.blit(font.render(f"SCORE: {self.score}", True, (0, 220, 160)), (10, 8))

        # Level + sector name
        sector = self.get_sector_name()
        self.screen.blit(small.render(f"LVL {self.level}/{len(self.SECTOR_DEFS)}  {sector}", True, (180, 180, 255)), (10, 30))

        # Capture progress bar — placed left, after score/level text
        bw, bh = 160, 10
        bx = 200
        by = 10
        pygame.draw.rect(self.screen, (40, 40, 60), (bx, by, bw, bh))
        pct = self.grid_manager.captured_area if self.grid_manager else 0
        fill = int((min(pct, 80.0) / 80.0) * bw)
        if fill > 0:
            pygame.draw.rect(self.screen, (0, 200, 130), (bx, by, fill, bh))
        pygame.draw.rect(self.screen, (0, 100, 70), (bx, by, bw, bh), 1)
        self.screen.blit(small.render(f"{pct:.1f}% / 80%", True, (160, 220, 200)), (bx, by + 13))

        # Lives
        lives_x = self.screen_width - 10
        for i in range(3):
            col = (220, 60, 80) if i < self.player.lives else (50, 30, 35)
            pygame.draw.circle(self.screen, col, (lives_x - (3 - i) * 22, 25), 8)

        # Score pops
        still_alive = []
        for pop in self._score_pops:
            pop['life'] -= 1
            pop['y'] -= 0.8
            if pop['life'] > 0:
                fs = pygame.font.Font(None, 22)
                label = pop.get('label') or f"+{pop['val']}"
                color = pop.get('color', (0, 255, 180))
                ts = fs.render(label, True, color)
                self.screen.blit(ts, (pop['x'], int(pop['y'])))
                still_alive.append(pop)
        self._score_pops = still_alive

        # All badges (status effects + item effects) — unified row between progress bar and lives
        freeze_timer = getattr(self.player, 'freeze_timer', 0)
        curse_timer  = getattr(self.player, 'curse_timer',  0)

        # Collect all active badges: (label, color, timer, max_duration)
        all_badges = []
        if freeze_timer > 0:
            all_badges.append(("FROZEN", (80, 140, 255), freeze_timer, 300))
        if curse_timer > 0:
            all_badges.append(("CURSED", (160, 255, 0),  curse_timer, 240))
        if self.item_manager:
            im = self.item_manager
            if im.star_active:
                all_badges.append(("STAR",  (255, 255, 80),  im.star_timer,      480))
            else:
                if im.lightning_active: all_badges.append(("SPEED",  (255, 230,   0), im.lightning_timer, 240))
                if im.snow_active:      all_badges.append(("FREEZE", (160, 220, 255), im.snow_timer,       240))
                if im.sword_active:     all_badges.append(("SWORD",  (210, 160, 255), im.sword_timer,      210))
                if im.banana_active:    all_badges.append(("SLIME",  ( 80, 220,  80), im.banana_timer,     480))

        if all_badges:
            BADGE_W, BADGE_H = 90, 20
            gap = 4
            lives_left_edge = self.screen_width - 10 - 3 * 22 - 8
            total_w = len(all_badges) * BADGE_W + (len(all_badges) - 1) * gap
            bx = lives_left_edge - total_w - 8
            by = (self.HUD_HEIGHT - BADGE_H) // 2
            font_lbl = pygame.font.Font(None, 15)
            font_sec = pygame.font.Font(None, 17)
            for i, (label, col, timer, max_dur) in enumerate(all_badges):
                rx   = bx + i * (BADGE_W + gap)
                ry   = by
                frac = max(0.0, min(1.0, timer / max_dur))
                secs = timer // 60 + 1
                pygame.draw.rect(self.screen, (15, 15, 25), (rx, ry, BADGE_W, BADGE_H))
                pygame.draw.rect(self.screen, col,          (rx, ry, BADGE_W, BADGE_H), 1)
                pygame.draw.circle(self.screen, col, (rx + 9, ry + BADGE_H // 2), 4)
                lbl_surf = font_lbl.render(label, True, col)
                self.screen.blit(lbl_surf, (rx + 17, ry + 2))
                bar_x = rx + 17
                bar_y = ry + BADGE_H - 6
                bar_w = BADGE_W - 42
                pygame.draw.rect(self.screen, (30, 30, 40), (bar_x, bar_y, bar_w, 3))
                fill_w = max(1, int(bar_w * frac))
                r_c = int((1 - frac) * 255)
                g_c = int(frac * 200 + 55)
                pygame.draw.rect(self.screen, (r_c, g_c, 40), (bar_x, bar_y, fill_w, 3))
                sec_surf = font_sec.render(f"{secs}s", True, col)
                self.screen.blit(sec_surf, (rx + BADGE_W - sec_surf.get_width() - 3,
                                            ry + BADGE_H // 2 - sec_surf.get_height() // 2))

    # ── READY ────────────────────────────────────────────────────────────────

    def _ready_mode(self) -> None:
        if self.sfx and self.sfx._current_theme is not None:
            self.sfx.stop_theme()

        self.screen.fill((10, 10, 20))
        self.grid_manager.draw(self.screen, offset_y=self.HUD_HEIGHT)
        self.player.draw(self.screen, offset_y=self.HUD_HEIGHT)
        for g in self.ghosts:
            g.draw(self.screen, offset_y=self.HUD_HEIGHT)
        self._draw_hud()

        cx = self.screen_width  // 2
        cy = self.screen_height // 2

        # Dark overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(160)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        font_big  = pygame.font.Font(None, 56)
        font_med  = pygame.font.Font(None, 30)
        font_sm   = pygame.font.Font(None, 22)

        def cx_blit(surf, y):
            self.screen.blit(surf, (cx - surf.get_width() // 2, y))

        y = cy - 130
        cx_blit(font_sm.render("MISSION BRIEFING", True, (0, 180, 130)), y); y += 28
        cx_blit(font_big.render(f"SECTOR {self.level}", True, (0, 255, 200)), y); y += 54
        cx_blit(font_med.render(self.get_sector_name(), True, (255, 215, 60)), y); y += 38

        # Ghost list
        idx2 = min(self.level - 1, len(self.SECTOR_DEFS) - 1)
        ghost_list2 = self.SECTOR_DEFS[idx2][1]
        counts: dict = {}
        for cls in ghost_list2:
            counts[cls.__name__] = counts.get(cls.__name__, 0) + 1
        total_ghosts = len(self.ghosts) + self._insider_count + self._decoy_count
        cx_blit(font_sm.render(f"{total_ghosts} HOSTILES DETECTED", True, (220, 80, 100)), y); y += 22
        GHOST_LABELS = {
            "GhostBouncer": "BOUNCER", "GhostClimberCW": "CLIMBER",
            "GhostClimberCCW": "CLIMBER", "GhostDasher": "DASHER",
            "GhostReverser": "REVERSER", "GhostFreezer": "FREEZER",
            "GhostInsider": "INSIDER", "GhostWatcher": "WATCHER",
            "GhostGatekeeper": "GATEKEEPER", "GhostDecoy": "DECOY",
        }
        merged_counts: dict = {}
        for cls_name, cnt in counts.items():
            label = GHOST_LABELS.get(cls_name, cls_name)
            merged_counts[label] = merged_counts.get(label, 0) + cnt
        for label, cnt in merged_counts.items():
            cx_blit(font_sm.render(f"  x{cnt}  {label}", True, (160, 160, 200)), y); y += 18

        y += 10
        cx_blit(font_sm.render("OBJECTIVE: CAPTURE 80% OF TERRITORY", True, (80, 180, 120)), y); y += 30
        blink = (self._tick // 22) % 2 == 0
        if blink:
            cx_blit(font_med.render("SPACE / ENTER  —  LAUNCH", True, (0, 255, 180)), y)

        if self._confirm_quit:
            self._draw_confirm_quit()

    # ── PLAY ─────────────────────────────────────────────────────────────────

    def _play_mode(self) -> None:
        if self._confirm_quit:
            self.screen.fill((10, 10, 20))
            self.grid_manager.draw(self.screen, offset_y=self.HUD_HEIGHT, infection=self._infection)
            self.player.draw(self.screen, offset_y=self.HUD_HEIGHT)
            for g in self.ghosts:
                g.draw(self.screen, offset_y=self.HUD_HEIGHT)
            self._draw_hud()
            self._draw_confirm_quit()
            return

        if self._infection:
            self._tick_infection()

        if getattr(self.player, 'is_frozen', False):
            self.player.freeze_timer -= 1
            if self.player.freeze_timer <= 0:
                self.player.is_frozen = False
            # If frozen while trailing, clear trail and snap back to safe ground
            if self.player.is_trailing and self.grid_manager.trail:
                sx, sy = self.grid_manager.trail[0]
                for y in range(self.grid_manager.height):
                    for x in range(self.grid_manager.width):
                        if self.grid_manager.grid[y][x] == 2:
                            self.grid_manager.grid[y][x] = 0
                self.grid_manager.trail.clear()
                self.grid_manager.start_position = (-1, -1)
                self.player.is_trailing = False
                self.player.set_position(sx, sy)

        if getattr(self.player, 'is_cursed', False):
            self.player.curse_timer -= 1
            if self.player.curse_timer <= 0:
                self.player.is_cursed = False

        if not getattr(self.player, 'is_frozen', False):
            raw_keys = pygame.key.get_pressed()
            if getattr(self.player, 'is_cursed', False):
                class _InvertedKeys:
                    def __init__(self, k):  self._k = k
                    def __getitem__(self, key):
                        swap = {
                            pygame.K_LEFT:  pygame.K_RIGHT,
                            pygame.K_RIGHT: pygame.K_LEFT,
                            pygame.K_UP:    pygame.K_DOWN,
                            pygame.K_DOWN:  pygame.K_UP,
                            pygame.K_a:     pygame.K_d,
                            pygame.K_d:     pygame.K_a,
                            pygame.K_w:     pygame.K_s,
                            pygame.K_s:     pygame.K_w,
                        }
                        return self._k[swap.get(key, key)]
                keys = _InvertedKeys(raw_keys)
            else:
                keys = raw_keys
            item_pos = None
            if self.item_manager and self.item_manager._item is not None:
                itm = self.item_manager._item
                item_pos = (itm.grid_x, itm.grid_y)
            self.player.move_with_collision(keys, self.grid_manager, item_pos=item_pos)

        self.player.clamp_to_bounds(self.screen_width, self.screen_height - self.HUD_HEIGHT)
        self.screen.fill((10, 10, 20))
        self.grid_manager.update_grid()
        self.grid_manager.draw(self.screen, offset_y=self.HUD_HEIGHT, infection=self._infection)
        self.player.draw(self.screen, offset_y=self.HUD_HEIGHT)
        for g in self.ghosts:
            g.update(self.grid_manager)
            g.draw(self.screen, offset_y=self.HUD_HEIGHT)
        self.handle_collisions()
        self._try_spawn_insider()

        if self.item_manager and self.item_manager.banana_active:
            self.item_manager.tick_slime(self.ghosts)

        if self.item_manager:
            self.item_manager.update(self.player, self.ghosts, self.grid_manager, self.level, sfx=self.sfx)
            collected = self.item_manager.last_collected
            if collected:
                self.item_manager.last_collected = None
                _ITEM_FLASH = {
                    'lightning': (255, 230,   0),
                    'snow':      (160, 220, 255),
                    'sword':     (210, 160, 255),
                    'slime':     ( 80, 220,  80),
                    'heart':     (255,  80, 120),
                    'star':      (255, 255, 200),
                }
                flash_col = _ITEM_FLASH.get(collected)
                if flash_col:
                    self._add_flash(flash_col, alpha=65, life=45)
                if collected == 'heart':
                    px, py = self.player.get_position()
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

        # ── Screen tint overlays ──────────────────────────────────────────
        tint = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        freeze_timer = getattr(self.player, 'freeze_timer', 0)
        curse_timer  = getattr(self.player, 'curse_timer',  0)
        if self.item_manager and self.item_manager.star_active:
            t = self._tick
            import math
            sr = int(127 + 127 * math.sin(t * 0.07))
            sg = int(127 + 127 * math.sin(t * 0.07 + 2.1))
            sb = int(127 + 127 * math.sin(t * 0.07 + 4.2))
            tint.fill((sr, sg, sb, 35))
            self.screen.blit(tint, (0, 0))
        else:
            if self.item_manager and self.item_manager.lightning_active:
                tint.fill((255, 230, 0, 28)); self.screen.blit(tint, (0, 0))
            if self.item_manager and self.item_manager.snow_active:
                tint.fill((160, 220, 255, 32)); self.screen.blit(tint, (0, 0))
            if self.item_manager and self.item_manager.sword_active:
                tint.fill((210, 160, 255, 28)); self.screen.blit(tint, (0, 0))
            if self.item_manager and self.item_manager.banana_active:
                tint.fill((80, 220, 80, 28)); self.screen.blit(tint, (0, 0))
        if freeze_timer > 0:
            tint.fill((30, 100, 220, 40)); self.screen.blit(tint, (0, 0))
        if curse_timer > 0:
            tint.fill((160, 255, 0, 35)); self.screen.blit(tint, (0, 0))
        self._draw_screen_flash()

        if self.grid_manager.calculate_coverage() >= 80.0:
            self.change_level()
        if self.player.lives <= 0:
            self.update_game_state(GAME_OVER)

    # ── GAME OVER ────────────────────────────────────────────────────────────

    def _game_over_mode(self) -> None:
        if not getattr(self, '_gameover_sfx_played', False):
            self._gameover_sfx_played = True
            self._add_flash((220, 40, 55), alpha=90, life=60)

        self.screen.fill((20, 5, 8))
        cx = self.screen_width  // 2
        cy = self.screen_height // 2

        def cx_blit(surf, y):
            self.screen.blit(surf, (cx - surf.get_width() // 2, y))

        f_big  = pygame.font.Font(None, 64)
        f_med  = pygame.font.Font(None, 32)
        f_sm   = pygame.font.Font(None, 22)

        y = cy - 120
        cx_blit(f_sm.render("MISSION FAILED", True, (180, 50, 60)), y); y += 30
        pygame.draw.line(self.screen, (80, 20, 25), (cx - 200, y), (cx + 200, y), 1); y += 14
        cx_blit(f_big.render("GAME OVER", True, (220, 40, 55)), y); y += 58
        pygame.draw.line(self.screen, (60, 15, 20), (cx - 180, y), (cx + 180, y), 1); y += 18
        cx_blit(f_med.render(f"SCORE:  {self.score}", True, (200, 140, 145)), y); y += 34
        cx_blit(f_med.render(f"SECTOR: {self.level}", True, (200, 140, 145)), y); y += 40
        pygame.draw.line(self.screen, (60, 15, 20), (cx - 180, y), (cx + 180, y), 1); y += 16
        blink = (self._tick // 28) % 2 == 0
        if blink:
            cx_blit(f_med.render("SPACE — TRY AGAIN", True, (220, 60, 75)), y)
        y += 34
        cx_blit(f_sm.render("ESC — RETURN TO MENU", True, (100, 40, 50)), y)
        self._draw_screen_flash()

    # ── COMPLETE ─────────────────────────────────────────────────────────────

    def _game_complete_mode(self) -> None:
        if not self._complete_sfx_played:
            self._complete_sfx_played = True
            if self.sfx: self.sfx.play_level_complete()
            self._add_flash((100, 255, 120), alpha=90, life=60)

        self.screen.fill((4, 16, 10))
        cx = self.screen_width  // 2
        cy = self.screen_height // 2

        def cx_blit(surf, y):
            self.screen.blit(surf, (cx - surf.get_width() // 2, y))

        f_big = pygame.font.Font(None, 64)
        f_med = pygame.font.Font(None, 32)
        f_sm  = pygame.font.Font(None, 22)

        y = cy - 120
        cx_blit(f_sm.render("ALL SECTORS SECURED", True, (0, 180, 100)), y); y += 30
        pygame.draw.line(self.screen, (0, 80, 50), (cx - 200, y), (cx + 200, y), 1); y += 14
        cx_blit(f_big.render("YOU WIN!", True, (100, 255, 120)), y); y += 58
        pygame.draw.line(self.screen, (0, 70, 40), (cx - 180, y), (cx + 180, y), 1); y += 18
        cx_blit(f_med.render(f"FINAL SCORE:  {self.score}", True, (140, 210, 145)), y); y += 34
        cx_blit(f_med.render(f"SECTORS: {len(self.SECTOR_DEFS)}", True, (140, 210, 145)), y); y += 40
        pygame.draw.line(self.screen, (0, 70, 40), (cx - 180, y), (cx + 180, y), 1); y += 16
        blink = (self._tick // 28) % 2 == 0
        if blink:
            cx_blit(f_med.render("SPACE — PLAY AGAIN", True, (80, 220, 100)), y)
        y += 34
        cx_blit(f_sm.render("ESC — RETURN TO MENU", True, (40, 100, 60)), y)

        self._draw_screen_flash()

    # ── CONFIRM QUIT ─────────────────────────────────────────────────────────

    def _draw_confirm_quit(self) -> None:
        cx = self.screen_width  // 2
        cy = self.screen_height // 2

        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.set_alpha(140)
        overlay.fill((0, 0, 10))
        self.screen.blit(overlay, (0, 0))

        pw, ph = 360, 180
        px, py = cx - pw // 2, cy - ph // 2
        pygame.draw.rect(self.screen, (10, 18, 30), (px, py, pw, ph))
        pygame.draw.rect(self.screen, (0, 150, 110), (px, py, pw, ph), 2)

        f_title = pygame.font.Font(None, 38)
        f_sub   = pygame.font.Font(None, 22)
        f_btn   = pygame.font.Font(None, 24)

        def cx_blit(surf, y):
            self.screen.blit(surf, (cx - surf.get_width() // 2, y))

        cx_blit(f_title.render("ABANDON MISSION?", True, (220, 230, 255)), py + 22)
        cx_blit(f_sub.render("All unsaved progress will be lost.", True, (100, 120, 115)), py + 62)
        pygame.draw.line(self.screen, (0, 80, 60), (px + 20, py + 90), (px + pw - 20, py + 90), 1)
        cx_blit(f_btn.render("ENTER — LEAVE    ESC — STAY", True, (0, 200, 150)), py + 104)

    # ── ALL LOGIC BELOW UNCHANGED ─────────────────────────────────────────────

    def handle_collisions(self) -> None:
        if self.player.is_iframe:
            return
        if getattr(self.player, 'sword_immune', False):
            return

        _can_start_infection = (self._infection is None)

        px, py = self.player.get_position()
        margin     = self.block_size * 0.35
        px_inner   = px + margin
        py_inner   = py + margin
        inner_size = self.block_size - margin * 2

        pgx, pgy = self.player.get_grid_position()
        for g in self.ghosts:
            if not getattr(g, 'is_insider', False) and not getattr(g, 'is_gatekeeper', False):
                continue
            if getattr(g, 'is_decoy', False):
                continue
            gx_pos = g.x + self.block_size / 2
            gy_pos = g.y + self.block_size / 2
            overlaps = (abs(gx_pos - (px + self.block_size / 2)) < inner_size and
                        abs(gy_pos - (py + self.block_size / 2)) < inner_size)
            if overlaps:
                self._player_hit()
                return
            # Check if player is standing in a gatekeeper blocked cell
            if getattr(g, 'is_gatekeeper', False):
                if g.is_border_blocked(pgx, pgy):
                    self._player_hit()
                    return

        for g in self.ghosts:
            if getattr(g, 'is_insider', False) or getattr(g, 'is_gatekeeper', False):
                continue
            if getattr(g, 'is_decoy', False):
                dgx = int(g.x // self.block_size)
                dgy = int(g.y // self.block_size)
                if self.grid_manager.get_cell(dgx, dgy) == 1:
                    continue

            ghost_gx = int((g.x + self.block_size / 2) // self.block_size)
            ghost_gy = int((g.y + self.block_size / 2) // self.block_size)

            gx_pos = g.x + self.block_size / 2
            gy_pos = g.y + self.block_size / 2
            overlaps = (abs(gx_pos - (px + self.block_size / 2)) < inner_size and
                        abs(gy_pos - (py + self.block_size / 2)) < inner_size)
            on_trail = (ghost_gx, ghost_gy) in set(self.grid_manager.trail)

            def _player_has_status():
                return getattr(self.player, 'is_cursed', False)

            if getattr(g, 'is_freezer', False):
                cooldown = getattr(g, '_freeze_cooldown', 0)
                if cooldown > 0:
                    g._freeze_cooldown = cooldown - 1
                    continue
                if overlaps:
                    if not getattr(self.player, 'is_frozen', False):
                        FREEZE_DURATION = 300
                        self.player.is_frozen    = True
                        self.player.freeze_timer = FREEZE_DURATION
                        g._freeze_cooldown = FREEZE_DURATION
                        self._add_flash((30, 100, 220), alpha=65, life=45)
                        return
                    else:
                        self._player_hit()
                        return
                if on_trail and not overlaps:
                    if not _player_has_status() and _can_start_infection:
                        self._start_infection(ghost_gx, ghost_gy)
                    return
                continue

            if getattr(g, 'is_reverser', False):
                cooldown = getattr(g, '_curse_cooldown', 0)
                if cooldown > 0:
                    g._curse_cooldown = cooldown - 1
                    continue
                if overlaps or on_trail:
                    if not getattr(self.player, 'is_cursed', False):
                        CURSE_DURATION = 240
                        self.player.is_cursed   = True
                        self.player.curse_timer = CURSE_DURATION
                        g._curse_cooldown = CURSE_DURATION
                        self._add_flash((160, 255, 0), alpha=65, life=45)
                    continue
                continue

            if getattr(g, 'is_dasher', False):
                if overlaps:
                    self._player_hit()
                    return
                if on_trail and not overlaps:
                    if not _player_has_status() and _can_start_infection:
                        self._start_infection(ghost_gx, ghost_gy)
                    return
                continue

            if getattr(g, 'is_watcher', False):
                if on_trail and not overlaps:
                    if not _player_has_status() and _can_start_infection:
                        self._start_infection(ghost_gx, ghost_gy)
                    return
                if overlaps:
                    self._player_hit()
                    return
                continue

            if on_trail and not overlaps:
                if not _player_has_status() and _can_start_infection:
                    self._start_infection(ghost_gx, ghost_gy)
                return
            if overlaps:
                self._player_hit()
                return

    def _start_infection(self, hit_gx, hit_gy):
        trail = self.grid_manager.trail
        if not trail:
            self._player_hit()
            return
        hit_idx = None
        for i, (tx, ty) in enumerate(trail):
            if tx == hit_gx and ty == hit_gy:
                hit_idx = i
                break
        if hit_idx is None:
            hit_idx = 0
        ordered = trail[hit_idx:]
        self._infection = {
            'cells':  ordered,
            'front':  0,
            'timer':  0,
            'speed':  2,
        }

    def _tick_infection(self):
        inf = self._infection
        inf['timer'] += 1
        if inf['timer'] >= inf['speed']:
            inf['timer'] = 0
            inf['front'] += 1
            if self.sfx: self.sfx.play_infection_tick()
            pgx, pgy = self.player.get_grid_position()
            current_front_idx = inf['front']
            cells = inf['cells']
            if current_front_idx >= len(cells):
                self._infection = None
                self._player_hit()
                return
            fx, fy = cells[current_front_idx]
            if (fx, fy) == (pgx, pgy):
                self._infection = None
                self._player_hit()

    def _player_hit(self):
        self._infection = None
        self._screen_flash = []
        self.player.is_frozen = False
        self.player.freeze_timer = 0
        self.player.is_cursed = False
        self.player.curse_timer = 0
        self.player.sword_immune = False
        if self.item_manager:
            self.item_manager._restore_player_speed(self.player)
            self.item_manager._restore_player_immunity(self.player)
            self.item_manager._restore_ghost_speeds(self.ghosts, 'snow')
            self.item_manager._restore_ghost_speeds(self.ghosts, 'banana')
            self.item_manager.lightning_timer = 0
            self.item_manager.snow_timer      = 0
            self.item_manager.sword_timer     = 0
            self.item_manager.banana_timer    = 0
            self.item_manager.star_timer      = 0
        # ── Stats: record death event ────────────────────────────────────────
        if self.stats and self.grid_manager:
            self.stats.on_player_death(
                level       = self.level,
                capture_pct = self.grid_manager.captured_area,
                player_pos  = self.player.get_position(),
                ghosts      = self.ghosts,
                block_size  = self.block_size,
            )
        if self.player.lose_life() > 0:
            if self.sfx: self.sfx.play_death()
            self.player.set_position(0, 0)
            self.player.reset_movement()
            self.grid_manager.trail.clear()
            self.grid_manager.start_position = (-1, -1)
            for y in range(self.grid_manager.height):
                for x in range(self.grid_manager.width):
                    if self.grid_manager.grid[y][x] == 2:
                        self.grid_manager.grid[y][x] = 0
        else:
            if self.sfx: self.sfx.play_death()
            if self.sfx: self.sfx.play_game_over()
            self.update_game_state(GAME_OVER)

    def _try_spawn_insider(self) -> None:
        if self.grid_manager.captured_area < 15.0:
            return
        gw = self.grid_manager.width
        gh = self.grid_manager.height
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

    def _sword_kill_check(self) -> list:
        bs        = self.block_size
        px, py    = self.player.x, self.player.y
        trail_set = set(self.grid_manager.trail)
        surviving = []
        for g in self.ghosts:
            body_hit = (abs(g.x - px) < bs and abs(g.y - py) < bs)
            ghost_gx = int(g.x // bs)
            ghost_gy = int(g.y // bs)
            trail_hit = (ghost_gx, ghost_gy) in trail_set
            if body_hit or trail_hit:
                self.score += 50
                self.add_score_pop(int(g.x), int(g.y) + self.HUD_HEIGHT, 50)
                continue
            surviving.append(g)
        return surviving

    def add_score_pop(self, x, y, val):
        self._score_pops.append({'x': x, 'y': y + self.HUD_HEIGHT, 'val': val, 'life': 60})

    def update_game_state(self, ns): self.game_state = ns

    def change_level(self):
        self._infection = None
        self.level += 1
        if self.level > len(self.SECTOR_DEFS):
            self.update_game_state(COMPLETE)
            return
        if self.sfx: self.sfx.play_level_complete()
        self.player.set_position(0, 0)
        self.player.lives = 3
        self.player.is_trailing = False
        self.player.is_frozen = False
        self.player.freeze_timer = 0
        self.player.is_cursed = False
        self.player.curse_timer = 0
        self.player.sword_immune = False
        self.player.is_iframe = True
        self.player.iframe_timer = self.player.iframe_duration
        if self.item_manager:
            self.item_manager._restore_player_speed(self.player)
        self.item_manager = ItemManager(self.block_size)
        self.grid_manager.reset()
        self.ghosts = self._generate_ghosts()
        self.update_game_state(READY)