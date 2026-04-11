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
        self._tick = random.randint(0, 100)

    def is_collision(self, px: int, py: int) -> bool:
        return (self.x < px + self.block_size and
                self.x + self.width > px and
                self.y < py + self.block_size and
                self.y + self.height > py)

    def draw(self, surface, offset_y: int = 0):
        self._tick += 1
        cx = int(self.x + self.width // 2)
        cy = int(self.y + self.height // 2 + offset_y)
        r = self.width // 2

        # Pulsing outer glow
        pulse = 0.7 + 0.3 * math.sin(self._tick * 0.12)
        glow_r = int(r * 1.8 * pulse)
        glow_surf = pygame.Surface((glow_r * 2 + 4, glow_r * 2 + 4), pygame.SRCALPHA)
        glow_alpha = int(60 * pulse)
        pygame.draw.circle(glow_surf, (*self.color, glow_alpha),
                           (glow_r + 2, glow_r + 2), glow_r)
        surface.blit(glow_surf, (cx - glow_r - 2, cy - glow_r - 2))

        # Main body circle
        pygame.draw.circle(surface, self.color, (cx, cy), r)

        # Inner highlight
        highlight_color = tuple(min(255, c + 80) for c in self.color)
        pygame.draw.circle(surface, highlight_color, (cx - r // 4, cy - r // 4), r // 4)

        # Eyes
        eye_white = (230, 240, 255)
        eye_pupil = (10, 10, 30)
        for ex_off, ey_off in [(-r // 3, -r // 5), (r // 3, -r // 5)]:
            pygame.draw.circle(surface, eye_white, (cx + ex_off, cy + ey_off), r // 5)
            pygame.draw.circle(surface, eye_pupil, (cx + ex_off + 1, cy + ey_off + 1), r // 9)


class GhostBouncer(Ghost):
    """
    Bounces at a random 360-degree angle. Checks all four corners per axis
    so it never clips through walls or captured territory.
    """
    def __init__(self, x, y, block_size):
        super().__init__(x, y, (255, 80, 160), block_size, speed=4.5)
        angle = random.uniform(0, 2 * math.pi)
        self.dx = math.cos(angle) * self.speed
        self.dy = math.sin(angle) * self.speed

    def _hits_wall(self, px, py, grid_manager):
        bs = self.block_size
        m = 1
        corners = [
            (int((px + m) // bs),              int((py + m) // bs)),
            (int((px + self.width - m) // bs), int((py + m) // bs)),
            (int((px + m) // bs),              int((py + self.height - m) // bs)),
            (int((px + self.width - m) // bs), int((py + self.height - m) // bs)),
        ]
        return any(grid_manager.get_cell(cx, cy) == 1 for cx, cy in corners)

    def update(self, grid_manager):
        new_x = self.x + self.dx
        if self._hits_wall(new_x, self.y, grid_manager):
            self.dx *= -1
            new_x = self.x + self.dx
            if self._hits_wall(new_x, self.y, grid_manager):
                new_x = self.x
        self.x = new_x

        new_y = self.y + self.dy
        if self._hits_wall(self.x, new_y, grid_manager):
            self.dy *= -1
            new_y = self.y + self.dy
            if self._hits_wall(self.x, new_y, grid_manager):
                new_y = self.y
        self.y = new_y


class GhostClimber(Ghost):
    """
    Traces the inner edge of walls using a hand-rule:
      clockwise=True  → right-hand rule (turns right first) — clockwise orbit
      clockwise=False → left-hand rule  (turns left first)  — counter-clockwise orbit

    When the player captures new territory the ghost re-anchors itself to
    the nearest open cell adjacent to any wall and resumes tracing.
    """

    def __init__(self, x, y, block_size, clockwise: bool = True):
        color = (0, 220, 255) if clockwise else (255, 160, 20)
        super().__init__(x, y, color, block_size, speed=3.5)
        self.clockwise = clockwise
        self.target_x = self.x
        self.target_y = self.y
        self.grid_x = x
        self.grid_y = y
        self.current_dir = (1, 0)
        self._last_wall_count = -1
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
        if not self._is_open(start[0], start[1], grid_manager):
            for ddx, ddy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = start[0] + ddx, start[1] + ddy
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

        for attempt_dir in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            adx, ady = attempt_dir
            if self.clockwise:
                side_dx, side_dy = -ady, adx
            else:
                side_dx, side_dy = ady, -adx

            nx_fwd   = self.grid_x + adx
            ny_fwd   = self.grid_y + ady
            nx_side  = self.grid_x + side_dx
            ny_side  = self.grid_y + side_dy
            if (self._is_open(nx_fwd, ny_fwd, grid_manager) and
                    grid_manager.get_cell(nx_side, ny_side) == 1):
                self.current_dir = attempt_dir
                return

        for attempt_dir in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
            adx, ady = attempt_dir
            if self._is_open(self.grid_x + adx, self.grid_y + ady, grid_manager):
                self.current_dir = attempt_dir
                return

    # ------------------------------------------------------------------ update

    def update(self, grid_manager):
        wall_count = self._count_walls(grid_manager)
        if wall_count != self._last_wall_count:
            self._last_wall_count = wall_count
            self._anchor_to_wall(grid_manager)

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

        if self.clockwise:
            priority_moves = [
                (-dy,  dx),
                ( dx,  dy),
                ( dy, -dx),
                (-dx, -dy),
            ]
        else:
            priority_moves = [
                ( dy, -dx),
                ( dx,  dy),
                (-dy,  dx),
                (-dx, -dy),
            ]

        recent = set(self._history)
        candidates = []

        for rank, (mdx, mdy) in enumerate(priority_moves):
            nx, ny = gx + mdx, gy + mdy
            if not self._is_open(nx, ny, grid_manager):
                continue
            on_edge = self._has_wall_neighbour(nx, ny, grid_manager)
            in_loop = (nx, ny, (mdx, mdy)) in recent
            candidates.append((rank, not on_edge, in_loop, mdx, mdy))

        if not candidates:
            return

        candidates.sort(key=lambda c: (c[0], c[1], c[2]))
        _, _, _, mdx, mdy = candidates[0]

        self.current_dir = (mdx, mdy)
        self.grid_x += mdx
        self.grid_y += mdy
        self.target_x = self.grid_x * self.block_size
        self.target_y = self.grid_y * self.block_size
        self._history.append((int(self.grid_x), int(self.grid_y), self.current_dir))


class GhostClimberCW(GhostClimber):
    """Clockwise wall-hugger — cyan."""
    def __init__(self, x, y, block_size):
        super().__init__(x, y, block_size, clockwise=True)


class GhostClimberCCW(GhostClimber):
    """Counter-clockwise wall-hugger — orange."""
    def __init__(self, x, y, block_size):
        super().__init__(x, y, block_size, clockwise=False)
