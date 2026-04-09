import pygame
import sys
from core.grid_manager import GridManager
from components.player import Player
from components.ghosts import GhostBouncer, GhostClimber
from core.menu import Menu  # Ensure this path is correct

MENU = 0
PLAY = 1
GAME_OVER = 2

class GameEngine:
    def __init__(self):
        self.game_state = MENU
        self.score = 0
        self.level = 1
        self.player = None
        self.grid_manager = None
        self.ghosts = []
        self.screen = None
        self.clock = None
        self.screen_width = 800
        self.screen_height = 600
        self.block_size = 20
        self.HUD_HEIGHT = 60 
        self.menu_system = None # Initialized in run()

    def run(self, screen, clock, screen_width: int, screen_height: int) -> None:
        self.screen = screen
        self.clock = clock
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.menu_system = Menu(screen, screen_width, screen_height) #

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and self.game_state != MENU:
                        self.game_state = MENU
                    self._handle_input(event)

            if self.game_state == MENU:
                self._menu_mode()
            elif self.game_state == PLAY:
                self._play_mode()
            elif self.game_state == GAME_OVER:
                self._game_over_mode()

            pygame.display.flip()
            self.clock.tick(60)

    def _handle_input(self, event) -> None:
        if self.game_state == MENU:
            # Delegate input to the menu class
            result = self.menu_system.handle_input(event)
            if result == "start":
                self._start_game()
            elif result == "quit":
                pygame.quit()
                sys.exit()
        elif self.game_state == PLAY:
            if event.key == pygame.K_r:
                self._reset_game()
        elif self.game_state == GAME_OVER:
            if event.key == pygame.K_SPACE:
                self._start_game()

    def _start_game(self) -> None:
        self.score = 0 
        self.level = 1
        self._init_game()
        self.update_game_state(PLAY)

    def _init_game(self) -> None:
        grid_width = self.screen_width // self.block_size
        grid_height = (self.screen_height - self.HUD_HEIGHT) // self.block_size

        self.player = Player(
            width=self.block_size,
            height=self.block_size,
            block_size=self.block_size
        )
        self.player.set_position(0, 0)

        self.grid_manager = GridManager(grid_width, grid_height, self.player, self, self.block_size)

        self.ghosts = [
            GhostBouncer(10, 10, self.block_size),
            GhostBouncer(20, 15, self.block_size),
            GhostClimber(0, 10, self.block_size),
            GhostClimber(0, 20, self.block_size)
        ]

    def _reset_game(self) -> None:
        self.player.set_position(0, 0)
        self.player.lives = 3
        self.player.is_trailing = False
        self.grid_manager.reset()

    def _advance_level(self) -> None:
        self.level += 1
        self.score += 1000
        self.player.set_position(0, 0)
        self.player.is_trailing = False
        self.grid_manager.reset()

    def _menu_mode(self) -> None:
        # Use the menu system's draw method
        self.menu_system.draw()

    def _game_over_mode(self) -> None:
        self.screen.fill((0, 0, 0))
        font_title = pygame.font.Font(None, 80)
        title = font_title.render("GAME OVER", True, (255, 50, 50))
        self.screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 150))
        font_stats = pygame.font.Font(None, 48)
        score_text = font_stats.render(f"Final Score: {self.score}", True, (255, 255, 255))
        level_text = font_stats.render(f"Final Level: {self.level}", True, (255, 255, 255))
        self.screen.blit(score_text, (self.screen_width // 2 - score_text.get_width() // 2, 250))
        self.screen.blit(level_text, (self.screen_width // 2 - level_text.get_width() // 2, 310))
        font_restart = pygame.font.Font(None, 36)
        restart_text = font_restart.render("Press SPACE to try again", True, (200, 200, 200))
        self.screen.blit(restart_text, (self.screen_width // 2 - restart_text.get_width() // 2, 450))

    def _play_mode(self) -> None:
        keys = pygame.key.get_pressed()
        self.player.move_with_collision(keys, self.grid_manager)
        self.player.clamp_to_bounds(self.screen_width, self.screen_height - self.HUD_HEIGHT)
        self.screen.fill((0, 0, 0))
        self.grid_manager.update_grid()
        self.grid_manager.draw(self.screen, offset_y=self.HUD_HEIGHT)
        self.player.draw(self.screen, offset_y=self.HUD_HEIGHT)
        for ghost in self.ghosts:
            ghost.update(self.grid_manager)
            ghost.draw(self.screen, offset_y=self.HUD_HEIGHT)
        self.handle_collisions()
        self._draw_hud()
        coverage = self.grid_manager.calculate_coverage()
        if coverage >= 80.0:
            self._advance_level()
        if self.player.lives <= 0:
            self.update_game_state(GAME_OVER)

    def _draw_hud(self) -> None:
        font = pygame.font.Font(None, 28)
        score_text = font.render(f"SCORE: {self.score}", True, (255, 255, 255))
        lives_text = font.render(f"LIVES: {self.player.lives}", True, (255, 255, 255))
        level_text = font.render(f"LEVEL: {self.level}", True, (255, 255, 255))
        val = self.grid_manager.captured_area
        formatted_coverage = f"{int(val)}" if val == int(val) else f"{val:.1f}"
        coverage_text = font.render(f"PROGRESS: {formatted_coverage}% / 80%", True, (0, 255, 0))
        margin = 15
        self.screen.blit(score_text, (margin, 10))
        self.screen.blit(lives_text, (self.screen_width - lives_text.get_width() - margin, 10))
        self.screen.blit(level_text, (margin, 35))
        self.screen.blit(coverage_text, (self.screen_width // 2 - coverage_text.get_width() // 2, 20))

    def handle_collisions(self) -> None:
        player_pos = self.player.get_position()
        for ghost in self.ghosts:
            if ghost.is_collision(player_pos[0], player_pos[1]):
                self._player_hit()
                return
            gx = int(ghost.x // self.block_size)
            gy = int(ghost.y // self.block_size)
            if self.grid_manager.get_cell(gx, gy) == 2:
                self._player_hit()
                return

    def _player_hit(self):
        lives = self.player.lose_life()
        if lives > 0:
            self.player.set_position(0, 0)
            self.grid_manager.trail.clear()
            self.grid_manager.start_position = (-1, -1)
            for y in range(self.grid_manager.height):
                for x in range(self.grid_manager.width):
                    if self.grid_manager.grid[y][x] == 2:
                        self.grid_manager.grid[y][x] = 0
        else:
            self.update_game_state(GAME_OVER)

    def update_game_state(self, new_state: int) -> None:
        self.game_state = new_state