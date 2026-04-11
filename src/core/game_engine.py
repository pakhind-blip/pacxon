import pygame
import sys
import random
import math
from core.grid_manager import GridManager
from components.player import Player
from components.ghosts import GhostBouncer, GhostClimberCW, GhostClimberCCW
from core.menu import Menu

# State Constants
MENU, PLAY, GAME_OVER, COMPLETE, READY = 0, 1, 2, 3, 4
GHOST_TYPES = [GhostBouncer, GhostClimberCW, GhostClimberCCW]

class GameEngine:
    def __init__(self):
        self.game_state = MENU
        self.score = 0
        self.player, self.grid_manager = None, None
        self.ghosts = []
        self.screen, self.clock = None, None
        self.screen_width, self.screen_height = 800, 600
        self.block_size = 20
        self.HUD_HEIGHT = 70
        self.menu_system = None
        self.level = 1
        self._tick = 0
        # Score pop particles
        self._score_pops = []  # list of {x, y, val, life}

    def _generate_ghosts(self) -> list:
        ghosts = []
        grid_width = self.screen_width // self.block_size
        grid_height = (self.screen_height - self.HUD_HEIGHT) // self.block_size
        for _ in range(self.level):
            ghost_cls = random.choice(GHOST_TYPES)
            gx, gy = random.randint(5, grid_width - 2), random.randint(5, grid_height - 2)
            ghosts.append(ghost_cls(gx, gy, self.block_size))
        return ghosts

    def run(self, screen, clock, screen_width: int, screen_height: int) -> None:
        self.screen, self.clock = screen, clock
        self.screen_width, self.screen_height = screen_width, screen_height
        self.menu_system = Menu(screen, screen_width, screen_height)
        running = True
        while running:
            self._tick += 1
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and self.game_state != MENU: self.game_state = MENU
                    self._handle_input(event)
            
            if self.game_state == MENU: self.menu_system.draw()
            elif self.game_state == READY: self._ready_mode()
            elif self.game_state == PLAY: self._play_mode()
            elif self.game_state == GAME_OVER: self._game_over_mode()
            elif self.game_state == COMPLETE: self._game_complete_mode()
            
            pygame.display.flip()
            self.clock.tick(60)

    def _handle_input(self, event) -> None:
        if self.game_state == MENU:
            res = self.menu_system.handle_input(event)
            if res == "start": self._start_game()
            elif res == "quit": pygame.quit(); sys.exit()
        elif self.game_state == READY and event.key == pygame.K_SPACE: 
            self.update_game_state(PLAY)
        elif self.game_state == PLAY and event.key == pygame.K_r: 
            self._reset_game()
        elif self.game_state == GAME_OVER and event.key == pygame.K_SPACE: 
            self._start_game()

    def _start_game(self) -> None:
        self.score, self.level = 0, 1
        self._init_game()
        self.update_game_state(READY)

    def _init_game(self) -> None:
        gw, gh = self.screen_width // self.block_size, (self.screen_height - self.HUD_HEIGHT) // self.block_size
        self.player = Player(width=self.block_size, height=self.block_size, block_size=self.block_size)
        self.player.set_position(0, 0)
        self.grid_manager = GridManager(gw, gh, self.player, self, self.block_size)
        self.ghosts = self._generate_ghosts()
        self._score_pops = []

    def _reset_game(self) -> None:
        self.player.set_position(0, 0)
        self.player.lives, self.player.is_trailing, self.player.is_iframe = 3, False, False
        self.grid_manager.reset()

    # ─── HUD ────────────────────────────────────────────────────────────────
    def _draw_hud(self) -> None:
        t = self._tick

        # ── Background panel
        hud_rect = pygame.Rect(0, 0, self.screen_width, self.HUD_HEIGHT)
        pygame.draw.rect(self.screen, (8, 8, 20), hud_rect)

        # Animated accent line with scanner glow
        line_y = self.HUD_HEIGHT - 1
        pygame.draw.line(self.screen, (0, 80, 60), (0, line_y), (self.screen_width, line_y), 2)
        scan_x = int((t * 3) % (self.screen_width + 100)) - 50
        for i in range(50):
            alpha = int(255 * (1 - i / 50))
            sx = scan_x - i
            if 0 <= sx < self.screen_width:
                s = pygame.Surface((1, 2), pygame.SRCALPHA)
                s.fill((0, 255, 180, alpha))
                self.screen.blit(s, (sx, line_y - 1))

        font_label = pygame.font.Font(None, 18)
        font_val   = pygame.font.Font(None, 30)

        # ── Score
        lbl = font_label.render("SCORE", True, (60, 180, 140))
        val = font_val.render(str(self.score), True, (0, 255, 180))
        self.screen.blit(lbl, (18, 10))
        self.screen.blit(val, (18, 26))

        # ── Sector
        lbl2 = font_label.render("SECTOR", True, (60, 180, 140))
        val2 = font_val.render(str(self.level), True, (200, 200, 255))
        self.screen.blit(lbl2, (130, 10))
        self.screen.blit(val2, (130, 26))

        # ── Capture progress bar (center)
        bw, bh = 240, 12
        bx = self.screen_width // 2 - bw // 2
        by = 12

        # Label
        cap_label = font_label.render("CAPTURE PROGRESS", True, (60, 180, 140))
        self.screen.blit(cap_label, (bx + bw // 2 - cap_label.get_width() // 2, by - 2))

        # Bar track
        pygame.draw.rect(self.screen, (20, 30, 25), (bx, by + 14, bw, bh), border_radius=4)
        pygame.draw.rect(self.screen, (0, 60, 50), (bx, by + 14, bw, bh), 1, border_radius=4)

        # Fill
        current_pct = self.grid_manager.captured_area
        fill = int((min(current_pct, 80.0) / 80.0) * bw)
        if fill > 0:
            # Gradient-ish: draw two rects
            pygame.draw.rect(self.screen, (0, 200, 130), (bx, by + 14, fill, bh), border_radius=4)
            pygame.draw.rect(self.screen, (0, 255, 180), (bx, by + 14, fill, bh // 3), border_radius=4)

        # Animated shimmer on bar
        shimmer_x = bx + int((t * 2) % (bw + 20)) - 10
        if fill > 0 and bx <= shimmer_x <= bx + fill:
            s = pygame.Surface((8, bh), pygame.SRCALPHA)
            s.fill((255, 255, 255, 40))
            self.screen.blit(s, (shimmer_x, by + 14))

        # Percentage text
        pct_txt = font_label.render(f"{current_pct:.1f}% / 80%", True, (160, 255, 220))
        self.screen.blit(pct_txt, (bx + bw + 8, by + 14))

        # ── Lives (right side) - glowing hearts
        lives_lbl = font_label.render("LIVES", True, (60, 180, 140))
        self.screen.blit(lives_lbl, (self.screen_width - 115, 10))
        for i in range(3):
            hx = self.screen_width - 110 + i * 32
            hy = 28
            alive = i < self.player.lives
            color = (255, 60, 100) if alive else (50, 20, 30)
            glow_color = (255, 100, 120, 60) if alive else None
            # Glow
            if alive:
                gs = pygame.Surface((20, 20), pygame.SRCALPHA)
                pygame.draw.circle(gs, (255, 60, 100, 50), (10, 10), 10)
                self.screen.blit(gs, (hx - 2, hy - 2))
            # Heart shape using circle + rect approximation
            pygame.draw.circle(self.screen, color, (hx + 4, hy + 3), 5)
            pygame.draw.circle(self.screen, color, (hx + 12, hy + 3), 5)
            pts = [(hx, hy + 6), (hx + 8, hy + 16), (hx + 16, hy + 6)]
            pygame.draw.polygon(self.screen, color, pts)

        # ── Score pop particles
        still_alive = []
        for pop in self._score_pops:
            pop['life'] -= 1
            pop['y'] -= 0.8
            alpha = int(255 * (pop['life'] / 60))
            fs = pygame.font.Font(None, 22)
            ts = fs.render(f"+{pop['val']}", True, (0, 255, 180))
            ts.set_alpha(alpha)
            self.screen.blit(ts, (pop['x'], int(pop['y'])))
            if pop['life'] > 0:
                still_alive.append(pop)
        self._score_pops = still_alive

    # ─── READY screen ───────────────────────────────────────────────────────
    def _ready_mode(self) -> None:
        self.screen.fill((8, 8, 20))
        self.grid_manager.draw(self.screen, offset_y=self.HUD_HEIGHT)
        self.player.draw(self.screen, offset_y=self.HUD_HEIGHT)
        for g in self.ghosts:
            g.draw(self.screen, offset_y=self.HUD_HEIGHT)
        self._draw_hud()

        # Dark overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        t = self._tick

        # Animated border
        pulse = int(40 + 20 * math.sin(t * 0.05))
        border_color = (0, pulse * 3, pulse * 2)
        pygame.draw.rect(self.screen, border_color, (30, 180, self.screen_width - 60, 220), 1)

        # Title
        f_xl = pygame.font.Font(None, 90)
        sector_text = f_xl.render(f"SECTOR  {self.level}", True, (0, 255, 200))
        glow_offset = int(2 * math.sin(t * 0.08))
        # Glow layer
        glow_surf = pygame.Surface(sector_text.get_size(), pygame.SRCALPHA)
        glow_surf.blit(sector_text, (0, 0))
        glow_surf.set_alpha(80)
        sx = self.screen_width // 2 - sector_text.get_width() // 2
        self.screen.blit(glow_surf, (sx + 3, 230 + glow_offset + 3))
        self.screen.blit(sector_text, (sx, 230 + glow_offset))

        # Ghost count info
        f_info = pygame.font.Font(None, 26)
        info = f_info.render(f"HOSTILES DETECTED: {len(self.ghosts)}", True, (255, 100, 120))
        self.screen.blit(info, (self.screen_width // 2 - info.get_width() // 2, 320))

        # Blinking prompt
        if (t // 30) % 2 == 0:
            f_s = pygame.font.Font(None, 32)
            p_t = f_s.render("[ SPACE ]  TO INITIALIZE", True, (180, 255, 230))
            self.screen.blit(p_t, (self.screen_width // 2 - p_t.get_width() // 2, 360))

    # ─── PLAY mode ──────────────────────────────────────────────────────────
    def _play_mode(self) -> None:
        self.player.move_with_collision(pygame.key.get_pressed(), self.grid_manager)
        self.player.clamp_to_bounds(self.screen_width, self.screen_height - self.HUD_HEIGHT)
        self.screen.fill((8, 8, 20))
        self.grid_manager.update_grid()
        self.grid_manager.draw(self.screen, offset_y=self.HUD_HEIGHT)
        self.player.draw(self.screen, offset_y=self.HUD_HEIGHT)
        for g in self.ghosts:
            g.update(self.grid_manager)
            g.draw(self.screen, offset_y=self.HUD_HEIGHT)
        self.handle_collisions()
        self._draw_hud()
        if self.grid_manager.calculate_coverage() >= 80.0:
            self.change_level()
        if self.player.lives <= 0:
            self.update_game_state(GAME_OVER)

    # ─── GAME OVER ──────────────────────────────────────────────────────────
    def _game_over_mode(self) -> None:
        t = self._tick
        self.screen.fill((12, 4, 4))

        # Scanlines effect
        for y in range(0, self.screen_height, 4):
            s = pygame.Surface((self.screen_width, 2), pygame.SRCALPHA)
            s.fill((0, 0, 0, 40))
            self.screen.blit(s, (0, y))

        # Pulsing red glow bg
        pulse = int(15 + 10 * abs(math.sin(t * 0.04)))
        bg_glow = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        bg_glow.fill((pulse * 4, 0, 0, 30))
        self.screen.blit(bg_glow, (0, 0))

        f_t = pygame.font.Font(None, 96)
        f_s = pygame.font.Font(None, 36)
        f_xs = pygame.font.Font(None, 26)

        shake = int(2 * math.sin(t * 0.3)) if t < 120 else 0
        title = f_t.render("CRITICAL FAILURE", True, (220, 30, 50))
        tx = self.screen_width // 2 - title.get_width() // 2 + shake
        # Red glow under title
        glow = pygame.Surface(title.get_size(), pygame.SRCALPHA)
        glow.blit(title, (0, 0))
        glow.set_alpha(60)
        self.screen.blit(glow, (tx + 4, 204))
        self.screen.blit(title, (tx, 200))

        score_txt = f_s.render(f"FINAL SCORE:  {self.score}", True, (200, 180, 180))
        self.screen.blit(score_txt, (self.screen_width // 2 - score_txt.get_width() // 2, 310))

        if (t // 35) % 2 == 0:
            restart = f_xs.render("PRESS  SPACE  TO REBOOT", True, (160, 100, 100))
            self.screen.blit(restart, (self.screen_width // 2 - restart.get_width() // 2, 370))

    # ─── GAME COMPLETE ──────────────────────────────────────────────────────
    def _game_complete_mode(self) -> None:
        t = self._tick
        self.screen.fill((4, 14, 8))

        # Particle stars
        random.seed(42)
        for _ in range(60):
            sx = random.randint(0, self.screen_width)
            sy = random.randint(0, self.screen_height)
            alpha = int(128 + 127 * math.sin(t * 0.05 + sx))
            s = pygame.Surface((3, 3), pygame.SRCALPHA)
            s.fill((0, 255, 120, alpha))
            self.screen.blit(s, (sx, sy))

        f_t = pygame.font.Font(None, 88)
        pulse = int(200 + 55 * abs(math.sin(t * 0.04)))
        color = (30, pulse, 80)
        title = f_t.render("SYSTEM SECURED", True, color)
        tx = self.screen_width // 2 - title.get_width() // 2
        self.screen.blit(title, (tx, 240))

        f_s = pygame.font.Font(None, 32)
        sc = f_s.render(f"SCORE: {self.score}", True, (100, 255, 180))
        self.screen.blit(sc, (self.screen_width // 2 - sc.get_width() // 2, 340))

    # ─── COLLISION (fixed) ──────────────────────────────────────────────────
    def handle_collisions(self) -> None:
        if self.player.is_iframe:
            return

        # Player is safe on wall cells (cell == 1)
        pgx, pgy = self.player.get_grid_position()
        if self.grid_manager.get_cell(pgx, pgy) == 1:
            return

        px, py = self.player.get_position()
        # Shrink hitbox so ghost has to be meaningfully overlapping
        margin = self.block_size * 0.35
        px_inner = px + margin
        py_inner = py + margin
        inner_size = self.block_size - margin * 2

        for g in self.ghosts:
            # Direct pixel overlap with shrunk hitbox
            overlaps = (g.x < px_inner + inner_size and
                        g.x + g.width > px_inner and
                        g.y < py_inner + inner_size and
                        g.y + g.height > py_inner)

            # Ghost on trail — only dangerous if player is also on trail
            ghost_gx = int(g.x // self.block_size)
            ghost_gy = int(g.y // self.block_size)
            on_trail = self.grid_manager.get_cell(ghost_gx, ghost_gy) == 2
            player_on_trail = self.grid_manager.get_cell(pgx, pgy) == 2

            if overlaps or (on_trail and player_on_trail):
                self._player_hit()
                return

    def _player_hit(self):
        if self.player.lose_life() > 0:
            self.player.set_position(0, 0)
            self.grid_manager.trail.clear()
            self.grid_manager.start_position = (-1, -1)
            for y in range(self.grid_manager.height):
                for x in range(self.grid_manager.width):
                    if self.grid_manager.grid[y][x] == 2:
                        self.grid_manager.grid[y][x] = 0
        else:
            self.update_game_state(GAME_OVER)

    def add_score_pop(self, x, y, val):
        self._score_pops.append({'x': x, 'y': y + self.HUD_HEIGHT, 'val': val, 'life': 60})

    def update_game_state(self, ns): self.game_state = ns

    def change_level(self):
        self.level += 1
        self.player.set_position(0, 0)
        self.player.lives = 3
        self.player.is_trailing = self.player.is_iframe = False
        self.grid_manager.reset()
        self.ghosts = self._generate_ghosts()
        self.update_game_state(READY)
