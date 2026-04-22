import pygame
from collections import deque

class GridManager:
    def __init__(self, width: int, height: int, player, gameEngine, block_size: int = 20):
        self.width, self.height, self.block_size = width, height, block_size
        self.grid = self._create_grid()
        self.player, self.gameEngine = player, gameEngine
        self.captured_area = 0.0
        self.trail = []
        self.start_position = (-1, -1)
        self.before_position = (0, 0)
        self._tick = 0
        self._last_trail_cell = (-1, -1)
        self._apply_border()

    def _create_grid(self) -> list:
        return [[0 for _ in range(self.width)] for _ in range(self.height)]

    def _apply_border(self) -> None:
        for x in range(self.width):
            self.grid[0][x] = self.grid[self.height-1][x] = 1
        for y in range(self.height):
            self.grid[y][0] = self.grid[y][self.width-1] = 1

    def get_cell(self, x, y):
        return self.grid[y][x] if 0 <= x < self.width and 0 <= y < self.height else 1

    def update_grid(self) -> None:
        self._tick += 1
        gx, gy = self.player.get_grid_position()

        trail_body = set(self.trail[:-1]) if self.trail else set()
        if self.player.is_trailing and (gx, gy) in trail_body:
            self.gameEngine._player_hit()
            return

        if self.grid[gy][gx] == 0:
            self.grid[gy][gx] = 2
            if hasattr(self.gameEngine, 'sfx') and (gx, gy) != self._last_trail_cell:
                self.gameEngine.sfx.play_trail()
                self._last_trail_cell = (gx, gy)
            if self.start_position == (-1, -1):
                self.start_position = self.before_position
                self.player.is_trailing = True
            self.trail.append((gx, gy))
        elif self.grid[gy][gx] == 1:
            if self.start_position != (-1, -1):
                self.player.is_trailing = False
                self.flood_fill(gx, gy)
            else:
                self.before_position = (gx, gy)
        self.calculate_coverage()

    def flood_fill(self, end_x, end_y):
        rows, cols = self.height, self.width
        start_x, start_y = self.start_position
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        parent = {(end_x, end_y): None}
        queue = deque([(end_x, end_y)])
        found = False
        while queue:
            x, y = queue.popleft()
            if x == start_x and y == start_y:
                found = True
                break
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if (0 <= nx < cols and 0 <= ny < rows
                        and (nx, ny) not in parent
                        and self.grid[ny][nx] == 1
                        and (nx, ny) not in self.trail):
                    parent[(nx, ny)] = (x, y)
                    queue.append((nx, ny))

        shortest_path = []
        if found:
            node = (start_x, start_y)
            while node is not None:
                shortest_path.append(node)
                node = parent[node]

        if not shortest_path:
            self.start_position = (-1, -1)
            self.trail.clear()
            self._last_trail_cell = (-1, -1)
            return

        border_set = set(self.trail + shortest_path)

        o_q = deque()
        for x in range(cols):
            o_q.append((x, 0))
            o_q.append((x, rows - 1))
        for y in range(rows):
            o_q.append((0, y))
            o_q.append((cols - 1, y))

        v_o, a_o = set(), set()
        while o_q:
            cx, cy = o_q.popleft()
            if (cx, cy) in v_o or (cx, cy) in border_set:
                continue
            v_o.add((cx, cy))
            if self.grid[cy][cx] in (0, 2):
                a_o.add((cx, cy))
                for dx, dy in dirs:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < cols and 0 <= ny < rows:
                        o_q.append((nx, ny))

        g_p = set()
        for g in self.gameEngine.ghosts:
            if getattr(g, 'is_insider', False):
                continue
            ghost_gx = int((g.x + self.block_size / 2) // self.block_size)
            ghost_gy = int((g.y + self.block_size / 2) // self.block_size)
            if (ghost_gx, ghost_gy) not in border_set and self.get_cell(ghost_gx, ghost_gy) in (0, 2):
                q, v = deque([(ghost_gx, ghost_gy)]), {(ghost_gx, ghost_gy)}
                while q:
                    cx, cy = q.popleft()
                    g_p.add((cx, cy))
                    for dx, dy in dirs:
                        nx, ny = cx + dx, cy + dy
                        if (0 <= nx < cols and 0 <= ny < rows
                                and (nx, ny) not in v
                                and (nx, ny) not in border_set
                                and self.grid[ny][nx] in (0, 2)):
                            v.add((nx, ny))
                            q.append((nx, ny))

        new_cnt = 0
        for y in range(rows):
            for x in range(cols):
                if self.grid[y][x] == 2 or (self.grid[y][x] == 0
                                             and (x, y) not in a_o
                                             and (x, y) not in g_p):
                    self.grid[y][x] = 1
                    new_cnt += 1

        if new_cnt > 0:
            self.gameEngine.score += new_cnt
            if hasattr(self.gameEngine, 'sfx'):
                self.gameEngine.sfx.play_capture()
            px, py = self.player.get_position()
            if hasattr(self.gameEngine, 'add_score_pop'):
                self.gameEngine.add_score_pop(int(px), int(py), new_cnt)

        # ── Stats: trail successfully closed ────────────────────────────────
        stats = getattr(self.player, 'stats', None)
        if stats is not None:
            total = self.width * self.height
            border = (self.width * 2) + (self.height * 2) - 4
            playable = max(1, total - border)
            per_trail_pct = round((new_cnt / playable) * 100.0, 2)
            stats.on_trail_close(
                level        = self.gameEngine.level,
                capture_pct  = per_trail_pct,   # % captured THIS trail only
                player_pos   = self.player.get_position(),
                ghosts       = self.gameEngine.ghosts,
                block_size   = self.block_size,
            )

        if hasattr(self.gameEngine, '_infection'):
            self.gameEngine._infection = None
        self.start_position = (-1, -1)
        self.trail.clear()
        self._last_trail_cell = (-1, -1)

    def calculate_coverage(self):
        total = self.width * self.height
        border = (self.width*2) + (self.height*2) - 4
        captured = sum(row.count(1) for row in self.grid)
        self.captured_area = (max(0, captured - border) / (total - border)) * 100.0 if total > border else 0.0
        return self.captured_area

    def reset(self):
        self.grid = self._create_grid()
        self.captured_area = 0.0
        self.trail, self.start_position = [], (-1, -1)
        self._last_trail_cell = (-1, -1)
        self._apply_border()

    def draw(self, surface, color=(38, 38, 56), offset_y=0, infection=None):
        bs = self.block_size

        infected_cells = set()
        infected_front = -1
        if infection and infection['cells']:
            front_idx = infection['front']
            for i, cell in enumerate(infection['cells']):
                if i <= front_idx:
                    infected_cells.add(cell)
            infected_front = front_idx

        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                rx = x * bs
                ry = y * bs + offset_y
                rect = pygame.Rect(rx, ry, bs, bs)

                if cell == 1:
                    pygame.draw.rect(surface, (40, 60, 80), rect)
                    pygame.draw.rect(surface, (60, 90, 110), rect, 1)

                elif cell == 2:
                    if (x, y) in infected_cells:
                        pygame.draw.rect(surface, (180, 30, 30), rect)
                    else:
                        pygame.draw.rect(surface, (0, 180, 60), rect)