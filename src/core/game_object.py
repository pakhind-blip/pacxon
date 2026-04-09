from abc import ABC, abstractmethod

class GameObject(ABC):
    def __init__(self, x: float = 0, y: float = 0, color: tuple = (255, 255, 255), speed: float = 1.0):
        self.x = x
        self.y = y
        self.color = color
        self.speed = speed

    @abstractmethod
    def update(self) -> None: pass

    @abstractmethod
    def draw(self, surface) -> None: pass