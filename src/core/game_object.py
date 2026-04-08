from abc import ABC, abstractmethod


class GameObject(ABC):
    """Abstract base class for all entities in the game.

    Provides position, color, and speed attributes along with
    abstract update and draw methods.
    """

    def __init__(self, x: float = 0, y: float = 0, color: tuple = (255, 255, 255), speed: float = 1.0):
        """Initialize game object.

        Args:
            x: Horizontal position (default: 0)
            y: Vertical position (default: 0)
            color: Sprite color as RGB tuple (default: white)
            speed: Movement speed (default: 1.0)
        """
        self.x = x
        self.y = y
        self.color = color
        self.speed = speed

    @abstractmethod
    def update(self) -> None:
        """Update object state.

        Called each frame to update the object's state.
        """
        pass

    @abstractmethod
    def draw(self, surface) -> None:
        """Render object on screen.

        Args:
            surface: Pygame surface to draw on
        """
        pass