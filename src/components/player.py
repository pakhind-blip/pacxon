import pygame
from core.game_object import GameObject
from core.collision import Collision


# Direction constants
LEFT = 0
RIGHT = 1
UP = 2
DOWN = 3


class Player(GameObject, Collision):
    """Player class that extends GameObject and implements Collision interface.

    Moves automatically in one direction. Arrow keys change direction.
    Moves block by block (grid-based movement).
    """

    def __init__(self, width: int = 20, height: int = 20, block_size: int = 20, move_delay: int = 10):
        """Initialize player.

        Args:
            width: Player width in pixels (default: 20)
            height: Player height in pixels (default: 20)
            block_size: Size of each block in pixels (default: 20)
            move_delay: Frames between moves (default: 10, higher = slower)
        """
        GameObject.__init__(self, x=0.0, y=0.0, color=(255, 0, 0), speed=1.0)
        self.width = width
        self.height = height
        self.block_size = block_size
        self.grid_x = 0  # Grid position (column)
        self.grid_y = 0  # Grid position (row)
        self.target_x = 0.0  # Target pixel position
        self.target_y = 0.0  # Target pixel position
        self.direction = LEFT  # Start moving left
        self.move_delay = move_delay
        self.move_timer = 0
        self.lerp_speed = 0.5  # LERP speed (0.0 to 1.0, higher = faster)

    def is_collision(self, x: int, y: int) -> bool:
        """Check if position collides with player.

        Args:
            x: X position to check
            y: Y position to check

        Returns:
            True if position is within player bounds
        """
        return (self.x <= x < self.x + self.width and
                self.y <= y < self.y + self.height)

    def handle_input(self, keys) -> None:
        """Change direction based on keyboard input.

        Args:
            keys: Pygame key state from pygame.key.get_pressed()
        """
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.direction = LEFT
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.direction = RIGHT
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            self.direction = UP
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.direction = DOWN

    def move(self) -> None:
        """Move player one block in current direction."""
        if self.direction == LEFT:
            self.grid_x -= 1
        elif self.direction == RIGHT:
            self.grid_x += 1
        elif self.direction == UP:
            self.grid_y -= 1
        elif self.direction == DOWN:
            self.grid_y += 1

        # Update target position for smooth movement
        self.target_x = self.grid_x * self.block_size
        self.target_y = self.grid_y * self.block_size

    def update(self) -> None:
        """Update player position using LERP for smooth movement."""
        self.x += (self.target_x - self.x) * self.lerp_speed
        self.y += (self.target_y - self.y) * self.lerp_speed

    def move_with_collision(self, keys, scene) -> None:
        """Handle movement - ignores scene walls, for ghost collision later.

        Args:
            keys: Pygame key state from pygame.key.get_pressed()
            scene: Scenes object (collision with walls ignored for player)
        """
        # Change direction based on input
        self.handle_input(keys)

        # Increment timer
        self.move_timer += 1

        # Only move when timer reaches delay
        if self.move_timer >= self.move_delay:
            self.move_timer = 0
            self.move()

        # Smooth movement update
        self.update()

    def clamp_to_bounds(self, max_width: int, max_height: int) -> None:
        """Keep player within screen bounds.

        Args:
            max_width: Maximum width (screen width)
            max_height: Maximum height (screen height)
        """
        max_grid_x = (max_width // self.block_size) - 1
        max_grid_y = (max_height // self.block_size) - 1

        self.grid_x = max(0, min(self.grid_x, max_grid_x))
        self.grid_y = max(0, min(self.grid_y, max_grid_y))

        # Update target position
        self.target_x = self.grid_x * self.block_size
        self.target_y = self.grid_y * self.block_size

    def draw(self, surface) -> None:
        """Draw the player on the given surface.

        Args:
            surface: Pygame surface to draw on
        """
        rect = (self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)

    def set_position(self, x: int, y: int) -> None:
        """Set player position in grid coordinates.

        Args:
            x: Grid X position (column)
            y: Grid Y position (row)
        """
        self.grid_x = x
        self.grid_y = y
        self.x = x * self.block_size
        self.y = y * self.block_size

    def get_position(self) -> tuple[int, int]:
        """Get current player position in pixels.

        Returns:
            Tuple of (x, y) pixel position
        """
        return (self.x, self.y)

    def get_grid_position(self) -> tuple[int, int]:
        """Get current player position in grid coordinates.

        Returns:
            Tuple of (grid_x, grid_y) grid position
        """
        return (self.grid_x, self.grid_y)

    def get_direction(self) -> int:
        """Get current direction.

        Returns:
            Direction constant (LEFT, RIGHT, UP, DOWN)
        """
        return self.direction