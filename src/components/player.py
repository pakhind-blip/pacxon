import pygame
import math
from core.game_object import GameObject
from core.collision import Collision

LEFT, RIGHT, UP, DOWN = 0, 1, 2, 3

class Player(GameObject, Collision):
    def __init__(self, width=20, height=20, block_size=20, move_delay=4):
        super().__init__(x=0.0, y=0.0, color=(255,230,0), speed=1.0)
        self.width=width; self.height=height; self.block_size=block_size
        self.grid_x=self.grid_y=0; self.target_x=self.target_y=0.0
        self.direction=RIGHT; self.move_delay=move_delay; self.move_timer=0
        self.lerp_speed=0.4; self.lives=3; self.is_trailing=False
        self.is_iframe=False; self.iframe_duration=210; self.iframe_timer=0
        self.blink_speed=10; self.sword_immune=False; self._tick=0
        # StatsLogger reference — set by GameEngine after construction
        self.stats: object | None = None

    def is_collision(self, x, y):
        return (self.x < x+self.width and self.x+self.width > x and
                self.y < y+self.height and self.y+self.height > y)

    def get_grid_position(self): return self.grid_x, self.grid_y
    def get_position(self):      return self.x, self.y
    def reset_movement(self):    self.is_trailing=False; self.direction=RIGHT; self.move_timer=0
    def update(self): pass

    def set_position(self, x, y):
        self.grid_x,self.grid_y=x,y
        self.x,self.y=x*self.block_size,y*self.block_size
        self.target_x,self.target_y=self.x,self.y

    def move_with_collision(self, keys, grid_manager, item_pos=None):
        if self.is_iframe:
            # Only count down timer while player is on safe wall territory
            cur_cell = grid_manager.get_cell(self.grid_x, self.grid_y)
            if cur_cell == 1:
                self.iframe_timer -= 1
                if self.iframe_timer <= 0:
                    self.is_iframe = False
        if self.move_timer>0:
            self.move_timer-=1
        else:
            k_l=keys[pygame.K_LEFT]  or keys[pygame.K_a]
            k_r=keys[pygame.K_RIGHT] or keys[pygame.K_d]
            k_u=keys[pygame.K_UP]    or keys[pygame.K_w]
            k_d=keys[pygame.K_DOWN]  or keys[pygame.K_s]
            if self.is_trailing:
                if   self.direction==RIGHT: k_l=False
                elif self.direction==LEFT:  k_r=False
                elif self.direction==UP:    k_d=False
                elif self.direction==DOWN:  k_u=False
            dx=dy=0
            prev_direction = self.direction
            if   k_l: dx,self.direction=-1,LEFT
            elif k_r: dx,self.direction= 1,RIGHT
            elif k_u: dy,self.direction=-1,UP
            elif k_d: dy,self.direction= 1,DOWN

            # ── Stats: notify direction change while trailing ─────────────
            if self.is_trailing and self.stats and self.direction != prev_direction:
                self.stats.on_direction_change(self.direction)

            if dx or dy:
                ngx,ngy=self.grid_x+dx,self.grid_y+dy
                if 0<=ngx<grid_manager.width and 0<=ngy<grid_manager.height:
                    next_cell = grid_manager.get_cell(ngx, ngy)
                    # End iframe the moment player steps onto empty space (starts trail)
                    if self.is_iframe and next_cell == 0:
                        self.is_iframe = False
                        self.iframe_timer = 0
                    # ── Stats: detect trail start (stepping onto empty cell) ──
                    was_trailing = self.is_trailing
                    if not was_trailing and next_cell == 0 and self.stats:
                        self.stats.on_trail_start(self.direction)

                    self.grid_x,self.grid_y=ngx,ngy
                    self.target_x=ngx*self.block_size; self.target_y=ngy*self.block_size
                    self.move_timer=self.move_delay
        self.x+=(self.target_x-self.x)*self.lerp_speed
        self.y+=(self.target_y-self.y)*self.lerp_speed

    def lose_life(self):
        self.lives-=1
        if self.lives>0:
            self.is_iframe=True; self.iframe_timer=self.iframe_duration
        return self.lives

    def clamp_to_bounds(self, sw, sh):
        self.x=max(0,min(self.x,sw-self.width)); self.y=max(0,min(self.y,sh-self.height))

    def _rotated_pts(self, cx, cy, pts, angle):
        c,s=math.cos(angle),math.sin(angle)
        return [(int(cx+px*c-py*s),int(cy+px*s+py*c)) for px,py in pts]

    def draw(self, surface, offset_y=0):
        self._tick+=1
        # Blink during iframe
        if self.is_iframe and (self.iframe_timer//self.blink_speed)%2!=0: return
        bs=self.block_size
        cx=int(self.x+bs//2)
        cy=int(self.y+bs//2+offset_y)
        r=bs//2-1
        angle={RIGHT:0,DOWN:math.pi/2,LEFT:math.pi,UP:-math.pi/2}.get(self.direction,0)
        color=(255,100,100) if self.is_iframe else (255,230,0)
        raw=[(r,0),(-r+3,-(r-3)),(-(r//2),0),(-r+3,r-3)]
        pts=self._rotated_pts(cx,cy,raw,angle)
        pygame.draw.polygon(surface, color, pts)
        pygame.draw.polygon(surface, (255,255,255), pts, 1)