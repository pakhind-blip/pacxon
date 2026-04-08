import pygame
import sys

from core.scenes import Scenes
from core.collision import Collision
from components.player import Player


def main():
    # Initialize Pygame
    pygame.init()

    # Screen settings
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    BLOCK_SIZE = 20

    # Create screen
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("PACXON")
    clock = pygame.time.Clock()

    # Calculate grid dimensions
    grid_width = SCREEN_WIDTH // BLOCK_SIZE
    grid_height = SCREEN_HEIGHT // BLOCK_SIZE



    # Create player at starting position (0, 0)
    player = Player(width=BLOCK_SIZE, height=BLOCK_SIZE, block_size=BLOCK_SIZE)
    player.set_position(0, 0)

    # Create scene (matrix with border walls)
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

        # Get keyboard state
        keys = pygame.key.get_pressed()

        # Update player with collision detection
        player.move_with_collision(keys, scene)
        player.clamp_to_bounds(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Render
        screen.fill((0, 0, 0))  # Black background

        scene.checkPlayer()
        # Draw scene (walls)
        scene.draw(screen, color=(100, 100, 100))

        # Draw player
        player.draw(screen)

        # Update display
        pygame.display.flip()

        # Control frame rate
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()