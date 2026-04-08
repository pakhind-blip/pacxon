# Game state constants
MENU = 0
PLAY = 1
GAME_OVER = 2


class GameEngine:
    def __init__(self):
        self.game_state = MENU
        self.score = 0
        self.level = 1

    def run(self) -> None:
        pass

    def handle_collisions(self) -> None:
        pass

    def update_game_state(self, new_state: int) -> None:
        self.game_state = new_state