import pygame
from components.player import Player
from collections import deque

class Scenes:
    """A class that manages a block matrix for rendering scenes.

    The matrix contains only 1s and 0s:
    - 1: renders as a box/block
    - 0: renders as empty space
    - Border is always set to 1
    """

    def __init__(self, width: int, height: int, player: Player, block_size: int = 20):
        """Initialize the scene with given dimensions.

        Args:
            width: Number of columns in the matrix
            height: Number of rows in the matrix
            block_size: Size of each block in pixels (default: 20)
        """
        self.width = width
        self.height = height
        self.block_size = block_size
        self._matrix = self._create_matrix()
        self.player = player
        self.linemove = []
        self._apply_border()
        self.startmove = (-1,-1)

    def _create_matrix(self) -> list[list[int]]:
        """Create a matrix filled with 0s."""
        return [[0 for _ in range(self.width)] for _ in range(self.height)]

    def _apply_border(self) -> None:
        """Set all border cells to 1."""
        for x in range(self.width):
            self._matrix[0][x] = 1  # Top border
            self._matrix[self.height - 1][x] = 1  # Bottom border
        for y in range(self.height):
            self._matrix[y][0] = 1  # Left border
            self._matrix[y][self.width - 1] = 1  # Right border

    def get_matrix(self) -> list[list[int]]:
        """Return the current matrix."""
        return self._matrix

    def set_cell(self, x: int, y: int, value: int) -> None:
        """Set a specific cell value (must be 0 or 1).

        Args:
            x: Column index
            y: Row index
            value: 1 for box, 0 for empty
        """
        if value in (0, 1) and 0 < x < self.width - 1 and 0 < y < self.height - 1:
            self._matrix[y][x] = value

    def get_cell(self, x: int, y: int) -> int:
        """Get the value at a specific cell.

        Args:
            x: Column index
            y: Row index

        Returns:
            1 if box, 0 if empty
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self._matrix[y][x]
        return 1  # Out of bounds treated as wall

    def draw(self, surface, color: tuple = (100, 100, 100)) -> None:
        """Render the matrix to the pygame surface.

        Args:
            surface: Pygame surface to draw on
            color: RGB tuple for block color (default: gray)
        """
        for y, row in enumerate(self._matrix):
            for x, cell in enumerate(row):
                if cell == 1:
                    rect = pygame.Rect(
                        x * self.block_size,
                        y * self.block_size,
                        self.block_size,
                        self.block_size
                    )
                    # Draw filled block
                    pygame.draw.rect(surface, color, rect)
                    # Draw white border around block
                    pygame.draw.rect(surface, (255, 255, 255), rect, 1)
                if cell == 0:
                    rect = pygame.Rect(
                        x * self.block_size,
                        y * self.block_size,
                        self.block_size,
                        self.block_size
                    )
                    
                    # Draw white border around block
                    pygame.draw.rect(surface, (255, 255, 255), rect, 1)
                if cell == 2:
                    rect = pygame.Rect(
                        x * self.block_size,
                        y * self.block_size,
                        self.block_size,
                        self.block_size
                    )
                    # Draw filled block
                    pygame.draw.rect(surface, (0,255,0), rect)
                    # Draw white border around block
                    pygame.draw.rect(surface, (255, 255, 255), rect, 1)

    def check_collision(self, x: int, y: int) -> bool:
        """Check if pixel position collides with a wall (value 1).

        Args:
            x: X pixel position
            y: Y pixel position

        Returns:
            True if collision with wall, False if empty space
        """
        grid_x = x // self.block_size
        grid_y = y // self.block_size
        return self.get_cell(grid_x, grid_y) == 1

    def check_rect_collision(self, x: int, y: int, width: int, height: int) -> bool:
        """Check if a rectangle collides with any wall.

        Checks all corners of the rectangle.

        Args:
            x: X position of rectangle
            y: Y position of rectangle
            width: Width of rectangle
            height: Height of rectangle

        Returns:
            True if any corner collides with wall
        """
        # Check all four corners
        corners = [
            (x, y),
            (x + width - 1, y),
            (x, y + height - 1),
            (x + width - 1, y + height - 1)
        ]
        for cx, cy in corners:
            if self.check_collision(cx, cy):
                return True
        return False

    def reset(self) -> None:
        """Reset matrix to initial state with only borders."""
        self._matrix = self._create_matrix()
        self._apply_border()
        
    def checkPlayer(self) -> None:
        index_x, index_y = self.player.get_grid_position()
        if self._matrix[index_y][index_x] == 0:
            self._matrix[index_y][index_x] = 2
            if self.startmove == (-1,-1):
                print(f"start : {(index_x,index_y)}")
                self.startmove = (index_x,index_y)
            self.linemove.append((index_x,index_y))
        if self._matrix[index_y][index_x] == 1 and self.startmove != (-1,-1):
            self.endmove = (index_x,index_y)
            print(f"end : {(index_x,index_y)}")
            self.floodfill(self.endmove[0],self.endmove[1])
        
        
        # print(index_x,index_y)

    def shortest_path(self):
        rows = len(self._matrix)
        cols = len(self._matrix[0])

        start_x, start_y = self.startmove
        end_x, end_y = self.endmove

        # Directions: up, down, left, right
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        queue = deque()
        queue.append((end_x, end_y, []))

        visited = set()
        visited.add((end_x, end_y))
        line_move_without_start =  self.linemove.copy()
        line_move_without_start.remove(self.startmove)
        print(line_move_without_start)
        while queue:
            x, y, path = queue.popleft()

            if x == start_x and y == start_y:
                print("done")
                return path + [(x, y)]

            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                # print("test" ,nx ,ny)
                if (0 <= nx < cols and 0 <= ny < rows and
                    (nx, ny) not in visited and
                    self._matrix[ny][nx] != 0 and (nx, ny) not in line_move_without_start):  
                    print(nx,ny)
                    visited.add((nx, ny))
                    queue.append((nx, ny, path + [(x, y)]))

        return []  # 
    
    def floodfill(self, index_x, index_y) -> None:
        rows = len(self._matrix)
        cols = len(self._matrix[0])

        
        
        shortest_path = self.shortest_path() 
        # find path shorther path to end startmove to endmove with 1 bfs   
        
        print(shortest_path)
        
        for x,y in self.linemove:
            self._matrix[y][x] = 1
            
        border =  self.linemove + shortest_path
        print(border)
        

        min_x = float("inf")
        min_y = float("inf")
        max_x = float("-inf")
        max_y = float("-inf")

        for x, y in border:
            if x > max_x:
                max_x = x
            if x < min_x:
                min_x = x
            if y > max_y:
                max_y = y
            if y < min_y:
                min_y = y
        
        print(max_x,min_x ,max_y ,min_y)
        
        border = set(border)


        queue = []

        for x in range(min_x - 1, max_x + 1):
            queue.append((x, min_y - 1))
            queue.append((x, max_y + 1))
        for y in range(min_y - 1, max_y + 1):
            queue.append((min_x - 1, y))
            queue.append((max_x + 1, y))

        # หาพื่นที่นอกกรอบเเล้วค่อยระบาบ
        border_set = set(border)
        visited_outside = set(queue)

        while queue:
            curr_x, curr_y = queue.pop(0)
            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]:
                nx, ny = curr_x + dx, curr_y + dy
                if (min_x - 1 <= nx <= max_x + 1 and 
                    min_y - 1 <= ny <= max_y + 1 and 
                    (nx, ny) not in border_set and 
                    (nx, ny) not in visited_outside):
                    
                    visited_outside.add((nx, ny))
                    queue.append((nx, ny))

        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                if (x, y) not in visited_outside and (x, y) not in border_set:
                    self._matrix[y][x] = 1

        self.startmove = (-1,-1)
        self.linemove.clear()