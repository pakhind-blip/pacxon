import pygame
import math
from collections import deque

class GridManager:
    def __init__(self, width: int, height: int, player, gameEngine, block_size: int = 20):
        self.width, self.height, self.block_size = width, height, block_size
        self.grid = self._create_grid()
        self.player, self.gameEngine = player, gameEngine
        self.captured_area = 0.0
        self.trail = []
        self.start_position = (-1, -1)
        self.before_postition = (0, 0)
        self._tick = 0
        self._apply_border()

    def _create_grid(self) -> list: return [[0 for _ in range(self.width)] for _ in range(self.height)]
    def _apply_border(self) -> None:
        for x in range(self.width): self.grid[0][x] = self.grid[self.height-1][x] = 1
        for y in range(self.height): self.grid[y][0] = self.grid[y][self.width-1] = 1

    def get_cell(self, x, y): return self.grid[y][x] if 0 <= x < self.width and 0 <= y < self.height else 1

    def update_grid(self) -> None:
        self._tick += 1
        gx, gy = self.player.get_grid_position()
        if self.player.is_trailing and (gx, gy) in self.trail[:-1]:
            self.gameEngine._player_hit(); return
        if self.grid[gy][gx] == 0:
            self.grid[gy][gx] = 2
            if self.start_position == (-1, -1):
                self.start_position = self.before_postition
                self.player.is_trailing = True
            self.trail.append((gx, gy))
        elif self.grid[gy][gx] == 1:
            if self.start_position != (-1, -1):
                self.player.is_trailing = False
                self.flood_fill(gx, gy)
            else: self.before_postition = (gx, gy)
        self.calculate_coverage()

    def flood_fill(self, end_x, end_y):
        rows, cols = self.height, self.width
        start_x, start_y = self.start_position
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        queue, visited = deque([(end_x, end_y, [])]), {(end_x, end_y)}
        shortest_path = []
        while queue:
            x, y, path = queue.popleft()
            if x == start_x and y == start_y: shortest_path = path + [(x, y)]; break
            for dx, dy in dirs:
                nx, ny = x+dx, y+dy
                if 0<=nx<cols and 0<=ny<rows and (nx,ny) not in visited and self.grid[ny][nx]!=0 and (nx,ny) not in self.trail:
                    visited.add((nx,ny)); queue.append((nx,ny, path+[(x,y)]))
        border_set = set(self.trail + shortest_path)
        min_x, max_x = max(0, min(x for x,y in border_set)-1), min(cols-1, max(x for x,y in border_set)+1)
        min_y, max_y = max(0, min(y for x,y in border_set)-1), min(rows-1, max(y for x,y in border_set)+1)
        o_q = deque()
        for x in range(min_x, max_x+1): o_q.append((x,min_y)); o_q.append((x,max_y))
        for y in range(min_y, max_y+1): o_q.append((min_x,y)); o_q.append((max_x,y))
        v_o, a_o = set(), set()
        while o_q:
            cx, cy = o_q.popleft()
            if (cx,cy) in v_o or (cx,cy) in border_set: continue
            v_o.add((cx,cy))
            if self.grid[cy][cx] == 0:
                a_o.add((cx,cy))
                for dx, dy in dirs:
                    nx, ny = cx+dx, cy+dy
                    if min_x<=nx<=max_x and min_y<=ny<=max_y: o_q.append((nx,ny))
        g_p = set()
        for g in self.gameEngine.ghosts:
            gx, gy = int(g.x//self.block_size), int(g.y//self.block_size)
            if (gx,gy) not in border_set and self.get_cell(gx,gy)==0:
                q, v = deque([(gx,gy)]), {(gx,gy)}
                while q:
                    cx,cy = q.popleft(); g_p.add((cx,cy))
                    for dx, dy in dirs:
                        nx, ny = cx+dx, cy+dy
                        if 0<=nx<cols and 0<=ny<rows and (nx,ny) not in v and (nx,ny) not in border_set and self.grid[ny][nx]==0:
                            v.add((nx,ny)); q.append((nx,ny))
        new_cnt = 0
        for y in range(min_y, max_y+1):
            for x in range(min_x, max_x+1):
                if self.grid[y][x]==2 or (self.grid[y][x]==0 and (x,y) not in a_o and (x,y) not in g_p):
                    self.grid[y][x]=1; new_cnt+=1
        if new_cnt > 0:
            self.gameEngine.score += new_cnt
            # Score pop at player position
            px, py = self.player.get_position()
            if hasattr(self.gameEngine, 'add_score_pop'):
                self.gameEngine.add_score_pop(int(px), int(py), new_cnt)
        self.start_position = (-1, -1); self.trail.clear()

    def calculate_coverage(self):
        total = self.width * self.height
        border = (self.width*2) + (self.height*2) - 4
        captured = sum(row.count(1) for row in self.grid)
        self.captured_area = (max(0, captured - border) / (total - border)) * 100.0 if total > border else 0.0
        return self.captured_area

    def reset(self):
        self.grid = self._create_grid(); self.captured_area = 0.0
        self.trail, self.start_position = [], (-1, -1); self._apply_border()

    def draw(self, surface, color=(38, 38, 56), offset_y=0):
        t = self._tick
        bs = self.block_size
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                rx = x * bs
                ry = y * bs + offset_y
                rect = pygame.Rect(rx, ry, bs, bs)

                if cell == 1:
                    # Captured wall: deep teal with inner bevel
                    pygame.draw.rect(surface, (28, 42, 52), rect)
                    # Top/left highlight
                    pygame.draw.line(surface, (55, 75, 90), (rx, ry), (rx + bs - 1, ry), 1)
                    pygame.draw.line(surface, (55, 75, 90), (rx, ry), (rx, ry + bs - 1), 1)
                    # Bottom/right shadow
                    pygame.draw.line(surface, (15, 22, 30), (rx + bs - 1, ry), (rx + bs - 1, ry + bs - 1), 1)
                    pygame.draw.line(surface, (15, 22, 30), (rx, ry + bs - 1), (rx + bs - 1, ry + bs - 1), 1)
                    # Subtle interior dot
                    pygame.draw.circle(surface, (40, 60, 75), (rx + bs // 2, ry + bs // 2), 1)

                elif cell == 2:
                    # Active trail — animated neon green
                    pulse = 0.7 + 0.3 * math.sin(t * 0.15 + x * 0.3 + y * 0.3)
                    trail_color = (0, int(210 * pulse), int(80 * pulse))
                    pygame.draw.rect(surface, trail_color, rect)
                    # Bright center glow line
                    inner = rect.inflate(-6, -6)
                    glow_c = (int(180 * pulse), 255, int(200 * pulse))
                    pygame.draw.rect(surface, glow_c, inner)

                else:
                    # Empty space — subtle grid dots
                    if x % 2 == 0 and y % 2 == 0:
                        pygame.draw.circle(surface, (22, 22, 36), rect.center, 1)
