"""
item_manager.py — Powerup / Debuff item system for PACXON
All game logic identical to original. Only draw() methods simplified.
"""

import pygame
import random
import os as _os

EFFECT_DURATION   = 480
ITEM_LIFETIME     = 600
SPAWN_INTERVAL    = 300
SPAWN_CHANCE      = 0.05
STAR_CHANCE       = 0.05

LIGHTNING = "lightning"
SNOW      = "snow"
SWORD     = "sword"
SLIME     = "slime"
HEART     = "heart"
STAR      = "star"

BASIC_ITEMS = [LIGHTNING, SNOW, SWORD, SLIME, HEART]

ITEM_META = {
    LIGHTNING: {"label": "!", "color": (255, 230, 0),   "hud": "SPEED UP!",      "hud_color": (255, 230,  50)},
    SNOW:      {"label": "*", "color": (160, 220, 255), "hud": "GHOSTS FROZEN!", "hud_color": (160, 220, 255)},
    SWORD:     {"label": "+", "color": (210, 160, 255), "hud": "GHOST KILLER!",  "hud_color": (210, 160, 255)},
    SLIME:     {"label": "~", "color": ( 80, 220,  80), "hud": "GHOSTS SLOWED!", "hud_color": (120, 255, 100)},
    HEART:     {"label": "v", "color": (255,  80, 120), "hud": "+1 LIFE!",       "hud_color": (255, 120, 160)},
    STAR:      {"label": "*", "color": (255, 255,  80), "hud": "STAR POWER!",    "hud_color": (255, 255,  80)},
}


