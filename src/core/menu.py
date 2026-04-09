import pygame

class Menu:
    def __init__(self, screen, screen_width: int, screen_height: int):
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.selected_option = 0
        # Updated options list
        self.options = ["Play", "Graph", "How to Play", "Quit"]
        self.view = "MAIN"  # Tracks current sub-menu state

    def draw(self) -> None:
        self.screen.fill((0, 0, 0))
        
        if self.view == "MAIN":
            self._draw_main_menu()
        elif self.view == "HOW_TO_PLAY":
            self._draw_how_to_play()
        elif self.view == "GRAPH":
            self._draw_graph_placeholder()

    def _draw_main_menu(self) -> None:
        # Title
        font_title = pygame.font.Font(None, 80)
        title = font_title.render("PACXON", True, (255, 255, 0))
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 80))

        # Render menu options with a selection highlight
        font_option = pygame.font.Font(None, 50)
        for i, option in enumerate(self.options):
            if i == self.selected_option:
                color = (0, 255, 0)
                text_str = f"> {option} <"
            else:
                color = (255, 255, 255)
                text_str = option
            
            text = font_option.render(text_str, True, color)
            self.screen.blit(text, (self.screen_width // 2 - text.get_width() // 2, 220 + i * 60))

    def _draw_how_to_play(self) -> None:
        font_title = pygame.font.Font(None, 60)
        title = font_title.render("How to Play", True, (0, 255, 255))
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 80))

        font_text = pygame.font.Font(None, 32)
        instructions = [
            "Use ARROW KEYS or WASD to move.",
            "Capture territory by creating closed loops.",
            "If ghosts hit you or your trail, you lose a life.",
            "Capture 80% of the map to advance levels.",
            "",
            "Press ESC or BACKSPACE to return"
        ]
        for i, line in enumerate(instructions):
            text = font_text.render(line, True, (200, 200, 200))
            self.screen.blit(text, (self.screen_width // 2 - text.get_width() // 2, 200 + i * 40))

    def _draw_graph_placeholder(self) -> None:
        font_title = pygame.font.Font(None, 60)
        text = font_title.render("GRAPH", True, (255, 255, 255))
        self.screen.blit(text, (self.screen_width // 2 - text.get_width() // 2, self.screen_height // 2 - 30))
        
        font_small = pygame.font.Font(None, 30)
        back_text = font_small.render("Press ESC to return", True, (150, 150, 150))
        self.screen.blit(back_text, (self.screen_width // 2 - back_text.get_width() // 2, 450))

    def handle_input(self, event) -> str:
        if event.type != pygame.KEYDOWN:
            return None

        # Logic for exiting sub-menus
        if self.view != "MAIN":
            if event.key in [pygame.K_ESCAPE, pygame.K_BACKSPACE]:
                self.view = "MAIN"
            return None

        # Main menu navigation
        if event.key in [pygame.K_UP, pygame.K_w]:
            self.selected_option = (self.selected_option - 1) % len(self.options)
        elif event.key in [pygame.K_DOWN, pygame.K_s]:
            self.selected_option = (self.selected_option + 1) % len(self.options)
        elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
            choice = self.options[self.selected_option]
            if choice == "Play":
                return "start"
            elif choice == "Graph":
                self.view = "GRAPH"
            elif choice == "How to Play":
                self.view = "HOW_TO_PLAY"
            elif choice == "Quit":
                return "quit"
        return None