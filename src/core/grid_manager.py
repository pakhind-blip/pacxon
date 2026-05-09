import pygame
from collections import deque


class GridManager:
    def __init__(self, width: int, height: int, player, gameEngine, block_size: int = 20):
        self.width = width; self.height = height; self.block_size = block_size
        self.grid = self._create_grid()
        self.player = player; self.gameEngine = gameEngine
        self.captured_area = 0.0
        self.trail: list = []
        self.start_position = (-1, -1)
        self.before_position = (0, 0)
        self._tick = 0
        self._last_trail_cell = (-1, -1)
        self._apply_border()

    # ── grid helpers ──────────────────────────────────────────────────────
    def _create_grid(self) -> list:
        return [[0] * self.width for _ in range(self.height)]

    def _apply_border(self) -> None:
        for x in range(self.width):
            self.grid[0][x] = self.grid[self.height - 1][x] = 1
        for y in range(self.height):
            self.grid[y][0] = self.grid[y][self.width - 1] = 1

    def get_cell(self, x, y) -> int:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return 1

    # ── per-tick update ───────────────────────────────────────────────────
    def update_grid(self) -> None:
        self._tick += 1
        gx, gy = self.player.get_grid_position()

        # Self-intersection check (exclude head)
        if self.player.is_trailing and self.trail and (gx, gy) in set(self.trail[:-1]):
            self.gameEngine._player_hit()
            return

        cell = self.grid[gy][gx]
        if cell == 0:
            self.grid[gy][gx] = 2
            sfx = getattr(self.gameEngine, 'sfx', None)
            if sfx and (gx, gy) != self._last_trail_cell:
                sfx.play_trail()
                self._last_trail_cell = (gx, gy)
            if self.start_position == (-1, -1):
                self.start_position = self.before_position
                self.player.is_trailing = True
            self.trail.append((gx, gy))
        elif cell == 1:
            if self.start_position != (-1, -1):
                self.player.is_trailing = False
                self.flood_fill(gx, gy)
            else:
                self.before_position = (gx, gy)
        self.calculate_coverage()

    # ── flood fill / capture ──────────────────────────────────────────────
    def flood_fill(self, end_x: int, end_y: int) -> None:
        rows, cols = self.height, self.width
        sx, sy     = self.start_position
        dirs       = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        # BFS for shortest wall path back to start
        parent = {(end_x, end_y): None}
        queue  = deque([(end_x, end_y)])
        found  = False
        while queue and not found:
            x, y = queue.popleft()
            if x == sx and y == sy:
                found = True; break
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
            node = (sx, sy)
            while node is not None:
                shortest_path.append(node)
                node = parent[node]

        if not shortest_path:
            self._reset_trail()
            return

        border_set = set(self.trail) | set(shortest_path)

        # Flood from edges to find outside (non-captured) cells
        o_q = deque()
        for x in range(cols):
            o_q.append((x, 0)); o_q.append((x, rows - 1))
        for y in range(rows):
            o_q.append((0, y)); o_q.append((cols - 1, y))

        v_o: set = set(); a_o: set = set()
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

        # Ghost-protected regions — cells reachable from each non-insider ghost
        g_p: set = set()
        bs = self.block_size
        for g in self.gameEngine.ghosts:
            if getattr(g, 'is_insider', False):
                continue
            ghost_gx = int((g.x + bs / 2) // bs)
            ghost_gy = int((g.y + bs / 2) // bs)
            if (ghost_gx, ghost_gy) in border_set:
                continue
            if self.get_cell(ghost_gx, ghost_gy) not in (0, 2):
                continue
            q: deque = deque([(ghost_gx, ghost_gy)])
            v: set   = {(ghost_gx, ghost_gy)}
            while q:
                cx, cy = q.popleft()
                g_p.add((cx, cy))
                for dx, dy in dirs:
                    nx, ny = cx + dx, cy + dy
                    if (0 <= nx < cols and 0 <= ny < rows
                            and (nx, ny) not in v
                            and (nx, ny) not in border_set
                            and self.grid[ny][nx] in (0, 2)):
                        v.add((nx, ny)); q.append((nx, ny))

        # Fill captured cells
        new_cnt = 0
        for y in range(rows):
            row = self.grid[y]
            for x in range(cols):
                if row[x] == 2 or (row[x] == 0 and (x, y) not in a_o and (x, y) not in g_p):
                    row[x] = 1; new_cnt += 1

        if new_cnt > 0:
            self.gameEngine.score += new_cnt
            sfx = getattr(self.gameEngine, 'sfx', None)
            if sfx: sfx.play_capture()
            px, py = self.player.get_position()
            add_pop = getattr(self.gameEngine, 'add_score_pop', None)
            if add_pop: add_pop(int(px), int(py), new_cnt)

        # Stats callback
        stats = getattr(self.player, 'stats', None)
        if stats is not None:
            total    = self.width * self.height
            border   = (self.width * 2) + (self.height * 2) - 4
            playable = max(1, total - border)
            stats.on_trail_close(
                level       = self.gameEngine.level,
                capture_pct = round((new_cnt / playable) * 100.0, 2),
                player_pos  = self.player.get_position(),
                ghosts      = self.gameEngine.ghosts,
                block_size  = self.block_size,
            )

        if hasattr(self.gameEngine, '_infection'):
            self.gameEngine._infection = None
        self._reset_trail()

    def _reset_trail(self):
        self.start_position   = (-1, -1)
        self.trail            = []
        self._last_trail_cell = (-1, -1)

    # ── coverage ──────────────────────────────────────────────────────────
    def calculate_coverage(self) -> float:
        total    = self.width * self.height
        border   = (self.width * 2) + (self.height * 2) - 4
        captured = sum(row.count(1) for row in self.grid)
        self.captured_area = (
            max(0, captured - border) / (total - border) * 100.0
            if total > border else 0.0
        )
        return self.captured_area

    def reset(self):
        self.grid          = self._create_grid()
        self.captured_area = 0.0
        self._reset_trail()
        self._apply_border()

    # ── draw ──────────────────────────────────────────────────────────────
    def draw(self, surface, color=(38, 38, 56), offset_y=0, infection=None):
        bs = self.block_size

        # Build infected cells set once
        infected_cells: set = set()
        if infection and infection['cells']:
            for i, cell in enumerate(infection['cells']):
                if i <= infection['front']:
                    infected_cells.add(cell)

        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                rx = x * bs; ry = y * bs + offset_y
                rect = pygame.Rect(rx, ry, bs, bs)
                if cell == 1:
                    pygame.draw.rect(surface, (40, 60, 80),  rect)
                    pygame.draw.rect(surface, (60, 90, 110), rect, 1)
                elif cell == 2:
                    col = (180, 30, 30) if (x, y) in infected_cells else (0, 180, 60)
                    pygame.draw.rect(surface, col, rect)