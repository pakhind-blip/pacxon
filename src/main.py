import pygame
import sys
from core.game_engine import GameEngine, MENU, PLAY, GAME_OVER

def main():
    pygame.init()
    SCREEN_WIDTH  = 800
    SCREEN_HEIGHT = 600
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("PyXon")
    clock = pygame.time.Clock()
    GameEngine().run(screen, clock, SCREEN_WIDTH, SCREEN_HEIGHT)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()