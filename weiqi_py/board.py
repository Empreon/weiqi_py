"""
Core board representation and game logic for Weiqi (Go).

This module provides the fundamental board representation and game logic for Weiqi (Go).
It handles stone placement, capture, and basic game rules while maintaining an efficient
internal representation of the board state.
"""

import numpy as np
from collections import defaultdict
from typing import Optional, Set, Tuple, List, Dict

# Constants for board states
EMPTY = 0
BLACK = 1
WHITE = 2
OFFBOARD = 3
DIRECTIONS = [(-1, 0), (0, 1), (1, 0), (0, -1)]

class GoError(Exception):
    """Base exception for Go-related errors."""
    pass

class InvalidMoveError(GoError):
    """Exception raised for invalid moves."""
    pass

class GroupManager:
    """
    Manages groups and their liberties incrementally.
    
    This class maintains the state of stone groups on the board, tracking their
    members and liberties. It provides efficient operations for group creation,
    merging, and liberty updates.
    """
    def __init__(self, size: int) -> None:
        """
        Initialize a new group manager.
        
        Args:
            size (int): Size of the board
        """
        self.size = size
        self.groups: Dict[Tuple[int, int], int] = {}  # (y, x) -> group_id
        self.group_stones: Dict[int, Set[Tuple[int, int]]] = defaultdict(set)  # group_id -> set of (y, x)
        self.group_liberties: Dict[int, Set[Tuple[int, int]]] = defaultdict(set)  # group_id -> set of (y, x)
        self.next_group_id = 0
        
    def get_group_id(self, y: int, x: int) -> Optional[int]:
        """
        Get the group ID for a stone.
        
        Args:
            y (int): Row coordinate
            x (int): Column coordinate
            
        Returns:
            Optional[int]: Group ID if the point has a stone, None otherwise
        """
        return self.groups.get((y, x))
        
    def get_group_stones(self, group_id: int) -> Set[Tuple[int, int]]:
        """
        Get all stones in a group.
        
        Args:
            group_id (int): ID of the group
            
        Returns:
            Set[Tuple[int, int]]: Set of (y, x) coordinates in the group
            
        Raises:
            KeyError: If group_id doesn't exist
        """
        return self.group_stones[group_id]
        
    def get_group_liberties(self, group_id: int) -> Set[Tuple[int, int]]:
        """
        Get all liberties of a group.
        
        Args:
            group_id (int): ID of the group
            
        Returns:
            Set[Tuple[int, int]]: Set of (y, x) coordinates of liberties
            
        Raises:
            KeyError: If group_id doesn't exist
        """
        return self.group_liberties[group_id]
        
    def create_group(self, y: int, x: int, color: int, board: np.ndarray) -> int:
        """
        Create a new group for a stone.
        
        Args:
            y (int): Row coordinate
            x (int): Column coordinate
            color (int): Color of the stone (BLACK or WHITE)
            board (np.ndarray): Current board state
            
        Returns:
            int: ID of the created group
        """
        group_id = self.next_group_id
        self.next_group_id += 1
        self.groups[(y, x)] = group_id
        self.group_stones[group_id].add((y, x))
        
        # Calculate liberties directly for the new stone
        liberties = set()
        for dy, dx in DIRECTIONS:
            ny, nx = y + dy, x + dx
            if 1 <= ny <= self.size and 1 <= nx <= self.size and board[ny, nx] == EMPTY:
                liberties.add((ny, nx))
        self.group_liberties[group_id] = liberties
        return group_id
        
    def merge_groups(self, group_ids: Set[int], new_stone: Tuple[int, int], board: np.ndarray) -> int:
        """
        Merge multiple groups into one, properly handling liberties.
        
        Args:
            group_ids (Set[int]): Set of group IDs to merge
            new_stone (Tuple[int, int]): (y, x) coordinates of the newly placed stone
            board (np.ndarray): Current board state
            
        Returns:
            int: ID of the merged group
            
        Raises:
            ValueError: If group_ids is empty
        """
        if not group_ids:
            raise ValueError("Cannot merge empty set of groups")
            
        # Use the smallest group ID as the new group ID
        new_group_id = min(group_ids)
        all_stones = set()
        all_liberties = set()
        
        # Collect all stones and liberties
        for group_id in group_ids:
            all_stones.update(self.group_stones[group_id])
            all_liberties.update(self.group_liberties[group_id])
            if group_id != new_group_id:
                del self.group_stones[group_id]
                del self.group_liberties[group_id]
                
        # Add the new stone
        all_stones.add(new_stone)
        
        # Remove the new stone from liberties
        all_liberties.discard(new_stone)
        
        # Add any new liberties from the new stone
        y, x = new_stone
        for dy, dx in DIRECTIONS:
            ny, nx = y + dy, x + dx
            if 1 <= ny <= self.size and 1 <= nx <= self.size and board[ny, nx] == EMPTY:
                all_liberties.add((ny, nx))
                
        # Update group data
        self.group_stones[new_group_id] = all_stones
        self.group_liberties[new_group_id] = all_liberties
        
        # Update stone-to-group mapping
        for y, x in all_stones:
            self.groups[(y, x)] = new_group_id
            
        return new_group_id
        
    def remove_group(self, group_id: int) -> None:
        """
        Remove a group and its data.
        
        Args:
            group_id (int): ID of the group to remove
            
        Raises:
            KeyError: If group_id doesn't exist
        """
        for y, x in self.group_stones[group_id]:
            del self.groups[(y, x)]
        del self.group_stones[group_id]
        del self.group_liberties[group_id]
        
    def update_adjacent_liberties(self, y: int, x: int, color: int, board: np.ndarray) -> None:
        """
        Update liberties of adjacent groups after a stone is placed.
        
        Args:
            y (int): Row coordinate of placed stone
            x (int): Column coordinate of placed stone
            color (int): Color of the placed stone (BLACK or WHITE)
            board (np.ndarray): Current board state
        """
        opponent = WHITE if color == BLACK else BLACK
        affected_groups = set()
        
        # Find all affected groups
        for dy, dx in DIRECTIONS:
            ny, nx = y + dy, x + dx
            if 1 <= ny <= self.size and 1 <= nx <= self.size:
                group_id = self.get_group_id(ny, nx)
                if group_id is not None:
                    affected_groups.add(group_id)
                    
        # Update liberties for each affected group
        for group_id in affected_groups:
            # Remove the placed stone from liberties
            self.group_liberties[group_id].discard((y, x))
            
            # If this is an opponent group, check if it's captured
            if board[y, x] == opponent:
                if not self.group_liberties[group_id]:
                    self.remove_group(group_id)
            # If this is a friendly group, add any new liberties from the placed stone
            elif board[y, x] == color:
                for dy, dx in DIRECTIONS:
                    ny, nx = y + dy, x + dx
                    if 1 <= ny <= self.size and 1 <= nx <= self.size and board[ny, nx] == EMPTY:
                        self.group_liberties[group_id].add((ny, nx))