class Item:
    DRAW_SCALE = 1.0
    _image_cache: dict = {}
    _cache_block_size: int = 0
    IMAGES_DIR = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "items")

    @classmethod
    def _load_images(cls, draw_size: int) -> None:
        if cls._cache_block_size == draw_size and cls._image_cache:
            return
        cls._image_cache.clear()
        cls._cache_block_size = draw_size
        candidates = [
            (LIGHTNING, ["lightning.png"]),
            (SNOW,      ["snow.png"]),
            (SWORD,     ["sword.png"]),
            (SLIME,     ["slime.png", "slime .png", "banana.png"]),
            (HEART,     ["heart.png"]),
            (STAR,      ["star.png"]),
        ]
        for item_type, filenames in candidates:
            for fname in filenames:
                path = _os.path.join(_os.path.normpath(cls.IMAGES_DIR), fname)
                if _os.path.exists(path):
                    try:
                        raw = pygame.image.load(path).convert_alpha()
                        cls._image_cache[item_type] = pygame.transform.smoothscale(raw, (draw_size, draw_size))
                    except pygame.error:
                        pass
                    break

    def __init__(self, grid_x: int, grid_y: int, block_size: int, item_type: str):
        self.grid_x     = grid_x
        self.grid_y     = grid_y
        self.block_size = block_size
        self.type       = item_type
        self.lifetime   = ITEM_LIFETIME
        self._tick      = 0
        Item._load_images(int(block_size * self.DRAW_SCALE))

    def update(self) -> bool:
        self.lifetime -= 1
        self._tick    += 1
        return self.lifetime > 0

    def draw(self, surface, offset_y: int = 0) -> None:
        bs  = self.block_size
        cx  = self.grid_x * bs + bs // 2
        cy  = self.grid_y * bs + bs // 2 + offset_y
        r   = bs // 2 - 1
        col = ITEM_META[self.type]["color"]

        # Blink when about to expire
        if self.lifetime < 180 and (self.lifetime // 10) % 2 == 0:
            return

        # Draw colored circle background
        pygame.draw.circle(surface, (8, 8, 22), (cx, cy), r)
        pygame.draw.circle(surface, col, (cx, cy), r, 2)

        # Draw image if available, else plain letter
        draw_size = int(bs * self.DRAW_SCALE)
        img = self._image_cache.get(self.type)
        if img is not None:
            scaled_px = max(8, int(draw_size * 0.80))
            scaled    = pygame.transform.smoothscale(img, (scaled_px, scaled_px))
            rect      = scaled.get_rect(center=(cx, cy))
            surface.blit(scaled, rect)
        else:
            f = pygame.font.Font(None, max(12, bs - 4))
            label = ITEM_META[self.type]["label"]
            ts = f.render(label, True, col)
            surface.blit(ts, (cx - ts.get_width() // 2, cy - ts.get_height() // 2))

    @property
    def pixel_rect(self):
        bs = self.block_size
        return pygame.Rect(self.grid_x * bs, self.grid_y * bs, bs, bs)


class ItemManager:
    _BADGE_H = 22
    _BADGE_W = 108

    def __init__(self, block_size: int):
        self.block_size      = block_size
        self._item: Item | None = None
        self._spawn_timer    = SPAWN_INTERVAL
        self._tick           = 0
        self.lightning_timer = 0
        self.snow_timer      = 0
        self.sword_timer     = 0
        self.banana_timer    = 0
        self.star_timer      = 0
        self.last_collected  = None

    @property
    def has_item(self) -> bool:
        return self._item is not None

    @property
    def lightning_active(self) -> bool:
        return self.lightning_timer > 0

    @property
    def snow_active(self) -> bool:
        return self.snow_timer > 0

    @property
    def sword_active(self) -> bool:
        return self.sword_timer > 0

    @property
    def banana_active(self) -> bool:
        return self.banana_timer > 0

    @property
    def star_active(self) -> bool:
        return self.star_timer > 0

    def any_ghost_slow(self) -> bool:
        return self.snow_active or self.banana_active

    def _choose_type(self) -> str:
        pool = [STAR] * 5 + BASIC_ITEMS * 19
        return random.choice(pool)

    def try_spawn(self, grid_manager, level: int = 1, sfx=None) -> None:
        if self._item is not None:
            return
        self._spawn_timer -= 1
        if self._spawn_timer > 0:
            return
        self._spawn_timer = SPAWN_INTERVAL
        chance = min(0.90, SPAWN_CHANCE + (level - 1) * 0.02)
        if random.random() >= chance:
            return
        gw, gh = grid_manager.width, grid_manager.height
        candidates = [(x, y) for y in range(1, gh - 1) for x in range(1, gw - 1)
                      if grid_manager.get_cell(x, y) == 0]
        if not candidates:
            return
        gx, gy    = random.choice(candidates)
        item_type = self._choose_type()
        self._item = Item(gx, gy, self.block_size, item_type)
        if sfx:
            sfx.play_item_spawn()

    def update(self, player, ghosts, grid_manager, level: int = 1, sfx=None) -> None:
        self._tick += 1

        if self.lightning_timer > 0:
            self.lightning_timer -= 1
            if self.lightning_timer == 0:
                self._restore_player_speed(player)

        if self.snow_timer > 0:
            self.snow_timer -= 1
            if self.snow_timer == 0:
                self._restore_ghost_speeds(ghosts, "snow")

        if self.sword_timer > 0:
            self.sword_timer -= 1
            if self.sword_timer == 0:
                self._restore_player_immunity(player)

        if self.banana_timer > 0:
            self.banana_timer -= 1
            if self.banana_timer == 0:
                self._restore_ghost_speeds(ghosts, "banana")

        if self.star_timer > 0:
            self.star_timer -= 1

        if self._item is not None:
            if not self._item.update():
                self._item = None
                return
            pgx, pgy = player.get_grid_position()
            if pgx == self._item.grid_x and pgy == self._item.grid_y:
                collected_type = self._item.type
                self._apply_effect(collected_type, player, ghosts)
                self._item = None
                self.last_collected = collected_type
                if sfx:
                    sfx.play_item_collect(collected_type)

        self.try_spawn(grid_manager, level, sfx=sfx)

    def _apply_effect(self, item_type: str, player, ghosts) -> None:
        star = (item_type == STAR)
        if item_type == LIGHTNING or star: self._apply_lightning(player)
        if item_type == SNOW      or star: self._apply_snow(ghosts)
        if item_type == SWORD     or star: self._apply_sword(player)
        if item_type == SLIME     or star: self._apply_banana(ghosts)
        if item_type == HEART:             self._apply_heart(player)
        if star:
            self.lightning_timer = 240
            self.snow_timer      = 240
            self.sword_timer     = 240
            self.banana_timer    = 240
            self.star_timer      = 240

    def _apply_sword(self, player) -> None:
        self.sword_timer    = 210
        player.sword_immune = True

    def _restore_player_immunity(self, player) -> None:
        player.sword_immune = False

    def _apply_heart(self, player) -> None:
        player.lives = min(3, player.lives + 1)

    def _apply_lightning(self, player) -> None:
        if not hasattr(player, '_orig_move_delay'):
            player._orig_move_delay = player.move_delay
        player.move_delay    = max(1, player._orig_move_delay // 2)
        self.lightning_timer = 240

    def _restore_player_speed(self, player) -> None:
        if hasattr(player, '_orig_move_delay'):
            player.move_delay = player._orig_move_delay
            del player._orig_move_delay

    def _apply_snow(self, ghosts) -> None:
        for g in ghosts:
            if not hasattr(g, '_orig_speed_snow'):
                g._orig_speed_snow = g.speed
                g._orig_dx_snow    = getattr(g, 'dx', 0)
                g._orig_dy_snow    = getattr(g, 'dy', 0)
            g.ghost_frozen = True
        self.snow_timer = 240

    def _restore_ghost_speeds(self, ghosts, tag: str) -> None:
        attr_speed = f'_orig_speed_{tag}'
        attr_dx    = f'_orig_dx_{tag}'
        attr_dy    = f'_orig_dy_{tag}'
        for g in ghosts:
            if hasattr(g, attr_speed):
                g.speed = getattr(g, attr_speed)
                delattr(g, attr_speed)
            if hasattr(g, attr_dx):
                if hasattr(g, 'dx'): g.dx = getattr(g, attr_dx)
                delattr(g, attr_dx)
            if hasattr(g, attr_dy):
                if hasattr(g, 'dy'): g.dy = getattr(g, attr_dy)
                delattr(g, attr_dy)
            if tag == 'snow':
                g.ghost_frozen = False
            if tag == 'banana':
                for attr in ('_orig_dash_dx_banana', '_orig_dash_dy_banana',
                             '_orig_charge_dx_banana', '_orig_charge_dy_banana'):
                    if hasattr(g, attr):
                        delattr(g, attr)
                if hasattr(g, '_slime_factor'):
                    delattr(g, '_slime_factor')

    def _apply_banana(self, ghosts) -> None:
        factor = 0.35
        for g in ghosts:
            if not hasattr(g, '_orig_speed_banana'):
                g._orig_speed_banana     = g.speed
                g._orig_dx_banana        = getattr(g, 'dx', 0)
                g._orig_dy_banana        = getattr(g, 'dy', 0)
                g._orig_dash_dx_banana   = getattr(g, '_dash_dx', None)
                g._orig_dash_dy_banana   = getattr(g, '_dash_dy', None)
                g._orig_charge_dx_banana = getattr(g, '_charge_dx', None)
                g._orig_charge_dy_banana = getattr(g, '_charge_dy', None)
            g.speed = max(0.1, g._orig_speed_banana * factor)
            if hasattr(g, 'dx') and g._orig_dx_banana != 0:
                g.dx = g._orig_dx_banana * factor
            if hasattr(g, 'dy') and g._orig_dy_banana != 0:
                g.dy = g._orig_dy_banana * factor
            if hasattr(g, '_dash_dx') and g._orig_dash_dx_banana is not None:
                g._dash_dx = g._orig_dash_dx_banana * factor
            if hasattr(g, '_dash_dy') and g._orig_dash_dy_banana is not None:
                g._dash_dy = g._orig_dash_dy_banana * factor
            if hasattr(g, '_charge_dx') and g._orig_charge_dx_banana is not None:
                g._charge_dx = g._orig_charge_dx_banana * factor
            if hasattr(g, '_charge_dy') and g._orig_charge_dy_banana is not None:
                g._charge_dy = g._orig_charge_dy_banana * factor
            g._slime_factor = factor
        self.banana_timer = 480

    def tick_slime(self, ghosts) -> None:
        if not self.banana_active:
            return
        factor = 0.35
        for g in ghosts:
            if not hasattr(g, '_slime_factor'):
                continue
            if hasattr(g, '_dash_dx') and hasattr(g, 'is_dasher'):
                orig_dash_speed = getattr(g, 'DASH_SPEED', 13.0)
                slowed_dash = orig_dash_speed * factor
                mag = (g._dash_dx ** 2 + g._dash_dy ** 2) ** 0.5
                if mag > slowed_dash + 0.01:
                    scale = slowed_dash / mag
                    g._dash_dx *= scale
                    g._dash_dy *= scale
            if hasattr(g, '_charge_dx') and hasattr(g, 'is_watcher'):
                orig_charge_speed = getattr(g, 'CHARGE_SPEED', 11.0)
                slowed_charge = orig_charge_speed * factor
                mag = (g._charge_dx ** 2 + g._charge_dy ** 2) ** 0.5
                if mag > slowed_charge + 0.01:
                    scale = slowed_charge / mag
                    g._charge_dx *= scale
                    g._charge_dy *= scale

    def draw(self, surface, offset_y: int = 0) -> None:
        if self._item is not None:
            self._item.draw(surface, offset_y)

    def draw_hud_effect(self, surface, screen_width: int, hud_height: int) -> None:
        pass  # Badges are now drawn centrally in GameEngine._draw_hud