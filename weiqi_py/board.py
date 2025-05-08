import numpy as np
from functools import lru_cache
from collections import deque

EMPTY = 0
BLACK = 1
WHITE = 2
OFFBOARD = 3  # Used for padding
DIRECTIONS = [(-1, 0), (0, 1), (1, 0), (0, -1)]

class Board:
    def __init__(self, size=19) -> None:
        self.size = size
        self.board = np.zeros((size + 2, size + 2), dtype=np.int8)
        self.board[0, :] = self.board[-1, :] = OFFBOARD
        self.board[:, 0] = self.board[:, -1] = OFFBOARD
        self.black_captures = 0
        self.white_captures = 0
        self.position_history = set()
        # Initialize Zobrist hash table for fast position hashing
        np.random.seed(0)
        self.zobrist_table = np.random.randint(1, 2**63 - 1, size=(size + 2, size + 2, 3), dtype=np.int64)
        self.current_hash = 0
        self._update_position_hash()  # Now call this after initializing the hash table
        
    def _update_position_hash(self) -> None:
        """Update and store the current board position hash"""
        self.current_hash = 0
        for y in range(1, self.size + 1):
            for x in range(1, self.size + 1):
                stone = self.board[y, x]
                if stone > 0: self.current_hash ^= self.zobrist_table[y, x, stone - 1]
        self.position_history.add(self.current_hash)
    
    def reset(self) -> None:
        """Reset the board to an empty state"""
        self.board[1:-1, 1:-1] = EMPTY
        self.black_captures = 0
        self.white_captures = 0
        self.position_history = set()
        self.current_hash = 0
        self._update_position_hash()
    
    def _get_group(self, y: int, x: int) -> set[tuple[int, int]]:
        """Find all connected stones of the same color"""
        color = self.board[y, x]
        if color == EMPTY or color == OFFBOARD: return set()
        visited = set()
        queue = deque([(y, x)])
        while queue:
            cy, cx = queue.popleft()
            if (cy, cx) in visited: continue
            visited.add((cy, cx))
            for dy, dx in DIRECTIONS:
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < self.size + 2 and 0 <= nx < self.size + 2:
                    if (self.board[ny, nx] == color and (ny, nx) not in visited): queue.append((ny, nx))
        return visited
    
    @lru_cache(maxsize=4096)
    def _get_liberties(self, group: frozenset[tuple[int, int]]) -> set[tuple[int, int]]:
        """Count the liberties (empty adjacent points) of a group"""
        liberties = set()
        for y, x in group:
            for dy, dx in DIRECTIONS:
                ny, nx = y + dy, x + dx
                if 0 <= ny < self.size + 2 and 0 <= nx < self.size + 2: 
                    if self.board[ny, nx] == EMPTY: liberties.add((ny, nx))
        return liberties
    
    def is_valid_move(self, y: int, x: int, color: int) -> bool:
        """Check if placing a stone at (y, x) is a valid move"""
        if not (1 <= y <= self.size and 1 <= x <= self.size): return False
        if self.board[y, x] != EMPTY: return False            
        temp_board = self.board.copy()
        temp_board[y, x] = color
        opponent = WHITE if color == BLACK else BLACK
        captured_groups = []
        for dy, dx in DIRECTIONS:
            ny, nx = y + dy, x + dx
            if temp_board[ny, nx] == opponent:
                group = self._get_group(ny, nx)
                liberties = self._get_liberties(frozenset(group))
                if not liberties:captured_groups.append(group)
        for group in captured_groups:
            for gy, gx in group: temp_board[gy, gx] = EMPTY
        group = set()
        queue = deque([(y, x)])
        while queue:
            cy, cx = queue.popleft()
            if (cy, cx) in group: continue
            group.add((cy, cx))
            for dy, dx in DIRECTIONS:
                ny, nx = cy + dy, cx + dx
                if temp_board[ny, nx] == color and (ny, nx) not in group: queue.append((ny, nx))
        has_liberties = False
        for gy, gx in group:
            for dy, dx in DIRECTIONS:
                ny, nx = gy + dy, gx + dx
                if temp_board[ny, nx] == EMPTY:
                    has_liberties = True
                    break
            if has_liberties: break
        if not has_liberties and not captured_groups: return False
        # Check for positional superko - calculate the new board position hash
        new_hash = self.current_hash ^ self.zobrist_table[y, x, color - 1]
        for group in captured_groups:
            for gy, gx in group: new_hash ^= self.zobrist_table[gy, gx, opponent - 1]
        if new_hash in self.position_history: return False  # Violates positional superko rule
        return True
    
    def place_stone(self, y: int, x: int, color: int) -> bool:
        """Place a stone on the board and handle captures"""
        if not self.is_valid_move(y, x, color): return False
        self.board[y, x] = color # Place the stone
        self.current_hash ^= self.zobrist_table[y, x, color - 1] # Update Zobrist hash
        opponent = WHITE if color == BLACK else BLACK # Check for captures
        captured_stones = 0
        for dy, dx in DIRECTIONS: # Check adjacent groups for captures
            ny, nx = y + dy, x + dx
            if self.board[ny, nx] == opponent:
                group = self._get_group(ny, nx)
                liberties = self._get_liberties(frozenset(group))
                if not liberties:
                    for gy, gx in group:
                        # Update Zobrist hash by removing stones
                        self.current_hash ^= self.zobrist_table[gy, gx, opponent - 1]
                        self.board[gy, gx] = EMPTY
                    captured_stones += len(group)
        if color == BLACK: self.black_captures += captured_stones
        else: self.white_captures += captured_stones
        self.position_history.add(self.current_hash) # Update position history for ko detection
        self._get_liberties.cache_clear() # Clear LRU cache since the board has changed
        return True
    
    def get_legal_moves(self, color: int) -> list[tuple[int, int]]:
        """Get all legal moves for the current player"""
        legal_moves = []
        for y in range(1, self.size + 1):
            for x in range(1, self.size + 1):
                if self.is_valid_move(y, x, color): legal_moves.append((y, x))
        return legal_moves
    
    def __str__(self) -> str:
        """String representation of the board for display"""
        result = ""
        for y in range(1, self.size + 1):
            for x in range(1, self.size + 1):
                if self.board[y, x] == EMPTY: result += ". "
                elif self.board[y, x] == BLACK: result += "B "
                elif self.board[y, x] == WHITE: result += "W "
            result += "\n"
        return result