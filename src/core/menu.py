import pygame
import math
import random

class Menu:
    def __init__(self, screen, screen_width: int, screen_height: int):
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.selected_option = 0
        self.options = ["Play", "Graph", "How to Play", "Quit"]
        self.view = "MAIN"
        self._tick = 0

        # Particle field for background
        random.seed(99)
        self._particles = [
            {
                'x': random.uniform(0, screen_width),
                'y': random.uniform(0, screen_height),
                'vx': random.uniform(-0.3, 0.3),
                'vy': random.uniform(-0.4, -0.1),
                'r': random.uniform(1, 2.5),
                'brightness': random.uniform(0.3, 1.0),
            }
            for _ in range(80)
        ]

        # Theme colors
        self.C_BG      = (6, 6, 18)
        self.C_ACCENT  = (0, 255, 200)
        self.C_DIM     = (0, 120, 95)
        self.C_TEXT    = (180, 200, 220)
        self.C_SEL     = (255, 255, 255)
        self.C_INACTIVE= (55, 65, 90)

    # ── helpers ────────────────────────────────────────────────────────────

    def _draw_particles(self):
        for p in self._particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            if p['y'] < -4:
                p['y'] = self.screen_height + 4
                p['x'] = random.uniform(0, self.screen_width)
            alpha = int(180 * p['brightness'] * abs(math.sin(self._tick * 0.015 + p['x'])))
            s = pygame.Surface((int(p['r'] * 2), int(p['r'] * 2)), pygame.SRCALPHA)
            pygame.draw.circle(s, (0, 255, 200, alpha), (int(p['r']), int(p['r'])), int(p['r']))
            self.screen.blit(s, (int(p['x'] - p['r']), int(p['y'] - p['r'])))

    def _draw_grid_bg(self):
        """Subtle animated perspective grid."""
        col = (0, 30, 22)
        spacing = 40
        t = self._tick
        for x in range(0, self.screen_width + spacing, spacing):
            offset = int(6 * math.sin(t * 0.02 + x * 0.01))
            pygame.draw.line(self.screen, col, (x, 0), (x, self.screen_height + offset), 1)
        for y in range(0, self.screen_height + spacing, spacing):
            offset = int(4 * math.sin(t * 0.02 + y * 0.01))
            pygame.draw.line(self.screen, col, (0, y + offset), (self.screen_width, y + offset), 1)

    # ── public ─────────────────────────────────────────────────────────────

    def draw(self) -> None:
        self._tick += 1
        self.screen.fill(self.C_BG)
        self._draw_grid_bg()
        self._draw_particles()

        if self.view == "MAIN":
            self._draw_main_menu()
        elif self.view == "HOW_TO_PLAY":
            self._draw_how_to_play()
        elif self.view == "GRAPH":
            self._draw_graph_placeholder()

    def _draw_main_menu(self) -> None:
        t = self._tick
        cx = self.screen_width // 2

        # ── Decorative top bar
        bar_alpha = int(120 + 60 * math.sin(t * 0.04))
        bar = pygame.Surface((self.screen_width, 3), pygame.SRCALPHA)
        bar.fill((0, 255, 200, bar_alpha))
        self.screen.blit(bar, (0, 50))

        # ── Title PACXON with glow layers
        font_title = pygame.font.Font(None, 110)
        title_surf = font_title.render("PACXON", True, self.C_ACCENT)
        tx = cx - title_surf.get_width() // 2

        # Multi-layer glow
        for radius, alpha in [(8, 20), (4, 40), (2, 80)]:
            glow = pygame.Surface(title_surf.get_size(), pygame.SRCALPHA)
            glow.blit(title_surf, (0, 0))
            glow.set_alpha(alpha)
            self.screen.blit(glow, (tx - radius, 68 - radius))
            self.screen.blit(glow, (tx + radius, 68 + radius))

        # Main title
        self.screen.blit(title_surf, (tx, 68))

        # ── Subtitle / tagline
        font_sub = pygame.font.Font(None, 22)
        sub = font_sub.render("TERRITORY  ACQUISITION  PROTOCOL  v2.0", True, self.C_DIM)
        self.screen.blit(sub, (cx - sub.get_width() // 2, 178))

        # ── Divider
        dw = 300
        pygame.draw.line(self.screen, self.C_DIM, (cx - dw // 2, 200), (cx + dw // 2, 200), 1)
        pygame.draw.circle(self.screen, self.C_ACCENT, (cx, 200), 4)

        # ── Menu options
        font_option = pygame.font.Font(None, 44)
        for i, option in enumerate(self.options):
            is_sel = (i == self.selected_option)
            y_pos = 230 + i * 62

            if is_sel:
                # Highlight panel
                highlight = pygame.Surface((self.screen_width, 48), pygame.SRCALPHA)
                highlight_alpha = int(25 + 15 * math.sin(t * 0.07))
                highlight.fill((0, 255, 200, highlight_alpha))
                self.screen.blit(highlight, (0, y_pos - 6))

                # Left accent bar
                pygame.draw.rect(self.screen, self.C_ACCENT, (0, y_pos - 6, 4, 48))

                # Corner decorations
                pygame.draw.line(self.screen, self.C_ACCENT,
                                 (cx - 180, y_pos - 8), (cx - 160, y_pos - 8), 2)
                pygame.draw.line(self.screen, self.C_ACCENT,
                                 (cx + 160, y_pos - 8), (cx + 180, y_pos - 8), 2)

                color = (255, 255, 255)
                prefix, suffix = "▶ ", " ◀"
            else:
                color = self.C_INACTIVE
                prefix, suffix = "  ", "  "

            label = font_option.render(f"{prefix}{option.upper()}{suffix}", True, color)
            self.screen.blit(label, (cx - label.get_width() // 2, y_pos))

        # ── Bottom tagline
        font_tiny = pygame.font.Font(None, 20)
        if (t // 40) % 2 == 0:
            hint = font_tiny.render("↑ ↓  NAVIGATE    ENTER / SPACE  SELECT", True, (40, 60, 55))
            self.screen.blit(hint, (cx - hint.get_width() // 2, self.screen_height - 30))

    def _draw_how_to_play(self) -> None:
        cx = self.screen_width // 2
        t = self._tick

        # Panel background
        panel = pygame.Surface((620, 320), pygame.SRCALPHA)
        panel.fill((0, 20, 16, 200))
        self.screen.blit(panel, (cx - 310, 120))
        pygame.draw.rect(self.screen, self.C_DIM, (cx - 310, 120, 620, 320), 1)

        font_title = pygame.font.Font(None, 56)
        title = font_title.render("MISSION  OBJECTIVES", True, self.C_ACCENT)
        self.screen.blit(title, (cx - title.get_width() // 2, 80))

        pygame.draw.line(self.screen, self.C_DIM, (cx - 240, 140), (cx + 240, 140), 1)

        font_text = pygame.font.Font(None, 28)
        instructions = [
            ("MOVE",    "ARROW KEYS  /  WASD"),
            ("CAPTURE", "Navigate empty space to claim territory"),
            ("DANGER",  "Avoid ghosts touching you or your trail"),
            ("WIN",     "Secure 80% of the map to advance"),
            ("RESET",   "Press  R  to reset your position"),
        ]
        for i, (key, desc) in enumerate(instructions):
            ky = 160 + i * 44
            k_surf = font_text.render(key, True, self.C_ACCENT)
            d_surf = font_text.render(desc, True, (160, 185, 175))
            self.screen.blit(k_surf, (cx - 270, ky))
            pygame.draw.line(self.screen, (0, 60, 50), (cx - 215, ky + 10), (cx - 200, ky + 10), 1)
            self.screen.blit(d_surf, (cx - 185, ky))

        # Back hint
        font_back = pygame.font.Font(None, 24)
        if (t // 35) % 2 == 0:
            back = font_back.render("[ ESC ]  TO RETURN", True, self.C_DIM)
            self.screen.blit(back, (cx - back.get_width() // 2, 470))

    def _draw_graph_placeholder(self) -> None:
        cx, cy = self.screen_width // 2, self.screen_height // 2
        t = self._tick

        # Panel
        panel = pygame.Surface((580, 300), pygame.SRCALPHA)
        panel.fill((0, 14, 10, 200))
        self.screen.blit(panel, (cx - 290, cy - 130))
        pygame.draw.rect(self.screen, self.C_DIM, (cx - 290, cy - 130, 580, 300), 1)

        font_title = pygame.font.Font(None, 52)
        title = font_title.render("SYSTEM TELEMETRY", True, self.C_SEL)
        self.screen.blit(title, (cx - title.get_width() // 2, cy - 100))

        # Fake animated graph bars
        font_small = pygame.font.Font(None, 22)
        labels = ["CPU", "MEM", "NET", "GPU", "I/O"]
        for i, lbl in enumerate(labels):
            bx = cx - 220 + i * 95
            bh_max = 80
            # animated bar height
            h = int(bh_max * abs(math.sin(t * 0.04 + i * 1.2)))
            by = cy + 30

            # Bar
            pygame.draw.rect(self.screen, (0, 40, 30), (bx, cy - 40, 60, bh_max + 10))
            pygame.draw.rect(self.screen, self.C_ACCENT, (bx, by - h, 60, h))
            pygame.draw.rect(self.screen, (200, 255, 240), (bx, by - h, 60, 4))

            l = font_small.render(lbl, True, self.C_DIM)
            self.screen.blit(l, (bx + 30 - l.get_width() // 2, by + 14))

        font_back = pygame.font.Font(None, 24)
        if (t // 35) % 2 == 0:
            back = font_back.render("[ ESC ]  TO RETURN", True, self.C_DIM)
            self.screen.blit(back, (cx - back.get_width() // 2, cy + 130))

    def handle_input(self, event) -> str:
        if event.type != pygame.KEYDOWN:
            return None
        if self.view != "MAIN":
            if event.key in [pygame.K_ESCAPE, pygame.K_BACKSPACE]:
                self.view = "MAIN"
            return None
        if event.key in [pygame.K_UP, pygame.K_w]:
            self.selected_option = (self.selected_option - 1) % len(self.options)
        elif event.key in [pygame.K_DOWN, pygame.K_s]:
            self.selected_option = (self.selected_option + 1) % len(self.options)
        elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
            choice = self.options[self.selected_option]
            if choice == "Play":      return "start"
            elif choice == "Graph":   self.view = "GRAPH"
            elif choice == "How to Play": self.view = "HOW_TO_PLAY"
            elif choice == "Quit":    return "quit"
        return None
