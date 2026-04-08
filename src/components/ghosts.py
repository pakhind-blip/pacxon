import pygame
import random
import math
from core.game_object import GameObject
from core.collision import Collision

class Ghost(GameObject, Collision):
    def __init__(self, x, y, color, block_size, speed=2.0):
        super().__init__(x * block_size, y * block_size, color, speed)
        self.block_size = block_size
        self.width = block_size
        self.height = block_size
        self.dx = random.choice([-1, 1]) * speed
        self.dy = random.choice([-1, 1]) * speed

    def is_collision(self, px: int, py: int) -> bool:
        """Standard AABB collision check."""
        return (self.x < px + self.block_size and
                self.x + self.width > px and
                self.y < py + self.block_size and
                self.y + self.height > py)

    def draw(self, surface):
        pygame.draw.circle(surface, self.color, 
                           (int(self.x + self.width//2), int(self.y + self.height//2)), 
                           self.width//2)

class GhostBouncer(Ghost):
    """Diagonal bouncer that stays in empty space (0) and bounces off walls (1)."""
    def __init__(self, x, y, block_size):
        super().__init__(x, y, (255, 105, 180), block_size, speed=2.5)

    def update(self, grid_manager):
        # Move X and check collision
        self.x += self.dx
        cx = int((self.x + self.width // 2) // self.block_size)
        cy = int((self.y + self.height // 2) // self.block_size)
        
        if grid_manager.get_cell(cx, cy) == 1 or self.x <= 0 or self.x >= (grid_manager.width - 1) * self.block_size:
            self.dx *= -1
            self.x += self.dx # Step back

        # Move Y and check collision
        self.y += self.dy
        cx = int((self.x + self.width // 2) // self.block_size)
        cy = int((self.y + self.height // 2) // self.block_size)

        if grid_manager.get_cell(cx, cy) == 1 or self.y <= 0 or self.y >= (grid_manager.height - 1) * self.block_size:
            self.dy *= -1
            self.y += self.dy # Step back


class GhostClimber(Ghost):
    def __init__(self, x, y, block_size):
        super().__init__(x, y, (0, 255, 255), block_size, speed=2.0)
        self.target_x, self.target_y = self.x, self.y
        self.grid_x, self.grid_y = x, y
        self.current_dir = (1, 0) 

    def update(self, grid_manager):
        if abs(self.x - self.target_x) < self.speed and abs(self.y - self.target_y) < self.speed:
            self.x, self.y = self.target_x, self.target_y
            self._choose_next_node(grid_manager)
        
        if self.x < self.target_x: self.x += self.speed
        elif self.x > self.target_x: self.x -= self.speed
        if self.y < self.target_y: self.y += self.speed
        elif self.y > self.target_y: self.y -= self.speed

    def _choose_next_node(self, grid_manager):
        gx, gy = int(self.grid_x), int(self.grid_y)
        dx, dy = self.current_dir
        
        cx, cy = grid_manager.width // 2, grid_manager.height // 2
        
        # Directions: Right turn, Left turn, and Straight
        # We EXCLUDE the backwards direction (-dx, -dy)
        potential_moves = [(dy, -dx), (-dy, dx), (dx, dy)]
        
        valid_options = []

        for move in potential_moves:
            nx, ny = gx + move[0], gy + move[1]
            if 0 <= nx < grid_manager.width and 0 <= ny < grid_manager.height:
                if grid_manager.get_cell(nx, ny) == 1:
                    # Calculate how "inside" this block is
                    dist = math.hypot(nx - cx, ny - cy)
                    valid_options.append((move, dist))

        if valid_options:
            # Sort by distance to center: The block closest to the middle wins!
            # This makes it DIVE into your new lines the moment it hits a junction.
            valid_options.sort(key=lambda x: x[1])
            self.current_dir = valid_options[0][0]
        else:
            # Only if trapped, go back
            self.current_dir = (-dx, -dy)

        self.grid_x += self.current_dir[0]
        self.grid_y += self.current_dir[1]
        self.target_x = self.grid_x * self.block_size
        self.target_y = self.grid_y * self.block_size