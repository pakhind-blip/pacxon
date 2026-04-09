import pygame
from components.player import Player
from collections import deque
 

class GridManager:
    def __init__(self, width: int, height: int, player: Player,gameEngine , block_size: int = 20):
        self.width = width
        self.height = height
        self.block_size = block_size
        self.grid = self._create_grid()
        self.player = player
        self.captured_area = 0.0
        self.gameEngine = gameEngine
        self.trail = []
        self.start_position = (-1, -1)
        self._apply_border()

    def _create_grid(self) -> list[list[int]]:
        return [[0 for _ in range(self.width)] for _ in range(self.height)]

    def _apply_border(self) -> None:
        for x in range(self.width):
            self.grid[0][x] = 1  # Top border
            self.grid[self.height - 1][x] = 1  # Bottom border
        for y in range(self.height):
            self.grid[y][0] = 1  # Left border
            self.grid[y][self.width - 1] = 1  # Right border

    def get_grid(self) -> list[list[int]]:
        return self.grid

    def set_cell(self, x: int, y: int, value: int) -> None:
        if value in (0, 1) and 0 < x < self.width - 1 and 0 < y < self.height - 1:
            self.grid[y][x] = value

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
                self.start_position = (grid_x, grid_y)
                self.player.is_trailing  = True
            self.trail.append((grid_x, grid_y))
        elif self.grid[grid_y][grid_x] == 1 and self.start_position != (-1, -1):
            end_position = (grid_x, grid_y)
            self.player.is_trailing  = False
            self.flood_fill(end_position[0], end_position[1])

        self.calculate_coverage()

    def flood_fill(self, end_x: int, end_y: int) -> None:
        rows = len(self.grid)
        cols = len(self.grid[0])

        start_x, start_y = self.start_position

        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        queue = deque()
        queue.append((end_x, end_y, []))

        visited = set()
        visited.add((end_x, end_y))
        trail_without_start = self.trail.copy()
        trail_without_start.remove(self.start_position)

        # shortest path to find border of shape 
        # it will find shortest path of startmove and endmove without trail
        shortest_path = []
        while queue:
            x, y, path = queue.popleft()

            if x == start_x and y == start_y:
                shortest_path = path + [(x, y)]
                break

            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if (0 <= nx < cols and 0 <= ny < rows and
                    (nx, ny) not in visited and
                    self.grid[ny][nx] != 0 and (nx, ny) not in trail_without_start):
                    visited.add((nx, ny))
                    queue.append((nx, ny, path + [(x, y)]))

        for x, y in self.trail:
            self.grid[y][x] = 1

        border = self.trail + shortest_path
        border_set = set(border)

        # draw oustide and reverse to inside
        min_x = min(x for x, y in border)
        max_x = max(x for x, y in border)
        min_y = min(y for x, y in border)
        max_y = max(y for x, y in border)

        outside_queue = []
        for x in range(min_x - 1, max_x + 1):
            outside_queue.append((x, min_y - 1))
            outside_queue.append((x, max_y + 1))
        for y in range(min_y - 1, max_y + 1):
            outside_queue.append((min_x - 1, y))
            outside_queue.append((max_x + 1, y))

        visited_outside = set(outside_queue)

        while outside_queue:
            curr_x, curr_y = outside_queue.pop(0)
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = curr_x + dx, curr_y + dy
                if (min_x - 1 <= nx <= max_x + 1 and
                    min_y - 1 <= ny <= max_y + 1 and
                    (nx, ny) not in border_set and
                    (nx, ny) not in visited_outside):
                    visited_outside.add((nx, ny))
                    outside_queue.append((nx, ny))

        can_ghost_lock_grid = set()

        ghosts = self.gameEngine.ghosts
        def bfs_from_ghost( start_x, start_y, visited_outside, border_set):
            queue = deque()
            visited = set()

            queue.append((start_x, start_y))
            visited.add((start_x, start_y))

            directions = [(1,0), (-1,0), (0,1), (0,-1)]

            while queue:
                x, y = queue.popleft()

                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if (nx, ny) not in visited:
                        if 0 <= nx < len(self.grid[0]) and 0 <= ny < len(self.grid):

                            # ❗ only move inside candidate area
                            if (nx, ny) not in visited_outside and (nx, ny) not in border_set and self.get_grid()[ny][nx] == 0:
                                visited.add((nx, ny))
                                queue.append((nx, ny))

            return visited
        for g in ghosts:
            gx = int(g.x // self.block_size)
            gy = int(g.y // self.block_size)

            # ghost must be inside candidate area
            if (gx, gy) not in visited_outside and (gx, gy) not in border_set:
                
                reachable = bfs_from_ghost(gx, gy, visited_outside, border_set)
                can_ghost_lock_grid.update(reachable)
        
        
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                # for all ghost if in that gird dont change anything include alreay change grid draw only traillin 
                if (x, y) not in visited_outside and (x, y) not in border_set and (x,y) not in can_ghost_lock_grid:                    
                    self.grid[y][x] = 1

        self.start_position = (-1, -1)
        self.trail.clear()

    def calculate_coverage(self) -> float:
        total_cells = self.width * self.height
        captured_cells = 0

        for row in self.grid:
            for cell in row:
                if cell == 1:
                    captured_cells += 1

        self.captured_area = (captured_cells / total_cells) * 100.0
        return self.captured_area

    def check_collision(self, x: int, y: int) -> bool:
        grid_x = x // self.block_size
        grid_y = y // self.block_size
        return self.get_cell(grid_x, grid_y) == 1

    def check_rect_collision(self, x: int, y: int, width: int, height: int) -> bool:
        corners = [
            (x, y),
            (x + width - 1, y),
            (x, y + height - 1),
            (x + width - 1, y + height - 1)
        ]
        for cx, cy in corners:
            if self.check_collision(cx, cy):
                return True
        return False

    def reset(self) -> None:
        self.grid = self._create_grid()
        self.captured_area = 0.0
        self.trail = []
        self.start_position = (-1, -1)
        self._apply_border()

    def draw(self, surface, color: tuple = (100, 100, 100)) -> None:
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                rect = pygame.Rect(
                    x * self.block_size,
                    y * self.block_size,
                    self.block_size,
                    self.block_size
                )
                if cell == 1:
                    pygame.draw.rect(surface, color, rect)
                    pygame.draw.rect(surface, (255, 255, 255), rect, 1)
                elif cell == 0:
                    pygame.draw.rect(surface, (255, 255, 255), rect, 1)
                elif cell == 2:
                    pygame.draw.rect(surface, (0, 255, 0), rect)
                    pygame.draw.rect(surface, (255, 255, 255), rect, 1)