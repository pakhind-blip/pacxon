import pygame


class Menu:
    def __init__(self, screen, screen_width: int, screen_height: int):

        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.selected_option = 0
        self.options = ["Start Game", "Quit"]

    def draw(self) -> None:
        self.screen.fill((0, 0, 0))

        # Title
        font_title = pygame.font.Font(None, 74)
        title = font_title.render("PACXON", True, (255, 255, 255))
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 150))

        # Instructions
        font_text = pygame.font.Font(None, 36)
        instructions = [
            "Use ARROW KEYS or WASD to move",
            "Avoid ghosts and fill the grid",
            "Reach 80% coverage to advance!"
        ]
        y_offset = 250
        for line in instructions:
            text = font_text.render(line, True, (200, 200, 200))
            self.screen.blit(text, (self.screen_width // 2 - text.get_width() // 2, y_offset))
            y_offset += 35

        # Options
        font_option = pygame.font.Font(None, 48)
        y_offset = 380
        for i, option in enumerate(self.options):
            color = (255, 255, 0) if i == self.selected_option else (255, 255, 255)
            text = font_option.render(option, True, color)
            self.screen.blit(text, (self.screen_width // 2 - text.get_width() // 2, y_offset))
            y_offset += 50

        # Start prompt
        font_small = pygame.font.Font(None, 30)
        start_text = font_small.render("Press SPACE or ENTER to select", True, (150, 150, 150))
        self.screen.blit(start_text, (self.screen_width // 2 - start_text.get_width() // 2, 500))

    def handle_input(self, event) -> str:
        if event.key == pygame.K_UP or event.key == pygame.K_w:
            self.selected_option = (self.selected_option - 1) % len(self.options)
        elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
            self.selected_option = (self.selected_option + 1) % len(self.options)
        elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
            if self.selected_option == 0:
                return "start"
            elif self.selected_option == 1:
                return "quit"
        return None