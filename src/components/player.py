import pygame
from core.game_object import GameObject
from core.collision import Collision


# Direction constants
LEFT = 0
RIGHT = 1
UP = 2
DOWN = 3


class Player(GameObject, Collision):

    def __init__(self, width: int = 20, height: int = 20, block_size: int = 20, move_delay: int = 10):
        GameObject.__init__(self, x=0.0, y=0.0, color=(255, 0, 0), speed=1.0)
        self.width = width
        self.height = height
        self.block_size = block_size
        self.grid_x = 0  # Grid position (column)
        self.grid_y = 0  # Grid position (row)
        self.target_x = 0.0  # Target pixel position
        self.target_y = 0.0  # Target pixel position
        self.direction = LEFT  # Movement direction
        self.move_delay = move_delay
        self.move_timer = 0
        self.lerp_speed = 0.5  # LERP speed (0.0 to 1.0, higher = faster)
        self.lives = 3  # Number of remaining lives
        self.is_trailing = False  # Indicates if player is creating a trail
        self.trail_positions = []  # List of grid positions forming the trail

    def is_collision(self, x: int, y: int) -> bool:
        return (self.x <= x < self.x + self.width and
                self.y <= y < self.y + self.height)

    def handle_input(self, keys) -> None:
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.direction = LEFT
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.direction = RIGHT
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            self.direction = UP
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.direction = DOWN

    def move(self) -> None:
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
        max_grid_x = (max_width // self.block_size) - 1
        max_grid_y = (max_height // self.block_size) - 1

        self.grid_x = max(0, min(self.grid_x, max_grid_x))
        self.grid_y = max(0, min(self.grid_y, max_grid_y))

        # Update target position
        self.target_x = self.grid_x * self.block_size
        self.target_y = self.grid_y * self.block_size

    def draw(self, surface) -> None:
        rect = (self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, self.color, rect)

    def set_position(self, x: int, y: int) -> None:
        self.grid_x = x
        self.grid_y = y
        self.x = x * self.block_size
        self.y = y * self.block_size

    def get_position(self) -> tuple[int, int]:
        return (self.x, self.y)

    def get_grid_position(self) -> tuple[int, int]:
        return (self.grid_x, self.grid_y)

    def get_direction(self) -> int:
        return self.direction

    def start_trail(self) -> None:
        self.is_trailing = True
        self.trail_positions = [(self.grid_x, self.grid_y)]

    def close_trail(self) -> list[tuple[int, int]]:
        self.is_trailing = False
        positions = self.trail_positions.copy()
        self.trail_positions = []
        return positions

    def lose_life(self) -> int:
        self.lives -= 1
        return self.lives