import pygame
import os

class SoundManager:
    def __init__(self, sounds_dir: str = "sound", volume: float = 0.7):
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        self._vol = volume
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._enabled = True

        files = {
            "capture":         "capture.wav",
            "death":           "death.wav",
            "ui_click":        "ui_click.wav",
            "infection_tick":  "infection_tick.wav",
            "level_complete":  "level_complete.wav",
            "game_over":       "game_over.wav",
            "theme":           "theme.wav",       # menu theme
            "game_theme":      "game_theme.wav",  # in-game theme
            "trail":           "trail.wav",
            # ── Item sounds ──────────────────────────────────────────────────
            "item_spawn":      "item_spawn.wav",      # same for all items
            "item_lightning":  "item_lightning.wav",
            "item_snow":       "item_snow.wav",
            "item_sword":      "item_sword.wav",
            "item_slime":      "item_slime.wav",
            "item_heart":      "item_heart.wav",
            "item_star":       "item_star.wav",
        }

        print(f"[SoundManager] Loading from: {os.path.abspath(sounds_dir)}")
        for key, filename in files.items():
            path = os.path.join(sounds_dir, filename)
            if os.path.exists(path):
                snd = pygame.mixer.Sound(path)
                snd.set_volume(volume)
                self._sounds[key] = snd
                print(f"[SoundManager] OK: {filename}")
            else:
                print(f"[SoundManager] MISSING: {os.path.abspath(path)}")

        # Dedicated channels
        self._trail_channel     = pygame.mixer.Channel(0)
        self._infection_channel = pygame.mixer.Channel(1)
        self._theme_channel     = pygame.mixer.Channel(2)

        # Track which theme is currently active
        self._current_theme: str | None = None

    # ── Volume / toggle ──────────────────────────────────────────────────────

    def set_volume(self, v: float):
        self._vol = max(0.0, min(1.0, v))
        for snd in self._sounds.values():
            snd.set_volume(self._vol)

    def toggle(self):
        self._enabled = not self._enabled
        if not self._enabled:
            pygame.mixer.stop()
        else:
            if self._current_theme == "game_theme":
                self.play_game_theme()
            else:
                self.play_menu_theme()

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _play(self, key: str):
        if self._enabled and key in self._sounds:
            self._sounds[key].play()

    def _switch_theme(self, key: str):
        """Stop current theme and start a new one only if it changed."""
        if not self._enabled or key not in self._sounds:
            return
        if self._current_theme == key and self._theme_channel.get_busy():
            return  # already playing the right one
        self._theme_channel.stop()
        self._theme_channel.play(self._sounds[key], loops=-1)
        self._current_theme = key

    # ── SFX ─────────────────────────────────────────────────────────────────

    def play_capture(self):
        self._play("capture")

    def play_death(self):
        if self._enabled and "death" in self._sounds:
            self._infection_channel.stop()
            self._sounds["death"].play()

    def play_ui_click(self):
        self._play("ui_click")

    def play_infection_tick(self):
        if self._enabled and "infection_tick" in self._sounds:
            if not self._infection_channel.get_busy():
                self._infection_channel.play(self._sounds["infection_tick"])

    def play_trail(self):
        if self._enabled and "trail" in self._sounds:
            if not self._trail_channel.get_busy():
                self._trail_channel.play(self._sounds["trail"])

    def play_level_complete(self):
        self._theme_channel.stop()
        self._current_theme = None
        self._play("level_complete")

    def play_game_over(self):
        self._theme_channel.stop()
        self._current_theme = None
        self._play("game_over")

    # ── Themes ───────────────────────────────────────────────────────────────

    def play_menu_theme(self):
        """Play the short looping menu theme (theme.wav)."""
        self._switch_theme("theme")

    def play_game_theme(self):
        """Play the longer in-game theme (game_theme.wav)."""
        self._switch_theme("game_theme")

    def stop_theme(self):
        self._theme_channel.stop()
        self._current_theme = None

    # Legacy alias — any old call to play_theme() plays the menu theme
    def play_theme(self):
        self.play_menu_theme()

    # ── Item sounds ──────────────────────────────────────────────────────────

    def play_item_spawn(self):
        self._play("item_spawn")

    def play_item_collect(self, item_type: str):
        """Play the collect sound for the given item type string."""
        key = f"item_{item_type}"   # e.g. "item_lightning", "item_star"
        self._play(key)