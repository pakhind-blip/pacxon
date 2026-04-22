import pygame
import random
import math
from collections import deque
from core.game_object import GameObject
from core.collision import Collision

DIRS4 = [(1,0),(-1,0),(0,1),(0,-1)]


class Ghost(GameObject, Collision):
    def __init__(self, x, y, color, block_size, speed=2.0):
        super().__init__(x * block_size, y * block_size, color, speed)
        self.block_size = block_size
        self.width = self.height = block_size
        self.dx = random.choice([-1, 1]) * speed
        self.dy = random.choice([-1, 1]) * speed
        self._tick = random.randint(0, 100)

    def is_collision(self, px, py):
        return (self.x < px + self.block_size and self.x + self.width  > px and
                self.y < py + self.block_size and self.y + self.height > py)

    def _corners(self, px, py, m=1):
        bs = self.block_size
        return [
            (int((px + m)              // bs), int((py + m)              // bs)),
            (int((px + self.width - m) // bs), int((py + m)              // bs)),
            (int((px + m)              // bs), int((py + self.height - m) // bs)),
            (int((px + self.width - m) // bs), int((py + self.height - m) // bs)),
        ]

    def _hits_wall(self, px, py, gm):
        return any(gm.get_cell(cx, cy) == 1 for cx, cy in self._corners(px, py))

    def _overlapping_wall(self, gm):
        return self._hits_wall(self.x, self.y, gm)

    def _rescue_from_wall(self, gm):
        bs  = self.block_size
        ndx = getattr(self, '_charge_dx', self.dx) or 1
        ndy = getattr(self, '_charge_dy', self.dy) or 1
        for _ in range(bs):
            if not self._overlapping_wall(gm): return
            if ndx > 0:   self.x -= 1
            elif ndx < 0: self.x += 1
            if ndy > 0:   self.y -= 1
            elif ndy < 0: self.y += 1
        if self._overlapping_wall(gm):
            cols, rows = gm.width, gm.height
            sgx = int((self.x + self.width  / 2) // bs)
            sgy = int((self.y + self.height / 2) // bs)
            visited, queue = {(sgx, sgy)}, deque([(sgx, sgy)])
            while queue:
                gx, gy = queue.popleft()
                if gm.get_cell(gx, gy) == 0:
                    self.x, self.y = gx * bs, gy * bs; return
                for dx, dy in DIRS4:
                    nx, ny = gx+dx, gy+dy
                    if (nx,ny) not in visited and 0<=nx<cols and 0<=ny<rows:
                        visited.add((nx,ny)); queue.append((nx,ny))

    def _bounce_move(self, gm):
        nx = self.x + self.dx
        if self._hits_wall(nx, self.y, gm):
            self.dx *= -1; nx = self.x + self.dx
            if self._hits_wall(nx, self.y, gm): nx = self.x
        self.x = nx
        ny = self.y + self.dy
        if self._hits_wall(self.x, ny, gm):
            self.dy *= -1; ny = self.y + self.dy
            if self._hits_wall(self.x, ny, gm): ny = self.y
        self.y = ny

    def _draw_eyes(self, surface, cx, cy, r):
        for ex in [-r//3, r//3]:
            pygame.draw.circle(surface, (230, 240, 255), (cx + ex, cy - r//5), max(1, r//5))
            pygame.draw.circle(surface, (10, 10, 30),    (cx + ex + 1, cy - r//5 + 1), max(1, r//9))

    def draw(self, surface, offset_y=0):
        self._tick += 1
        bs = self.block_size
        cx = int(self.x + bs//2)
        cy = int(self.y + bs//2 + offset_y)
        r  = bs//2 - 1
        pygame.draw.circle(surface, self.color, (cx, cy), r)
        self._draw_eyes(surface, cx, cy, r)


# ── GhostBouncer ─────────────────────────────────────────────────────────────

class GhostBouncer(Ghost):
    def __init__(self, x, y, block_size):
        super().__init__(x, y, (255,80,160), block_size, speed=4.5)
        a = random.uniform(0, 2*math.pi)
        self.dx, self.dy = math.cos(a)*self.speed, math.sin(a)*self.speed

    def update(self, gm):
        if getattr(self,'ghost_frozen',False): return
        if self._overlapping_wall(gm):
            self._rescue_from_wall(gm); self.dx *= -1; self.dy *= -1; return
        self._bounce_move(gm)


# ── GhostClimber ─────────────────────────────────────────────────────────────

class GhostClimber(Ghost):
    def __init__(self, x, y, block_size, clockwise=True):
        super().__init__(x, y, (255,140,20), block_size, speed=2.5)
        self.clockwise = clockwise
        self.target_x = self.x; self.target_y = self.y
        self.grid_x = x; self.grid_y = y
        self.current_dir = (1,0)
        self._last_wall_count = -1
        self._history = deque(maxlen=12)

    def _is_open(self, gx, gy, gm):    return gm.get_cell(gx, gy) in (0, 2)
    def _has_wall_nb(self, gx, gy, gm): return any(gm.get_cell(gx+dx,gy+dy)==1 for dx,dy in DIRS4)

    def _find_wall_edge(self, gm):
        bs = self.block_size
        start = (int((self.x+self.width/2)//bs), int((self.y+self.height/2)//bs))
        visited, queue = {start}, deque([start])
        while queue:
            cx, cy = queue.popleft()
            if self._is_open(cx,cy,gm) and self._has_wall_nb(cx,cy,gm): return (cx,cy)
            for dx,dy in DIRS4:
                nx,ny=cx+dx,cy+dy
                if (nx,ny) not in visited: visited.add((nx,ny)); queue.append((nx,ny))
        return None

    def _anchor(self, gm):
        dest = self._find_wall_edge(gm)
        if not dest: return
        self.grid_x, self.grid_y = dest
        self.x = self.grid_x * self.block_size; self.y = self.grid_y * self.block_size
        self.target_x, self.target_y = self.x, self.y
        self._history.clear()
        for adx,ady in [(1,0),(0,1),(-1,0),(0,-1)]:
            sdx,sdy = (-ady,adx) if self.clockwise else (ady,-adx)
            if (self._is_open(self.grid_x+adx,self.grid_y+ady,gm) and
                    gm.get_cell(self.grid_x+sdx,self.grid_y+sdy)==1):
                self.current_dir=(adx,ady); return
        for adx,ady in [(1,0),(0,1),(-1,0),(0,-1)]:
            if self._is_open(self.grid_x+adx,self.grid_y+ady,gm):
                self.current_dir=(adx,ady); return

    def _in_wall(self, gm):
        bs = self.block_size
        return gm.get_cell(int((self.x+self.width/2)//bs), int((self.y+self.height/2)//bs))==1

    def update(self, gm):
        if getattr(self,'ghost_frozen',False): return
        wc = sum(c==1 for row in gm.grid for c in row)
        if wc != self._last_wall_count or self._in_wall(gm):
            self._last_wall_count = wc; self._anchor(gm)
        if abs(self.x-self.target_x)<self.speed and abs(self.y-self.target_y)<self.speed:
            self.x,self.y = self.target_x,self.target_y; self._next_node(gm)
        if   self.x < self.target_x: self.x += self.speed
        elif self.x > self.target_x: self.x -= self.speed
        if   self.y < self.target_y: self.y += self.speed
        elif self.y > self.target_y: self.y -= self.speed

    def _next_node(self, gm):
        gx,gy = int(self.grid_x),int(self.grid_y); dx,dy = self.current_dir
        moves = [(-dy,dx),(dx,dy),(dy,-dx),(-dx,-dy)] if self.clockwise else [(dy,-dx),(dx,dy),(-dy,dx),(-dx,-dy)]
        recent = set(self._history)
        cands = [(rank, not self._has_wall_nb(gx+mdx,gy+mdy,gm),
                  (gx+mdx,gy+mdy,(mdx,mdy)) in recent, mdx, mdy)
                 for rank,(mdx,mdy) in enumerate(moves)
                 if self._is_open(gx+mdx,gy+mdy,gm)]
        if not cands: return
        cands.sort()
        *_, mdx,mdy = cands[0]
        self.current_dir=(mdx,mdy); self.grid_x+=mdx; self.grid_y+=mdy
        self.target_x=self.grid_x*self.block_size; self.target_y=self.grid_y*self.block_size
        self._history.append((int(self.grid_x),int(self.grid_y),self.current_dir))


class GhostClimberCW(GhostClimber):
    def __init__(self,x,y,bs): super().__init__(x,y,bs,True)

class GhostClimberCCW(GhostClimber):
    def __init__(self,x,y,bs): super().__init__(x,y,bs,False)


# ── GhostInsider ─────────────────────────────────────────────────────────────

class GhostInsider(Ghost):
    SPEED=3.5; COLOR=(0,220,255)

    def __init__(self, x, y, block_size):
        super().__init__(x, y, self.COLOR, block_size, speed=self.SPEED)
        self.is_insider = True
        a = random.uniform(0,2*math.pi)
        self.dx, self.dy = math.cos(a)*self.SPEED, math.sin(a)*self.SPEED

    def _hits_inside(self, px, py, gm):
        bs,m = gm.block_size,2; w=self.width-m; mx,my=gm.width-1,gm.height-1
        for gx,gy in [(int((px+m)//bs),int((py+m)//bs)),(int((px+w)//bs),int((py+m)//bs)),
                      (int((px+m)//bs),int((py+w)//bs)),(int((px+w)//bs),int((py+w)//bs))]:
            if gx<=0 or gy<=0 or gx>=mx or gy>=my or gm.get_cell(gx,gy)!=1: return True
        return False

    def update(self, gm):
        if getattr(self,'ghost_frozen',False): return
        nx,ny = self.x+self.dx, self.y+self.dy
        if self._hits_inside(nx,self.y,gm):
            self.dx*=-1; nx=self.x+self.dx
            if self._hits_inside(nx,self.y,gm): nx=self.x
        ny = self.y+self.dy
        if self._hits_inside(nx,ny,gm):
            self.dy*=-1; ny=self.y+self.dy
            if self._hits_inside(nx,ny,gm): ny=self.y
        self.x,self.y=nx,ny


# ── GhostDasher ──────────────────────────────────────────────────────────────

class GhostDasher(Ghost):
    WANDER_SPEED=3.0; DASH_SPEED=13.0; CHARGE_FRAMES=50; WANDER_FRAMES=120
    COLOR_NORMAL=(255,220,0); COLOR_CHARGE=(255,255,180); COLOR_DASH=(255,200,0)
    _WANDER=0; _CHARGE=1; _DASH=2

    def __init__(self, x, y, block_size):
        super().__init__(x, y, self.COLOR_NORMAL, block_size, speed=self.WANDER_SPEED)
        a=random.uniform(0,2*math.pi)
        self.dx,self.dy=math.cos(a)*self.WANDER_SPEED,math.sin(a)*self.WANDER_SPEED
        self._state=self._WANDER; self._state_timer=0
        self._wander_timer=self.WANDER_FRAMES; self._dash_dx=self._dash_dy=0.0
        self.is_dasher=True; self._streak=[]

    def _snap_dir(self, tx, ty):
        vx=tx-(self.x+self.width/2); vy=ty-(self.y+self.height/2)
        if abs(vx)>=abs(vy): return (1.,0.) if vx>=0 else (-1.,0.)
        return (0.,1.) if vy>=0 else (0.,-1.)

    def update(self, gm):
        if getattr(self,'ghost_frozen',False): return
        if self._overlapping_wall(gm):
            self._rescue_from_wall(gm)
            if self._state==self._DASH: self._enter_wander()
            return
        if   self._state==self._WANDER: self._do_wander(gm)
        elif self._state==self._CHARGE:
            self._state_timer-=1
            if self._state_timer<=0: self._state=self._DASH
        elif self._state==self._DASH:   self._do_dash(gm)

    def _do_wander(self, gm):
        self._bounce_move(gm)
        if self._wander_timer>0: self._wander_timer-=1
        else:
            p=gm.player; dx,dy=self._snap_dir(p.x+p.width/2,p.y+p.height/2)
            self._dash_dx,self._dash_dy=dx*self.DASH_SPEED,dy*self.DASH_SPEED
            self._state=self._CHARGE; self._state_timer=self.CHARGE_FRAMES; self._streak.clear()

    def _do_dash(self, gm):
        self._streak.append((int(self.x),int(self.y)))
        if len(self._streak)>8: self._streak.pop(0)
        total=math.hypot(self._dash_dx,self._dash_dy)
        if not total: self._enter_wander(); return
        ux,uy=self._dash_dx/total,self._dash_dy/total
        rem=total; step=float(self.block_size-1)
        while rem>0.01:
            m=min(step,rem); sdx,sdy=ux*m,uy*m
            if self._hits_wall(self.x+sdx,self.y,gm) or self._hits_wall(self.x,self.y+sdy,gm):
                self._enter_wander(); return
            self.x+=sdx; self.y+=sdy; rem-=m

    def _enter_wander(self):
        self._state=self._WANDER; self._wander_timer=self.WANDER_FRAMES; self._streak.clear()
        a=random.uniform(0,2*math.pi)
        self.dx,self.dy=math.cos(a)*self.WANDER_SPEED,math.sin(a)*self.WANDER_SPEED

    def draw(self, surface, offset_y=0):
        self._tick += 1
        bs = self.block_size
        cx = int(self.x + bs//2)
        cy = int(self.y + bs//2 + offset_y)
        r  = bs//2 - 1
        # Show charge state with a simple ring
        if self._state == self._CHARGE:
            pygame.draw.circle(surface, (255, 255, 100), (cx, cy), r + 3, 2)
            bc = self.COLOR_CHARGE
        elif self._state == self._DASH:
            bc = self.COLOR_DASH
        else:
            bc = self.COLOR_NORMAL
        pygame.draw.circle(surface, bc, (cx, cy), r)
        self._draw_eyes(surface, cx, cy, r)


# ── GhostFreezer ─────────────────────────────────────────────────────────────

class GhostFreezer(Ghost):
    WANDER_SPEED=2.5; CHARGE_FRAMES=90; WANDER_FRAMES=200
    FREEZE_DURATION=300; FREEZE_RANGE=8
    COLOR_NORMAL=(30,100,220); COLOR_CHARGE=(120,180,255)
    _WANDER=0; _CHARGE=1

    def __init__(self, x, y, block_size):
        super().__init__(x, y, self.COLOR_NORMAL, block_size, speed=self.WANDER_SPEED)
        self.is_freezer=True
        a=random.uniform(0,2*math.pi)
        self.dx,self.dy=math.cos(a)*self.WANDER_SPEED,math.sin(a)*self.WANDER_SPEED
        self._state=self._WANDER; self._wander_timer=self.WANDER_FRAMES
        self._charge_timer=0; self._ring_radius=0.0

    def _dist_cells(self, gm):
        bs=self.block_size; gx=(self.x+self.width/2)/bs; gy=(self.y+self.height/2)/bs
        pgx,pgy=gm.player.get_grid_position()
        return max(abs(gx-pgx),abs(gy-pgy))

    def update(self, gm):
        if getattr(self,'ghost_frozen',False): return
        if self._overlapping_wall(gm):
            self._rescue_from_wall(gm); self.dx*=-1; self.dy*=-1; return
        if self._state==self._WANDER: self._do_wander(gm)
        else: self._do_charge(gm)

    def _do_wander(self, gm):
        self._bounce_move(gm)
        if self._wander_timer>0: self._wander_timer-=1
        elif self._dist_cells(gm)<=self.FREEZE_RANGE:
            self._state=self._CHARGE; self._charge_timer=self.CHARGE_FRAMES; self._ring_radius=0.0
        else: self._wander_timer=40

    def _do_charge(self, gm):
        nx=self.x+self.dx*0.25
        if not self._hits_wall(nx,self.y,gm): self.x=nx
        ny=self.y+self.dy*0.25
        if not self._hits_wall(self.x,ny,gm): self.y=ny
        self._ring_radius=(1.0-self._charge_timer/self.CHARGE_FRAMES)*self.FREEZE_RANGE*self.block_size
        self._charge_timer-=1
        if self._charge_timer<=0: self._fire_pulse(gm)

    def _fire_pulse(self, gm):
        p=gm.player; pgx,pgy=p.get_grid_position()
        if (gm.get_cell(pgx,pgy)!=1 and not getattr(p,'is_frozen',False)
                and not getattr(p,'is_cursed',False) and self._dist_cells(gm)<=self.FREEZE_RANGE):
            dur=self.FREEZE_DURATION//2 if getattr(p,'is_trailing',False) else self.FREEZE_DURATION
            p.is_frozen=True; p.freeze_timer=dur
        self._state=self._WANDER; self._wander_timer=self.WANDER_FRAMES; self._ring_radius=0.0

    def draw(self, surface, offset_y=0):
        self._tick += 1
        bs = self.block_size
        cx = int(self.x + bs//2)
        cy = int(self.y + bs//2 + offset_y)
        r  = bs//2 - 1
        charging = self._state == self._CHARGE
        if charging:
            # Simple expanding ring
            rr = int(self._ring_radius)
            if rr > 0:
                pygame.draw.circle(surface, (100, 160, 255), (cx, cy), rr, 1)
        bc = self.COLOR_CHARGE if (charging and (self._tick // 5) % 2 == 0) else self.COLOR_NORMAL
        pygame.draw.circle(surface, bc, (cx, cy), r)
        self._draw_eyes(surface, cx, cy, r)


# ── GhostReverser ────────────────────────────────────────────────────────────

class GhostReverser(Ghost):
    WANDER_SPEED=6.0; CURSE_DURATION_TRAIL=90; CURSE_DURATION_BODY=240; COLOR=(160,255,0)

    def __init__(self, x, y, block_size):
        super().__init__(x, y, self.COLOR, block_size, speed=self.WANDER_SPEED)
        self.is_reverser=True
        a=random.uniform(0,2*math.pi)
        self.dx,self.dy=math.cos(a)*self.WANDER_SPEED,math.sin(a)*self.WANDER_SPEED

    def update(self, gm):
        if getattr(self,'ghost_frozen',False): return
        if self._overlapping_wall(gm):
            self._rescue_from_wall(gm); self.dx*=-1; self.dy*=-1; return
        self._bounce_move(gm)


# ── GhostWatcher ─────────────────────────────────────────────────────────────

class GhostWatcher(Ghost):
    CHARGE_SPEED=11.0; ALERT_FRAMES=40; COOLDOWN_FRAMES=80
    COLOR_IDLE=(200,50,255); COLOR_ALERT=(255,80,80); COLOR_CHARGE=(255,140,255)
    _IDLE=0; _ALERT=1; _CHARGING=2; _COOLDOWN=3

    def __init__(self, x, y, block_size):
        super().__init__(x, y, self.COLOR_IDLE, block_size, speed=0.0)
        self.is_watcher=True; self.dx=self.dy=0.0
        self._state=self._IDLE; self._state_timer=0
        self._charge_dx=self._charge_dy=0.0; self._streak=[]

    def _has_los(self, gm):
        bs=gm.block_size
        gx=int((self.x+self.width/2)//bs); gy=int((self.y+self.height/2)//bs)
        pgx=int((gm.player.x+gm.player.width/2)//bs); pgy=int((gm.player.y+gm.player.height/2)//bs)
        for ddx,ddy in DIRS4:
            cx,cy=gx+ddx,gy+ddy
            while 0<=cx<gm.width and 0<=cy<gm.height:
                if gm.get_cell(cx,cy)==1: break
                if (cx,cy)==(pgx,pgy): return (float(ddx),float(ddy))
                cx+=ddx; cy+=ddy
        return None

    def update(self, gm):
        if getattr(self,'ghost_frozen',False): return
        if self._overlapping_wall(gm):
            self._rescue_from_wall(gm)
            if self._state==self._CHARGING: self._enter_cooldown()
            return
        if self._state==self._IDLE:
            los=self._has_los(gm)
            if los:
                self._charge_dx,self._charge_dy=los[0]*self.CHARGE_SPEED,los[1]*self.CHARGE_SPEED
                self._state=self._ALERT; self._state_timer=self.ALERT_FRAMES; self._streak.clear()
        elif self._state==self._ALERT:
            self._state_timer-=1
            if self._state_timer<=0: self._state=self._CHARGING
        elif self._state==self._CHARGING:
            self._streak.append((int(self.x),int(self.y)))
            if len(self._streak)>10: self._streak.pop(0)
            rem=math.hypot(self._charge_dx,self._charge_dy)
            if not rem: self._enter_cooldown(); return
            ux,uy=self._charge_dx/rem,self._charge_dy/rem
            left=rem; step=float(self.block_size-1)
            while left>0.01:
                m=min(step,left); sdx,sdy=ux*m,uy*m
                if self._hits_wall(self.x+sdx,self.y,gm) or self._hits_wall(self.x,self.y+sdy,gm):
                    self._enter_cooldown(); return
                self.x+=sdx; self.y+=sdy; left-=m
        elif self._state==self._COOLDOWN:
            self._state_timer-=1
            if self._state_timer<=0: self._state=self._IDLE; self._streak.clear()

    def _enter_cooldown(self):
        self._state=self._COOLDOWN; self._state_timer=self.COOLDOWN_FRAMES

    def draw(self, surface, offset_y=0):
        self._tick += 1
        t  = self._tick
        bs = self.block_size
        cx = int(self.x + bs//2)
        cy = int(self.y + bs//2 + offset_y)
        r  = bs//2 - 1
        if self._state == self._ALERT:
            # Flash ring
            if (t // 4) % 2 == 0:
                pygame.draw.circle(surface, (255, 60, 60), (cx, cy), r + 4, 2)
            bc = self.COLOR_ALERT
        elif self._state == self._CHARGING:
            bc = self.COLOR_CHARGE
        elif self._state == self._COOLDOWN:
            bc = self.COLOR_IDLE
        else:
            # Draw LOS lines simply as thin dots along 4 axes
            bc = self.COLOR_IDLE
        pygame.draw.circle(surface, bc, (cx, cy), r)
        self._draw_eyes(surface, cx, cy, r)


# ── GhostGatekeeper ──────────────────────────────────────────────────────────

class GhostGatekeeper(Ghost):
    PATROL_SPEED=3.5; COLOR=(255,30,30); BLOCK_RADIUS=2

    def __init__(self, x, y, block_size, grid_w, grid_h, clockwise=None):
        super().__init__(x, y, self.COLOR, block_size, speed=self.PATROL_SPEED)
        self.is_gatekeeper=True; self.grid_w=grid_w; self.grid_h=grid_h
        self.clockwise=random.choice([True,False]) if clockwise is None else clockwise
        self._border_path=self._build_path(); self._path_len=len(self._border_path)
        sx,sy=max(0,min(int(x),grid_w-1)),max(0,min(int(y),grid_h-1))
        self._path_index=min(range(self._path_len),
                            key=lambda i:abs(self._border_path[i][0]-sx)+abs(self._border_path[i][1]-sy))
        gx,gy=self._border_path[self._path_index]
        self.x,self.y=float(gx*block_size),float(gy*block_size); self._progress=0.0

    def _build_path(self):
        w,h=self.grid_w,self.grid_h
        p=[(x,0) for x in range(w)]+[(w-1,y) for y in range(1,h)]
        p+=[(x,h-1) for x in range(w-2,-1,-1)]+[(0,y) for y in range(h-2,0,-1)]
        return p

    def get_blocked_cells(self):
        return {self._border_path[(self._path_index+o)%self._path_len]
                for o in range(-self.BLOCK_RADIUS,self.BLOCK_RADIUS+1)}

    def is_border_blocked(self, gx, gy): return (gx,gy) in self.get_blocked_cells()

    def update(self, gm):
        if getattr(self,'ghost_frozen',False): return
        bs=self.block_size; step=1 if self.clockwise else -1
        self._progress+=self.PATROL_SPEED/bs
        while self._progress>=1.0:
            self._progress-=1.0; self._path_index=(self._path_index+step)%self._path_len
        cx,cy=self._border_path[self._path_index]; nidx=(self._path_index+step)%self._path_len
        nx,ny=self._border_path[nidx]
        self.x=(cx+(nx-cx)*self._progress)*bs; self.y=(cy+(ny-cy)*self._progress)*bs

    def draw(self, surface, offset_y=0):
        self._tick += 1
        bs = self.block_size
        # Draw blocked cells as simple red X marks
        for bx, by in self.get_blocked_cells():
            rx = bx * bs; ry = by * bs + offset_y
            pad = 4
            pygame.draw.line(surface, (180, 0, 0), (rx+pad, ry+pad), (rx+bs-pad, ry+bs-pad), 2)
            pygame.draw.line(surface, (180, 0, 0), (rx+bs-pad, ry+pad), (rx+pad, ry+bs-pad), 2)
        cx = int(self.x + bs//2)
        cy = int(self.y + bs//2 + offset_y)
        r  = bs//2 - 1
        pygame.draw.circle(surface, self.COLOR, (cx, cy), r)
        self._draw_eyes(surface, cx, cy, r)


# ── GhostDecoy ───────────────────────────────────────────────────────────────

class GhostDecoy(Ghost):
    SPEED=3.0; COLOR=(50,255,80); REVEAL_FRAMES=30; EXPOSE_FRAMES=90
    _HIDDEN=0; _REVEALED=1; _EXPOSED=2

    def __init__(self, x, y, block_size):
        super().__init__(x, y, self.COLOR, block_size, speed=self.SPEED)
        self.is_insider=True; self.is_decoy=True
        a=random.uniform(0,2*math.pi)
        self.dx,self.dy=math.cos(a)*self.SPEED,math.sin(a)*self.SPEED
        self._state=self._HIDDEN; self._state_timer=0; self._hit_fired=False

    def _hits_inside(self, px, py, gm):
        bs,m=gm.block_size,2; w=self.width-m; mx,my=gm.width-1,gm.height-1
        for gx,gy in [(int((px+m)//bs),int((py+m)//bs)),(int((px+w)//bs),int((py+m)//bs)),
                      (int((px+m)//bs),int((py+w)//bs)),(int((px+w)//bs),int((py+w)//bs))]:
            if gx<=0 or gy<=0 or gx>=mx or gy>=my or gm.get_cell(gx,gy)!=1: return True
        return False

    def _move(self, gm):
        nx,ny=self.x+self.dx,self.y+self.dy
        if self._hits_inside(nx,self.y,gm):
            self.dx*=-1; nx=self.x+self.dx
            if self._hits_inside(nx,self.y,gm): nx=self.x
        ny=self.y+self.dy
        if self._hits_inside(nx,ny,gm):
            self.dy*=-1; ny=self.y+self.dy
            if self._hits_inside(nx,ny,gm): ny=self.y
        self.x,self.y=nx,ny

    def update(self, gm):
        if getattr(self,'ghost_frozen',False): return
        bs=self.block_size; p=gm.player
        if self._state==self._HIDDEN:
            self._move(gm)
            ggx=int((self.x+bs/2)//bs); ggy=int((self.y+bs/2)//bs)
            if p.get_grid_position()==(ggx,ggy):
                self._state=self._REVEALED; self._state_timer=self.REVEAL_FRAMES; self._hit_fired=False
        elif self._state==self._REVEALED:
            self._state_timer-=1
            if not self._hit_fired:
                self._hit_fired=True
                if hasattr(gm,'gameEngine'): gm.gameEngine._player_hit()
            if self._state_timer<=0: self._state=self._EXPOSED; self._state_timer=self.EXPOSE_FRAMES
        elif self._state==self._EXPOSED:
            self._move(gm); self._state_timer-=1
            if self._state_timer<=0: self._state=self._HIDDEN

    def draw(self, surface, offset_y=0):
        self._tick += 1
        bs = self.block_size
        gx = int((self.x + bs/2) // bs)
        gy = int((self.y + bs/2) // bs)
        rx = gx * bs
        ry = gy * bs + offset_y
        if self._state == self._HIDDEN:
            # Looks like a wall tile — just a slight tint
            pygame.draw.rect(surface, (28, 42, 52), (rx, ry, bs, bs))
            pygame.draw.rect(surface, (50, 80, 60), (rx, ry, bs, bs), 1)
        elif self._state == self._REVEALED:
            # Flash white then show self
            pygame.draw.rect(surface, (255, 255, 255), (rx - 2, ry - 2, bs + 4, bs + 4), 3)
            pygame.draw.circle(surface, self.COLOR, (rx + bs//2, ry + bs//2), bs//2 - 1)
        else:
            cx = int(self.x + bs//2)
            cy = int(self.y + bs//2 + offset_y)
            r  = bs//2 - 1
            pygame.draw.circle(surface, self.COLOR, (cx, cy), r)
            self._draw_eyes(surface, cx, cy, r)