import pygame
import random
import math
from collections import deque
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

    def draw(self, surface, offset_y: int = 0):
            # Render the ghost with the vertical offset
            pygame.draw.circle(surface, self.color,
                            (int(self.x + self.width // 2), 
                                int(self.y + self.height // 2 + offset_y)),
                            self.width // 2)


class GhostBouncer(Ghost):
    """Diagonal bouncer that stays in empty space (0) and bounces off walls (1)."""
    def __init__(self, x, y, block_size):
        super().__init__(x, y, (255, 105, 180), block_size, speed=2.5)

    def update(self, grid_manager):
        self.x += self.dx
        cx = int((self.x + self.width // 2) // self.block_size)
        cy = int((self.y + self.height // 2) // self.block_size)
        if (grid_manager.get_cell(cx, cy) == 1
                # or self.x - self.width <= 0
                # or self.x + self.width >= (grid_manager.width - 1) * self.block_size):
                or self.x  <= 0
                or self.x  >= (grid_manager.width - 1) * self.block_size):
            self.dx *= -1
            self.x += self.dx

        self.y += self.dy
        cx = int((self.x + self.width // 2) // self.block_size)
        cy = int((self.y + self.height // 2) // self.block_size)
        if (grid_manager.get_cell(cx, cy) == 1
                # or self.y - self.height  <= 0
                # or self.y + self.height >= (grid_manager.height - 1) * self.block_size):
                or self.y   <= 0
                or self.y  >= (grid_manager.height - 1) * self.block_size):
            self.dy *= -1
            self.y += self.dy


class GhostClimber(Ghost):
    """
    Moves through open space (cell == 0) and traces the inner edge of walls.
    Uses a right-hand rule: always tries to keep a wall on its right side.
    When the player captures new territory (wall count changes), the ghost
    re-anchors itself to the nearest open cell adjacent to any wall and
    resumes tracing from there.
    """

    def __init__(self, x, y, block_size):
        super().__init__(x, y, (0, 255, 255), block_size, speed=2.0)
        self.target_x = self.x
        self.target_y = self.y
        self.grid_x = x
        self.grid_y = y
        self.current_dir = (1, 0)
        self._last_wall_count = -1
        self.reverse = random.choice([True, False])
        self._history = deque(maxlen=12)

    # ------------------------------------------------------------------ helpers

    def _is_open(self, gx, gy, grid_manager):
        return grid_manager.get_cell(gx, gy) == 0 or grid_manager.get_cell(gx, gy) == 2

    def _has_wall_neighbour(self, gx, gy, grid_manager):
        for ddx, ddy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            if grid_manager.get_cell(gx + ddx, gy + ddy) == 1:
                return True
        return False

    def _count_walls(self, grid_manager):
        return sum(cell == 1 for row in grid_manager.grid for cell in row)

    def _find_nearest_wall_edge(self, grid_manager):
        """BFS from current position to find nearest open cell adjacent to a wall."""
        start = (int(self.grid_x), int(self.grid_y))
        # If already on a wall cell, find nearest open cell first
        if not self._is_open(start[0], start[1], grid_manager):
            for ddx, ddy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx, ny = start[0]+ddx, start[1]+ddy
                if self._is_open(nx, ny, grid_manager):
                    start = (nx, ny)
                    break
            else:
                return None

        visited = {start}
        queue = deque([start])
        while queue:
            cx, cy = queue.popleft()
            if self._has_wall_neighbour(cx, cy, grid_manager):
                return (cx, cy)
            for ddx, ddy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = cx + ddx, cy + ddy
                if (nx, ny) not in visited and self._is_open(nx, ny, grid_manager):
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        return None

    def _anchor_to_wall(self, grid_manager):
        """Teleport to nearest wall-edge cell and pick the best starting direction."""
        dest = self._find_nearest_wall_edge(grid_manager)
        if not dest:
            return
        self.grid_x, self.grid_y = dest
        self.x = self.grid_x * self.block_size
        self.y = self.grid_y * self.block_size
        self.target_x = self.x
        self.target_y = self.y
        self._history.clear()

        # Pick direction: forward must be open, wall must be on the right
        for attempt_dir in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            adx, ady = attempt_dir
            if not self.reverse:
                right_dx, right_dy = -ady, adx          # 90° right of direction
                nx_fwd = self.grid_x + adx
                ny_fwd = self.grid_y + ady
                nx_right = self.grid_x + right_dx
                ny_right = self.grid_y + right_dy
                if (self._is_open(nx_fwd, ny_fwd, grid_manager) and
                    grid_manager.get_cell(nx_right, ny_right) == 1):
                    self.current_dir = attempt_dir
                    return
            else:
                left_dx, left_dy = ady, -adx   # 90° left of direction
                nx_fwd   = self.grid_x + adx
                ny_fwd   = self.grid_y + ady
                nx_left  = self.grid_x + left_dx
                ny_left  = self.grid_y + left_dy
                if (self._is_open(nx_fwd, ny_fwd, grid_manager) and
                    grid_manager.get_cell(nx_left, ny_left) == 1):
                    self.current_dir = attempt_dir
                    return

        # Fallback: any open neighbour
        for attempt_dir in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            adx, ady = attempt_dir
            if self._is_open(self.grid_x + adx, self.grid_y + ady, grid_manager):
                self.current_dir = attempt_dir
                return

    # ------------------------------------------------------------------ update

    def update(self, grid_manager):
        # Re-anchor whenever the player captures new territory
        wall_count = self._count_walls(grid_manager)
        if wall_count != self._last_wall_count:
            self._last_wall_count = wall_count
            self._anchor_to_wall(grid_manager)

        # Smooth pixel movement
        if abs(self.x - self.target_x) < self.speed and abs(self.y - self.target_y) < self.speed:
            self.x, self.y = self.target_x, self.target_y
            self._choose_next_node(grid_manager)

        if self.x < self.target_x:
            self.x += self.speed
        elif self.x > self.target_x:
            self.x -= self.speed
        if self.y < self.target_y:
            self.y += self.speed
        elif self.y > self.target_y:
            self.y -= self.speed

    def _choose_next_node(self, grid_manager):
        gx, gy = int(self.grid_x), int(self.grid_y)
        dx, dy = self.current_dir

        # Right-hand rule in open space — wall stays on the RIGHT.
        # right of (dx,dy) = (-dy, dx)
        # Priority: turn right (into wall gap) → straight → turn left → reverse
        if not self.reverse:
            # RIGHT-hand rule (clockwise)
            priority_moves = [
                (-dy,  dx),   # turn right
                ( dx,  dy),   # straight
                ( dy, -dx),   # turn left
                (-dx, -dy),   # reverse
            ]
        else:
            # LEFT-hand rule (counter-clockwise)
            priority_moves = [
                ( dy, -dx),   # turn left
                ( dx,  dy),   # straight
                (-dy,  dx),   # turn right
                (-dx, -dy),   # reverse
            ]

        recent = set(self._history)
        candidates = []

        for rank, (mdx, mdy) in enumerate(priority_moves):
            nx, ny = gx + mdx, gy + mdy
            if not self._is_open(nx, ny, grid_manager):
                continue
            on_edge = self._has_wall_neighbour(nx, ny, grid_manager)
            in_loop = (nx, ny, (mdx, mdy)) in recent
            # Prefer: lower rank, on-edge cells, non-looping
            candidates.append((rank, not on_edge, in_loop, mdx, mdy))

        if not candidates:
            return  # completely enclosed — stay put

        candidates.sort(key=lambda c: (c[0], c[1], c[2]))
        _, _, _, mdx, mdy = candidates[0]

        self.current_dir = (mdx, mdy)
        self.grid_x += mdx
        self.grid_y += mdy
        self.target_x = self.grid_x * self.block_size
        self.target_y = self.grid_y * self.block_size
        self._history.append((int(self.grid_x), int(self.grid_y), self.current_dir))
