import numpy as np
from functools import lru_cache

class ZobristHash:
    def __init__(self, board_size=19) -> None:
        np.random.seed(0)
        self.table = np.random.randint(1, 2**63 - 1, size=(board_size + 2, board_size + 2, 3), dtype=np.int64)
        
    def hash_position(self, board) -> int:
        """Compute the Zobrist hash for the current board position"""
        hash_val = 0
        board_size = board.shape[0] - 2  # Account for the border
        for y in range(1, board_size + 1):
            for x in range(1, board_size + 1):
                stone = board[y, x]
                if stone > 0:  hash_val ^= self.table[y, x, stone - 1]
        return hash_val

def get_adjacent_points(y:int, x:int, board_size:int) -> list[tuple[int, int]]:
    """Get the coordinates of adjacent points (up, right, down, left)"""
    directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    adjacent = []
    for dy, dx in directions:
        ny, nx = y + dy, x + dx
        if 1 <= ny <= board_size and 1 <= nx <= board_size: adjacent.append((ny, nx))
    return adjacent

@lru_cache(maxsize=4096)
def get_manhattan_distance(p1:tuple[int, int], p2:tuple[int, int]) -> int:
    """Calculate the Manhattan distance between two points"""
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

def coord_to_sgf(y:int, x:int, board_size:int) -> str:
    """Convert board coordinates to SGF format"""
    col = chr(ord('a') + x - 1)
    row = chr(ord('a') + board_size - y)
    return col + row

def sgf_to_coord(sgf:str, board_size:int) -> tuple[int, int]:
    """Convert SGF format to board coordinates"""
    col = ord(sgf[0]) - ord('a') + 1
    row = board_size - (ord(sgf[1]) - ord('a'))
    return row, col

def coord_to_gtp(y:int, x:int, board_size:int) -> str:
    """Convert board coordinates to GTP format"""
    col_letters = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
    col = col_letters[x - 1]
    row = board_size - y + 1
    return col + str(row)

def gtp_to_coord(gtp:str, board_size:int) -> tuple[int, int]:
    """Convert GTP format to board coordinates"""
    col_letters = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
    col = col_letters.index(gtp[0]) + 1
    row = board_size - int(gtp[1:]) + 1
    return row, col 