class Board:
    """
    Represents a Weiqi (Go) board with game logic.
    
    The board uses a numpy array with padding for efficient boundary checking.
    Coordinates are 1-based for the actual board area, with 0 and size+1 being
    the padding areas marked as OFFBOARD.
    """
    
    def __init__(self, size: int = 19) -> None:
        """
        Initialize a new board.
        
        Args:
            size (int): Board size (default: 19)
            
        Raises:
            ValueError: If size is invalid (must be between 5 and 25)
        """
        if not 5 <= size <= 25:
            raise ValueError("Board size must be between 5 and 25")
            
        self.size = size
        # Initialize board with padding for boundary checking
        self.board = np.zeros((size + 2, size + 2), dtype=np.int8)
        self.board[0, :] = self.board[-1, :] = OFFBOARD
        self.board[:, 0] = self.board[:, -1] = OFFBOARD
        
        # Game state tracking
        self.black_captures = 0
        self.white_captures = 0
        self.position_history = set()
        
        # Initialize Zobrist hashing for position tracking
        np.random.seed(0)
        self.zobrist_table = np.random.randint(1, 2**63 - 1, size=(size + 2, size + 2, 3), dtype=np.int64)
        self.current_hash = 0
        
        # Initialize group manager
        self.group_manager = GroupManager(size)
        self._update_position_hash()

    def _update_position_hash(self) -> None:
        """
        Update the Zobrist hash for the current board position.
        
        This method calculates a unique hash for the current board state,
        which is used for detecting repeated positions (ko rule).
        """
        self.current_hash = 0
        for y in range(1, self.size + 1):
            for x in range(1, self.size + 1):
                stone = self.board[y, x]
                if stone > 0: 
                    self.current_hash ^= self.zobrist_table[y, x, stone - 1]
        self.position_history.add(self.current_hash)

    def reset(self) -> None:
        """
        Reset the board to its initial empty state.
        
        This method clears all stones, resets capture counts, and reinitializes
        the group manager and position history.
        """
        self.board[1:-1, 1:-1] = EMPTY
        self.black_captures = 0
        self.white_captures = 0
        self.position_history = set()
        self.current_hash = 0
        self.group_manager = GroupManager(self.size)
        self._update_position_hash()

    def _analyze_move(self, y: int, x: int, color: int) -> Tuple[bool, str, Set[int], Set[Tuple[int, int]]]:
        """
        Analyze a move without modifying the board.
        
        This method checks if a move is valid and calculates its consequences
        (captures, liberties) without actually making the move.
        
        Args:
            y (int): Row coordinate
            x (int): Column coordinate
            color (int): Color of the stone (BLACK or WHITE)
            
        Returns:
            Tuple[bool, str, Set[int], Set[Tuple[int, int]]]: 
                (is_valid, reason, captured_groups, new_group_liberties)
        """
        # Basic move validation
        if not (1 <= y <= self.size and 1 <= x <= self.size):
            return False, "out of bounds", set(), set()
        if self.board[y, x] != EMPTY:
            return False, "position already occupied", set(), set()

        opponent = WHITE if color == BLACK else BLACK
        captured_groups = set()
        adjacent_groups = set()
        new_liberties = set()

        # Check adjacent points
        for dy, dx in DIRECTIONS:
            ny, nx = y + dy, x + dx
            if 1 <= ny <= self.size and 1 <= nx <= self.size:
                if self.board[ny, nx] == EMPTY:
                    new_liberties.add((ny, nx))
                elif self.board[ny, nx] == opponent:
                    group_id = self.group_manager.get_group_id(ny, nx)
                    if group_id is not None:
                        # Check if this move would capture the group
                        if len(self.group_manager.get_group_liberties(group_id)) == 1:
                            captured_groups.add(group_id)
                elif self.board[ny, nx] == color:
                    group_id = self.group_manager.get_group_id(ny, nx)
                    if group_id is not None:
                        adjacent_groups.add(group_id)

        # Check for suicide
        if not new_liberties and not captured_groups:
            return False, "suicide move", set(), set()

        # Check for ko rule violation
        new_hash = self.current_hash ^ self.zobrist_table[y, x, color - 1]
        for group_id in captured_groups:
            for gy, gx in self.group_manager.get_group_stones(group_id):
                new_hash ^= self.zobrist_table[gy, gx, opponent - 1]
        if new_hash in self.position_history:
            return False, "ko rule violation", set(), set()

        return True, "", captured_groups, new_liberties

    def is_valid_move(self, y: int, x: int, color: int) -> Tuple[bool, str]:
        """
        Check if placing a stone at (y, x) is a valid move.
        
        Args:
            y (int): Row coordinate
            x (int): Column coordinate
            color (int): Color of the stone (BLACK or WHITE)
            
        Returns:
            Tuple[bool, str]: (is_valid, reason) where reason is empty if valid
            
        Raises:
            ValueError: If coordinates or color are invalid
        """
        if not isinstance(y, int) or not isinstance(x, int):
            raise ValueError("Coordinates must be integers")
        if color not in (BLACK, WHITE):
            raise ValueError("Color must be BLACK or WHITE")
            
        is_valid, reason, _, _ = self._analyze_move(y, x, color)
        return is_valid, reason

    def place_stone(self, y: int, x: int, color: int) -> bool:
        """
        Place a stone on the board and handle captures.
        
        Args:
            y (int): Row coordinate
            x (int): Column coordinate
            color (int): Color of the stone (BLACK or WHITE)
            
        Returns:
            bool: True if the move was successful
            
        Raises:
            InvalidMoveError: If the move is invalid
            ValueError: If coordinates or color are invalid
        """
        if not isinstance(y, int) or not isinstance(x, int):
            raise ValueError("Coordinates must be integers")
        if color not in (BLACK, WHITE):
            raise ValueError("Color must be BLACK or WHITE")
            
        is_valid, reason, captured_groups, _ = self._analyze_move(y, x, color)
        if not is_valid:
            raise InvalidMoveError(f"Invalid move at ({y}, {x}): {reason}")

        opponent = WHITE if color == BLACK else BLACK
        captured_stones = 0

        # Remove captured groups
        for group_id in captured_groups:
            for gy, gx in self.group_manager.get_group_stones(group_id):
                self.board[gy, gx] = EMPTY
                self.current_hash ^= self.zobrist_table[gy, gx, opponent - 1]
                captured_stones += 1
            self.group_manager.remove_group(group_id)

        # Place the stone
        self.board[y, x] = color
        self.current_hash ^= self.zobrist_table[y, x, color - 1]

        # Create or merge groups
        adjacent_groups = set()
        for dy, dx in DIRECTIONS:
            ny, nx = y + dy, x + dx
            if 1 <= ny <= self.size and 1 <= nx <= self.size and self.board[ny, nx] == color:
                group_id = self.group_manager.get_group_id(ny, nx)
                if group_id is not None:
                    adjacent_groups.add(group_id)

        if adjacent_groups:
            self.group_manager.merge_groups(adjacent_groups, (y, x), self.board)
        else:
            self.group_manager.create_group(y, x, color, self.board)

        # Update liberties of adjacent groups
        self.group_manager.update_adjacent_liberties(y, x, color, self.board)

        # Update capture counts
        if color == BLACK:
            self.black_captures += captured_stones
        else:
            self.white_captures += captured_stones

        self.position_history.add(self.current_hash)
        return True

    def get_legal_moves(self, color: int) -> List[Tuple[int, int]]:
        """
        Get all legal moves for the current player.
        
        Args:
            color (int): Color of the player (BLACK or WHITE)
            
        Returns:
            List[Tuple[int, int]]: List of valid move coordinates
            
        Raises:
            ValueError: If color is invalid
        """
        if color not in (BLACK, WHITE):
            raise ValueError("Color must be BLACK or WHITE")
            
        legal_moves = []
        # Only check empty intersections
        for y in range(1, self.size + 1):
            for x in range(1, self.size + 1):
                if self.board[y, x] == EMPTY:
                    # Quick check for adjacent stones or liberties
                    has_adjacent = False
                    for dy, dx in DIRECTIONS:
                        ny, nx = y + dy, x + dx
                        if 1 <= ny <= self.size and 1 <= nx <= self.size:
                            if self.board[ny, nx] != EMPTY:
                                has_adjacent = True
                                break
                    # Only do full validation if there are adjacent stones
                    if has_adjacent:
                        is_valid, _ = self.is_valid_move(y, x, color)
                        if is_valid:
                            legal_moves.append((y, x))
                    else:
                        # If no adjacent stones, move is valid unless it's a ko violation
                        new_hash = self.current_hash ^ self.zobrist_table[y, x, color - 1]
                        if new_hash not in self.position_history:
                            legal_moves.append((y, x))
        return legal_moves

    def __str__(self) -> str:
        """
        String representation of the board for display.
        
        Returns:
            str: Board representation with B for black, W for white, and . for empty
        """
        result = ""
        for y in range(1, self.size + 1):
            for x in range(1, self.size + 1):
                if self.board[y, x] == EMPTY:
                    result += ". "
                elif self.board[y, x] == BLACK:
                    result += "B "
                elif self.board[y, x] == WHITE:
                    result += "W "
            result += "\n"
        return result