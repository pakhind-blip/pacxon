import pygame
import sys
from core.game_engine import GameEngine

def main():
    pygame.init()

    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("PACXON")
    clock = pygame.time.Clock()
    game_engine = GameEngine()
    game_engine.run(screen, clock, SCREEN_WIDTH, SCREEN_HEIGHT)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()