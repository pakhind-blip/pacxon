import pygame
from core.game_object import GameObject
from core.collision import Collision

LEFT, RIGHT, UP, DOWN = 0, 1, 2, 3

class Player(GameObject, Collision):
    def __init__(self, width: int = 20, height: int = 20, block_size: int = 20, move_delay: int = 8,iframe_color=(255, 0, 0)):
        super().__init__(x=0.0, y=0.0, color=(255, 255, 0), speed=1.0)
        self.width = width
        self.height = height
        self.block_size = block_size
        self.grid_x = 0
        self.grid_y = 0
        self.target_x = 0.0
        self.target_y = 0.0
        self.direction = RIGHT
        self.move_delay = move_delay
        self.move_timer = 0
        self.lerp_speed = 0.6 
        self.lives = 3
        self.is_trailing = False
        self.is_iframe = False
        self.iframe_time = 60
        self.iframe_color = iframe_color

    def is_collision(self, x: int, y: int) -> bool:
        return (self.x < x + self.width and self.x + self.width > x and
                self.y < y + self.height and self.y + self.height > y)

    def handle_input(self, keys) -> bool:
        """
        Processes input. If the player tries to go backward while trailing, 
        is_moving returns False so they stay still.
        """
        new_direction = None
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            new_direction = LEFT
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            new_direction = RIGHT
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            new_direction = UP
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            new_direction = DOWN

        if new_direction is None:
            return False

        # Rule: Cannot move in the exact opposite direction if a trail exists
        if self.is_trailing:
            if (new_direction == LEFT and self.direction == RIGHT) or \
               (new_direction == RIGHT and self.direction == LEFT) or \
               (new_direction == UP and self.direction == DOWN) or \
               (new_direction == DOWN and self.direction == UP):
                return False  # Stay still instead of reversing or continuing forward

        self.direction = new_direction
        return True

    def move(self) -> None:
        if self.direction == LEFT: self.grid_x -= 1
        elif self.direction == RIGHT: self.grid_x += 1
        elif self.direction == UP: self.grid_y -= 1
        elif self.direction == DOWN: self.grid_y += 1
        self.target_x = self.grid_x * self.block_size
        self.target_y = self.grid_y * self.block_size

    def update(self) -> None:
        if self.is_iframe:
            self.iframe_time -= 1
            if self.iframe_time <= 0:
                self.is_iframe = False
        self.x += (self.target_x - self.x) * self.lerp_speed
        self.y += (self.target_y - self.y) * self.lerp_speed

    def move_with_collision(self, keys, scene) -> None:
        is_key_held = self.handle_input(keys)
        self.move_timer += 1
        
        # Only move to the next grid cell if a valid key is held and timer is up
        if self.move_timer >= self.move_delay:
            self.move_timer = 0
            if is_key_held: 
                self.move()
                
        self.update()

    def clamp_to_bounds(self, max_width: int, max_height: int) -> None:
        max_grid_x = (max_width // self.block_size) - 1
        max_grid_y = (max_height // self.block_size) - 1
        self.grid_x = max(0, min(self.grid_x, max_grid_x))
        self.grid_y = max(0, min(self.grid_y, max_grid_y))
        self.target_x = self.grid_x * self.block_size
        self.target_y = self.grid_y * self.block_size

    def draw(self, surface, offset_y: int = 0) -> None:
        if self.is_iframe:
            pygame.draw.rect(surface, self.iframe_color, (self.x, self.y + offset_y, self.width, self.height))
        else:
            pygame.draw.rect(surface, self.color, (self.x, self.y + offset_y, self.width, self.height))

    def set_position(self, x: int, y: int) -> None:
        self.grid_x, self.grid_y = x, y
        self.x, self.y = x * self.block_size, y * self.block_size
        self.target_x, self.target_y = self.x, self.y

    def get_position(self) -> tuple: return (self.x, self.y)
    def get_grid_position(self) -> tuple: return (self.grid_x, self.grid_y)

    def lose_life(self) -> int:
        if self.is_iframe:
            return self.lives

        self.lives -= 1
        self.is_iframe = True
        self.iframe_time = 60  # 3 seconds at 60 FPS
        self.is_trailing = False

        return self.lives