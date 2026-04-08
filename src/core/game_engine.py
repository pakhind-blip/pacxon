import pygame

from core.grid_manager import GridManager
from components.player import Player
from components.ghosts import GhostBouncer, GhostClimber

# Game state constants
MENU = 0
PLAY = 1
GAME_OVER = 2


class GameEngine:
    """Controls the main game loop and state transitions.

    Manages game state, score, level, and collision handling.
    """

    def __init__(self):
        """Initialize game engine."""
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

    def run(self, screen, clock, screen_width: int, screen_height: int) -> None:
        """Main game loop.

        Controls the flow between menu, play, and game over states.

        Args:
            screen: Pygame display surface
            clock: Pygame clock for frame rate
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
        """
        self.screen = screen
        self.clock = clock
        self.screen_width = screen_width
        self.screen_height = screen_height

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
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
        """Handle input based on current game state."""
        if self.game_state == MENU:
            if event.key == pygame.K_SPACE:
                self._start_game()
        elif self.game_state == PLAY:
            if event.key == pygame.K_r:
                self._reset_game()
        elif self.game_state == GAME_OVER:
            if event.key == pygame.K_SPACE:
                self._start_game()

    def _start_game(self) -> None:
        """Initialize game and start play mode."""
        self.score = 0
        self.level = 1
        self._init_game()
        self.update_game_state(PLAY)

    def _init_game(self) -> None:
        """Initialize game objects."""
        grid_width = self.screen_width // self.block_size
        grid_height = self.screen_height // self.block_size

        self.player = Player(
            width=self.block_size,
            height=self.block_size,
            block_size=self.block_size
        )
        self.player.set_position(0, 0)

        self.grid_manager = GridManager(grid_width, grid_height, self.player,self, self.block_size)

        self.ghosts = [
        GhostBouncer(10, 10, self.block_size),
        GhostBouncer(10, 10, self.block_size),
        GhostClimber(0, 10, self.block_size),
        GhostClimber(0, 20, self.block_size) # Starts on border
        ]

    def _reset_game(self) -> None:
        """Reset game to initial state."""
        self.player.set_position(0, 0)
        self.player.lives = 3
        self.player.is_trailing = False
        self.player.trail_positions = []
        self.grid_manager.reset()

    def _advance_level(self) -> None:
        """Advance to next level when coverage reaches 80%."""
        self.level += 1
        self.score += 1000
        self.player.set_position(0, 0)
        self.player.is_trailing = False
        self.player.trail_positions = []
        self.grid_manager.reset()

    def _menu_mode(self) -> None:
        """Handle menu mode rendering and logic."""
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
            "",
            "Press SPACE to start"
        ]
        y_offset = 280
        for line in instructions:
            text = font_text.render(line, True, (200, 200, 200))
            self.screen.blit(text, (self.screen_width // 2 - text.get_width() // 2, y_offset))
            y_offset += 40

    def _play_mode(self) -> None:
        """Handle play mode logic and rendering."""
        keys = pygame.key.get_pressed()

        self.player.move_with_collision(keys, self.grid_manager)
        self.player.clamp_to_bounds(self.screen_width, self.screen_height)

        self.screen.fill((0, 0, 0))
        self.grid_manager.update_grid()
        self.grid_manager.draw(self.screen, color=(100, 100, 100))
        self.player.draw(self.screen)

        # Draw HUD
        self._draw_hud()

        for ghost in self.ghosts:
            ghost.update(self.grid_manager)
            ghost.draw(self.screen)
    
        self.handle_collisions()

        # Check for level completion (80% coverage)
        coverage = self.grid_manager.calculate_coverage()
        if coverage >= 80.0:
            self._advance_level()

        if self.player.lives <= 0:
            self.update_game_state(GAME_OVER)

    def _draw_hud(self) -> None:
        """Draw heads-up display with score, level, lives, and coverage."""
        font = pygame.font.Font(None, 30)
        score_text = font.render(f"Score: {self.score}", True, (255, 255, 255))
        level_text = font.render(f"Level: {self.level}", True, (255, 255, 255))
        lives_text = font.render(f"Lives: {self.player.lives}", True, (255, 255, 255))
        coverage_text = font.render(f"Coverage: {self.grid_manager.captured_area:.1f}%", True, (255, 255, 255))

        self.screen.blit(score_text, (10, 10))
        self.screen.blit(level_text, (self.screen_width // 2 - level_text.get_width() // 2, 10))
        self.screen.blit(lives_text, (self.screen_width - lives_text.get_width() - 10, 10))
        self.screen.blit(coverage_text, (self.screen_width // 2 - coverage_text.get_width() // 2, 40))

    def _game_over_mode(self) -> None:
        """Handle game over mode rendering."""
        self.screen.fill((0, 0, 0))

        # Game Over text
        font_large = pygame.font.Font(None, 74)
        game_over_text = font_large.render("GAME OVER", True, (255, 0, 0))
        self.screen.blit(game_over_text, (self.screen_width // 2 - game_over_text.get_width() // 2, 180))

        # Final score
        font_text = pygame.font.Font(None, 48)
        score_text = font_text.render(f"Final Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (self.screen_width // 2 - score_text.get_width() // 2, 280))

        # Restart prompt
        font_small = pygame.font.Font(None, 36)
        restart_text = font_small.render("Press SPACE to play again", True, (200, 200, 200))
        self.screen.blit(restart_text, (self.screen_width // 2 - restart_text.get_width() // 2, 350))

    def handle_collisions(self) -> None:
        player_pos = self.player.get_position()
        
        for ghost in self.ghosts:
            # 1. Ghost hits Player directly
            if ghost.is_collision(player_pos[0], player_pos[1]):
                self._player_hit()
                return

            # 2. Ghost hits the Player's Trail (value 2 in grid)
            # Check the grid cell the ghost is currently occupying
            gx = int(ghost.x // self.block_size)
            gy = int(ghost.y // self.block_size)
            if self.grid_manager.get_cell(gx, gy) == 2:
                self._player_hit()
                return

    def _player_hit(self):
        lives = self.player.lose_life()
        if lives > 0:
            self.player.set_position(0, 0)
            # Clear current trail so player isn't stuck in a death loop
            self.grid_manager.trail.clear()
            self.grid_manager.start_position = (-1,-1)
            # Clear value 2 (trail) from grid
            for y in range(self.grid_manager.height):
                for x in range(self.grid_manager.width):
                    if self.grid_manager.grid[y][x] == 2:
                        self.grid_manager.grid[y][x] = 0
        else:
            self.update_game_state(GAME_OVER)

    def update_game_state(self, new_state: int) -> None:
        """Control transitions between game states.

        Args:
            new_state: New game state (MENU, PLAY, GAME_OVER)
        """
        self.game_state = new_state