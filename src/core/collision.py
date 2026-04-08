from abc import ABC, abstractmethod


class Collision(ABC):
    """Interface for collision detection.

    Defines the contract for objects that can detect collisions.
    """

    @abstractmethod
    def is_collision(self, x: int, y: int) -> bool:
        """Check if position collides with this object.

        Args:
            x: X position to check
            y: Y position to check

        Returns:
            True if collision detected, False otherwise
        """
        pass