import pygame
import sys

from core.scenes import Scenes
from core.collision import Collision
from components.player import Player


def main():
    pygame.init()

    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    BLOCK_SIZE = 20

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("PACXON")
    clock = pygame.time.Clock()

    grid_width = SCREEN_WIDTH // BLOCK_SIZE
    grid_height = SCREEN_HEIGHT // BLOCK_SIZE

    player = Player(width=BLOCK_SIZE, height=BLOCK_SIZE, block_size=BLOCK_SIZE)
    player.set_position(0, 0)

    scene = Scenes(grid_width, grid_height, player, BLOCK_SIZE)
    running = True
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    # Reset scene
                    scene.reset()
                    player.set_position(0, 0)

        keys = pygame.key.get_pressed()

        player.move_with_collision(keys, scene)
        player.clamp_to_bounds(SCREEN_WIDTH, SCREEN_HEIGHT)

        screen.fill((0, 0, 0))  # Black background

        scene.checkPlayer()
        scene.draw(screen, color=(100, 100, 100))

        player.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()