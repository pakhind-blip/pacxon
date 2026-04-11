import pygame
from core.game_object import GameObject
from core.collision import Collision

LEFT, RIGHT, UP, DOWN = 0, 1, 2, 3

class Player(GameObject, Collision):
    def __init__(self, width: int = 20, height: int = 20, block_size: int = 20, move_delay: int = 4, iframe_color=(255, 0, 0)):
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
        self.lerp_speed = 0.4
        self.lives = 3
        self.is_trailing = False
        
        # iframe settings
        self.is_iframe = False
        self.iframe_duration = 180  # 3 seconds at 60 FPS
        self.iframe_timer = 0
        self.blink_speed = 10 

    def is_collision(self, x: int, y: int) -> bool:
        return self.x < x + self.width and self.x + self.width > x and \
               self.y < y + self.height and self.y + self.height > y

    def get_grid_position(self) -> tuple:
        return self.grid_x, self.grid_y

    def move_with_collision(self, keys, grid_manager) -> None:
        if self.is_iframe:
            self.iframe_timer -= 1
            if self.iframe_timer <= 0:
                self.is_iframe = False

        if self.move_timer > 0:
            self.move_timer -= 1
        else:
            dx, dy = 0, 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx, self.direction = -1, LEFT
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx, self.direction = 1, RIGHT
            elif keys[pygame.K_UP] or keys[pygame.K_w]: dy, self.direction = -1, UP
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]: dy, self.direction = 1, DOWN

            if dx != 0 or dy != 0:
                new_grid_x = self.grid_x + dx
                new_grid_y = self.grid_y + dy
                
                # Immediate iframe loss if we start a trail
                if grid_manager.get_cell(new_grid_x, new_grid_y) == 0:
                    self.is_iframe = False
                    self.iframe_timer = 0

                if 0 <= new_grid_x < grid_manager.width and 0 <= new_grid_y < grid_manager.height:
                    self.grid_x, self.grid_y = new_grid_x, new_grid_y
                    self.target_x = self.grid_x * self.block_size
                    self.target_y = self.grid_y * self.block_size
                    self.move_timer = self.move_delay

        self.x += (self.target_x - self.x) * self.lerp_speed
        self.y += (self.target_y - self.y) * self.lerp_speed

    def lose_life(self) -> int:
        self.lives -= 1
        if self.lives > 0:
            self.is_iframe = True
            self.iframe_timer = self.iframe_duration
        return self.lives

    def clamp_to_bounds(self, screen_width: int, screen_height: int) -> None:
        self.x = max(0, min(self.x, screen_width - self.width))
        self.y = max(0, min(self.y, screen_height - self.height))

    def update(self) -> None: pass

    def draw(self, surface, offset_y: int = 0) -> None:
        if self.is_iframe:
            if (self.iframe_timer // self.blink_speed) % 2 == 0:
                temp_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                pygame.draw.rect(temp_surf, (*self.color, 128), (0, 0, self.width, self.height))
                surface.blit(temp_surf, (self.x, self.y + offset_y))
        else:
            pygame.draw.rect(surface, self.color, (self.x, self.y + offset_y, self.width, self.height))

    def set_position(self, x: int, y: int) -> None:
        self.grid_x, self.grid_y = x, y
        self.x, self.y = x * self.block_size, y * self.block_size
        self.target_x, self.target_y = self.x, self.y

    def get_position(self) -> tuple: return (self.x, self.y)