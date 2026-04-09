import pygame
from collections import deque

class GridManager:
    def __init__(self, width: int, height: int, player, gameEngine, block_size: int = 20):
        self.width = width
        self.height = height
        self.block_size = block_size
        self.grid = self._create_grid()
        self.player = player
        self.captured_area = 0.0
        self.gameEngine = gameEngine
        self.trail = []
        self.start_position = (-1, -1)
        self.before_postition = (0,0)
        self._apply_border()

    def _create_grid(self) -> list[list[int]]:
        return [[0 for _ in range(self.width)] for _ in range(self.height)]

    def _apply_border(self) -> None:
        for x in range(self.width):
            self.grid[0][x] = 1
            self.grid[self.height - 1][x] = 1
        for y in range(self.height):
            self.grid[y][0] = 1
            self.grid[y][self.width - 1] = 1

    def get_cell(self, x: int, y: int) -> int:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return 1

    def update_grid(self) -> None:
        grid_x, grid_y = self.player.get_grid_position()
        if self.player.is_trailing and (grid_x, grid_y) in self.trail[:-1]:
            self.gameEngine._player_hit()
            return
        if self.grid[grid_y][grid_x] == 0:
            self.grid[grid_y][grid_x] = 2
            if self.start_position == (-1, -1):
                self.start_position = self.before_postition 
                self.player.is_trailing = True
                
            self.trail.append((grid_x, grid_y))
        elif self.grid[grid_y][grid_x] == 1 :
            if self.start_position != (-1, -1) :
                end_position = (grid_x, grid_y)
                self.player.is_trailing = False
                self.flood_fill(end_position[0], end_position[1])
            else:
                self.before_postition = (grid_x, grid_y)
        self.calculate_coverage()

    def flood_fill(self, end_x: int, end_y: int) -> None:
        rows = self.height
        cols = self.width
        start_x, start_y = self.start_position
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        queue = deque([(end_x, end_y, [])])
        visited = {(end_x, end_y)}
        # trail_without_start = [p for p in self.trail if p != self.start_position]
        # (x,y) start - all direct
        

        shortest_path = []
        while queue:
            x, y, path = queue.popleft()
            if x == start_x and y == start_y:
                shortest_path = path + [(x, y)]
                break
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if (0 <= nx < cols and 0 <= ny < rows and (nx, ny) not in visited and
                        self.grid[ny][nx] != 0 and (nx, ny) not in self.trail):
                    visited.add((nx, ny))
                    queue.append((nx, ny, path + [(x, y)]))

        border_set = set(self.trail + shortest_path)
        min_x = max(0, min(x for x, y in border_set) - 1)
        max_x = min(cols - 1, max(x for x, y in border_set) + 1)
        min_y = max(0, min(y for x, y in border_set) - 1)
        max_y = min(rows - 1, max(y for x, y in border_set) + 1)

        outside_queue = deque()
        for x in range(min_x, max_x + 1):
            outside_queue.append((x, min_y))
            outside_queue.append((x, max_y))
        for y in range(min_y, max_y + 1):
            outside_queue.append((min_x, y))
            outside_queue.append((max_x, y))

        visited_outside = set()
        actual_outside = set()
        while outside_queue:
            cx, cy = outside_queue.popleft()
            if (cx, cy) in visited_outside or (cx, cy) in border_set:
                continue
            visited_outside.add((cx, cy))
            if self.grid[cy][cx] == 0:
                actual_outside.add((cx, cy))
                for dx, dy in directions:
                    nx, ny = cx + dx, cy + dy
                    if min_x <= nx <= max_x and min_y <= ny <= max_y:
                        outside_queue.append((nx, ny))

        ghost_protected = set()
        for g in self.gameEngine.ghosts:
            gx, gy = int(g.x // self.block_size), int(g.y // self.block_size)
            if (gx, gy) not in border_set and self.get_cell(gx, gy) == 0:
                q = deque([(gx, gy)])
                v = {(gx, gy)}
                while q:
                    cx, cy = q.popleft()
                    ghost_protected.add((cx, cy))
                    for dx, dy in directions:
                        nx, ny = cx + dx, cy + dy
                        if (0 <= nx < cols and 0 <= ny < rows and (nx, ny) not in v and 
                            (nx, ny) not in border_set and self.grid[ny][nx] == 0):
                            v.add((nx, ny))
                            q.append((nx, ny))

        newly_captured_count = 0
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                is_internal = (x, y) not in actual_outside and (x, y) not in ghost_protected
                if (self.grid[y][x] == 2) or (self.grid[y][x] == 0 and is_internal):
                    self.grid[y][x] = 1
                    newly_captured_count += 1

        # Updated: Add 1 point per new block captured
        if newly_captured_count > 0:
            self.gameEngine.score += (newly_captured_count * 1)

        self.start_position = (-1, -1)
        self.trail.clear()

    def calculate_coverage(self) -> float:
        total_cells = self.width * self.height
        initial_border_count = (self.width * 2) + (self.height * 2) - 4
        playable_area_size = total_cells - initial_border_count
        captured_cells = sum(row.count(1) for row in self.grid)
        actual_captured = max(0, captured_cells - initial_border_count)
        self.captured_area = (actual_captured / playable_area_size) * 100.0 if playable_area_size > 0 else 0.0
        return self.captured_area

    def reset(self) -> None:
        self.grid = self._create_grid()
        self.captured_area = 0.0
        self.trail = []
        self.start_position = (-1, -1)
        self._apply_border()

    def draw(self, surface, color: tuple = (100, 100, 100), offset_y: int = 0) -> None:
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                rect = pygame.Rect(x * self.block_size, y * self.block_size + offset_y, self.block_size, self.block_size)
                if cell == 1:
                    pygame.draw.rect(surface, color, rect)
                    pygame.draw.rect(surface, (60, 60, 60), rect, 1)
                elif cell == 2:
                    pygame.draw.rect(surface, (0, 255, 0), rect)
                else:
                    pygame.draw.rect(surface, (30, 30, 30), rect, 1)