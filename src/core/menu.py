import pygame

class Menu:
    def __init__(self, screen, screen_width: int, screen_height: int):
        self.screen = screen
        self.screen_width  = screen_width
        self.screen_height = screen_height
        self.selected_option = 0
        self.options = ["Play", "Index", "Graph", "How to Play", "Quit"]
        self.view = "MAIN"
        self.index_tab = "GHOST"
        self._ghost_scroll = 0
        self._item_scroll  = 0
        self._tick = 0

    def on_resize(self, new_width: int, new_height: int) -> None:
        self.screen_width  = new_width
        self.screen_height = new_height

    def draw(self):
        self._tick += 1
        self.screen.fill((20, 20, 30))

        if self.view == "MAIN":
            self._draw_main()
        elif self.view == "HOW_TO_PLAY":
            self._draw_how_to_play()
        elif self.view == "INDEX":
            self._draw_index()
        elif self.view == "GRAPH":
            self._draw_graph()

    def _center_text(self, surf, y):
        self.screen.blit(surf, (self.screen_width // 2 - surf.get_width() // 2, y))

    def _draw_main(self):
        cx = self.screen_width  // 2
        cy = self.screen_height // 2

        f_title = pygame.font.Font(None, 72)
        title = f_title.render("GRIDRUSH", True, (255, 230, 0))
        self._center_text(title, cy - 180)

        f_opt = pygame.font.Font(None, 36)
        for i, opt in enumerate(self.options):
            color = (0, 255, 180) if i == self.selected_option else (160, 160, 160)
            prefix = "> " if i == self.selected_option else "  "
            surf = f_opt.render(prefix + opt, True, color)
            self._center_text(surf, cy - 80 + i * 44)

        f_hint = pygame.font.Font(None, 20)
        hint = f_hint.render("UP/DOWN to navigate   SPACE/ENTER to select", True, (80, 80, 100))
        self._center_text(hint, self.screen_height - 40)

    def _draw_how_to_play(self):
        cx = self.screen_width  // 2
        y  = 60

        f_title = pygame.font.Font(None, 40)
        title = f_title.render("HOW TO PLAY", True, (0, 255, 180))
        self._center_text(title, y); y += 50

        pygame.draw.line(self.screen, (0, 100, 80), (cx - 280, y), (cx + 280, y), 1); y += 12

        instructions = [
            ("ARROW / WASD", "Move your ship around the grid"),
            ("EMPTY SPACE",  "Move into it to start laying a capture trail"),
            ("REACH WALL",   "Return to a wall to capture the enclosed area"),
            ("SELF-TRAIL",   "Crossing your own trail loses a life"),
            ("GHOSTS",       "Contact loses a life; some curse or freeze you"),
            ("TARGET: 80%",  "Capture 80% of the map to advance"),
            ("ESC",          "Return to main menu"),
        ]
        f_key  = pygame.font.Font(None, 24)
        f_desc = pygame.font.Font(None, 24)
        for key, desc in instructions:
            ks = f_key.render(key, True, (0, 220, 160))
            ds = f_desc.render(desc, True, (200, 200, 200))
            self.screen.blit(ks,  (cx - 280, y))
            self.screen.blit(ds,  (cx - 60,  y))
            y += 36

        y += 10
        f_back = pygame.font.Font(None, 22)
        back = f_back.render("ESC — BACK", True, (100, 100, 120))
        self._center_text(back, y)

    def _draw_index(self):
        cx = self.screen_width  // 2
        y  = 60

        f_title = pygame.font.Font(None, 40)
        title = f_title.render("INDEX", True, (0, 255, 180))
        self._center_text(title, y); y += 46

        # Tab bar
        for tab_name, tx in [("GHOST", cx - 100), ("ITEM", cx + 20)]:
            col = (0, 255, 180) if self.index_tab == tab_name else (100, 100, 120)
            ft = pygame.font.Font(None, 28)
            ts = ft.render(tab_name, True, col)
            self.screen.blit(ts, (tx, y))
        y += 34
        pygame.draw.line(self.screen, (0, 100, 80), (cx - 280, y), (cx + 280, y), 1); y += 10

        GHOST_DATA = {
            "GhostBouncer":    ("BOUNCER",     (255,  80, 160), "Ricochets off walls at high speed"),
            "GhostClimber":    ("CLIMBER",     (255, 140,  20), "Hugs walls and traces their edges"),
            "GhostDasher":     ("DASHER",      (255, 220,   0), "Wanders then snaps axis and dashes"),
            "GhostReverser":   ("REVERSER",    (160, 255,   0), "Contact reverses your controls"),
            "GhostFreezer":    ("FREEZER",     ( 30, 100, 220), "Charges up and fires a freeze pulse"),
            "GhostInsider":    ("INSIDER",     (  0, 220, 255), "Spawns and bounces inside your territory"),
            "GhostWatcher":    ("WATCHER",     (200,  50, 255), "Stationary; charges when it sees you"),
            "GhostGatekeeper": ("GATEKEEPER",  (255,  30,  30), "Patrols the border, blocks your path"),
            "GhostDecoy":      ("DECOY",       ( 50, 255,  80), "Hides as a wall tile, hits on reveal"),
        }
        ITEM_DATA = [
            ("LIGHTNING",  (255, 220,  0), "Boosts your movement speed"),
            ("SNOW",       ( 80, 180, 255), "Completely freezes all ghosts"),
            ("SWORD",      (220, 100, 255), "Kill ghosts on contact"),
            ("SLIME",      ( 50, 200,  50), "Slows all ghosts to 35% speed"),
            ("HEART",      (255,  60, 100), "Restores one life (max 3)"),
            ("STAR",       (255, 240,  80), "Activates all effects at once"),
        ]

        f_name = pygame.font.Font(None, 24)
        f_desc = pygame.font.Font(None, 20)
        row_h  = 30

        if self.index_tab == "GHOST":
            items = list(GHOST_DATA.values())
        else:
            items = [(n, c, d) for n, c, d in ITEM_DATA]

        for i, entry in enumerate(items):
            name, col, desc = entry
            ns = f_name.render(name, True, col)
            ds = f_desc.render(desc, True, (180, 180, 180))
            self.screen.blit(ns, (cx - 280, y + i * row_h))
            self.screen.blit(ds, (cx - 80,  y + i * row_h + 4))

        f_hint = pygame.font.Font(None, 20)
        hint = f_hint.render("LEFT/RIGHT switch tab   ESC back", True, (80, 80, 100))
        self._center_text(hint, self.screen_height - 30)

    def _draw_graph(self):
        cx = self.screen_width  // 2
        cy = self.screen_height // 2

        f_title = pygame.font.Font(None, 40)
        title = f_title.render("STATISTICS", True, (0, 255, 180))
        self._center_text(title, cy - 60)

        f_msg = pygame.font.Font(None, 30)
        msg = f_msg.render("COMING SOON", True, (160, 160, 160))
        self._center_text(msg, cy)

        f_back = pygame.font.Font(None, 22)
        back = f_back.render("ESC — BACK", True, (100, 100, 120))
        self._center_text(back, cy + 50)

    def handle_input(self, event) -> str:
        if event.type != pygame.KEYDOWN:
            return None
        if self.view != "MAIN":
            if event.key in [pygame.K_ESCAPE, pygame.K_BACKSPACE]:
                self.view = "MAIN"
            elif self.view == "INDEX":
                if event.key in [pygame.K_LEFT, pygame.K_a]:
                    self.index_tab = "GHOST"
                elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                    self.index_tab = "ITEM"
            return None
        if event.key in [pygame.K_UP, pygame.K_w]:
            self.selected_option = (self.selected_option - 1) % len(self.options)
        elif event.key in [pygame.K_DOWN, pygame.K_s]:
            self.selected_option = (self.selected_option + 1) % len(self.options)
        elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
            choice = self.options[self.selected_option]
            if choice == "Play":          return "start"
            elif choice == "How to Play": self.view = "HOW_TO_PLAY"
            elif choice == "Index":
                self.view = "INDEX"
                self.index_tab = "GHOST"
                self._ghost_scroll = 0
                self._item_scroll  = 0
            elif choice == "Graph":        return "graph"
            elif choice == "Quit":        return "quit"
        return None