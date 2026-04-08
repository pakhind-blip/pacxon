from abc import ABC, abstractmethod


class Collision(ABC):

    @abstractmethod
    def is_collision(self, x: int, y: int) -> bool:
        pass