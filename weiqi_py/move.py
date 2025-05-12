"""
Move representation and move stack management for Weiqi (Go) game.

This module provides classes for representing moves and managing move history
with undo/redo functionality.
"""

from copy import deepcopy
from typing import Optional, List, Tuple, Set
from .board import BLACK, WHITE, EMPTY, DIRECTIONS, GoError

class MoveError(GoError):
    """Base exception for move-related errors."""
    pass

class Move:
    """
    Represents a single move in the game.
    
    A move can be a stone placement, pass, or resignation.
    """
    
    def __init__(self, y: Optional[int] = None, x: Optional[int] = None, 
                 color: Optional[int] = None, is_pass: bool = False, 
                 is_resign: bool = False) -> None:
        """
        Initialize a move.
        
        Args:
            y (Optional[int]): Row coordinate for stone placement
            x (Optional[int]): Column coordinate for stone placement
            color (Optional[int]): Color of the stone (BLACK or WHITE)
            is_pass (bool): Whether this is a pass move
            is_resign (bool): Whether this is a resignation
            
        Raises:
            ValueError: If move parameters are invalid
        """
        if color is not None and color not in [BLACK, WHITE]:
            raise ValueError(f"Invalid color: {color}. Must be BLACK or WHITE.")
        if is_pass and is_resign:
            raise ValueError("Move cannot be both pass and resign")
        if not is_pass and not is_resign and (y is None or x is None):
            raise ValueError("Stone placement moves must have coordinates")
            
        self.y = y
        self.x = x
        self.color = color
        self.is_pass = is_pass
        self.is_resign = is_resign
        self.captured_stones: List[Tuple[int, int]] = []
        self.previous_zobrist_hash: Optional[int] = None
        self.previous_position_history: Optional[Set[int]] = None
        
    def __str__(self) -> str:
        """
        String representation of the move.
        
        Returns:
            str: Human-readable move description
        """
        if self.is_pass:
            return f"{'Black' if self.color == BLACK else 'White'} Pass"
        elif self.is_resign:
            return f"{'Black' if self.color == BLACK else 'White'} Resign"
        else:
            return f"{'Black' if self.color == BLACK else 'White'} ({self.y},{self.x})"

class MoveStack:
    """
    Stack-based representation of moves for efficient game state management.
    
    This class maintains a history of moves and provides methods to traverse
    the move history, supporting undo/redo operations.
    """
    
    def __init__(self, board) -> None:
        """
        Initialize a move stack.
        
        Args:
            board: The game board to operate on
        """
        self.board = board
        self.moves: List[Move] = []
        self.current_index = -1
        
    def push(self, move: Move) -> bool:
        """
        Push a move onto the stack and apply it to the board.
        
        Args:
            move (Move): The move to push
            
        Returns:
            bool: True if the move was successfully applied
            
        Raises:
            MoveError: If the move cannot be applied
        """
        # Store current state for potential undo
        move.previous_zobrist_hash = self.board.current_hash
        move.previous_position_history = deepcopy(self.board.position_history)
        
        # Handle pass and resign moves
        if move.is_pass or move.is_resign:
            self.moves = self.moves[:self.current_index + 1]
            self.moves.append(move)
            self.current_index += 1
            return True
            
        # Check for potential captures
        opponent = WHITE if move.color == BLACK else BLACK
        potential_captures: List[Tuple[int, int]] = []
        temp_board = self.board.board.copy()
        temp_board[move.y, move.x] = move.color
        
        # Find groups that would be captured
        for dy, dx in DIRECTIONS:
            ny, nx = move.y + dy, move.x + dx
            if 1 <= ny <= self.board.size and 1 <= nx <= self.board.size:
                if temp_board[ny, nx] == opponent:
                    group = self.board._get_group(ny, nx)
                    liberties = self.board._get_liberties(group)
                    if len(liberties) == 1 and (move.y, move.x) in liberties:
                        potential_captures.extend(group)
                        
        try:
            # Apply the move
            if not self.board.place_stone(move.y, move.x, move.color):
                raise MoveError(f"Invalid move at ({move.y}, {move.x})")
                
            # Record captured stones
            for y, x in potential_captures:
                if self.board.board[y, x] == EMPTY:
                    move.captured_stones.append((y, x))
                    
            # Update move stack
            self.moves = self.moves[:self.current_index + 1]
            self.moves.append(move)
            self.current_index += 1
            return True
        except GoError as e:
            raise MoveError(str(e))
        
    def pop(self) -> Optional[Move]:
        """
        Pop a move from the stack and undo it on the board.
        
        Returns:
            Optional[Move]: The popped move, or None if stack is empty
            
        Raises:
            MoveError: If there is an error undoing the move
        """
        if self.current_index < 0:
            return None
            
        move = self.moves[self.current_index]
        self.current_index -= 1
        
        if move.is_pass or move.is_resign:
            return move
            
        try:
            # Undo the move
            self.board.board[move.y, move.x] = EMPTY
            opponent = WHITE if move.color == BLACK else BLACK
            
            # Restore captured stones
            for y, x in move.captured_stones:
                self.board.board[y, x] = opponent
                
            # Restore previous state
            self.board.current_hash = move.previous_zobrist_hash
            self.board.position_history = move.previous_position_history
            
            return move
        except Exception as e:
            raise MoveError(f"Error undoing move: {e}")
        
    def peek(self) -> Optional[Move]:
        """
        Peek at the current move without popping.
        
        Returns:
            Optional[Move]: The current move, or None if stack is empty
        """
        if self.current_index < 0:
            return None
        return self.moves[self.current_index]
        
    def peek_next(self) -> Optional[Move]:
        """
        Peek at the next move without pushing.
        
        Returns:
            Optional[Move]: The next move, or None if at end of stack
        """
        if self.current_index + 1 >= len(self.moves):
            return None
        return self.moves[self.current_index + 1]
        
    def forward(self) -> bool:
        """
        Move forward in the move stack (redo).
        
        Returns:
            bool: True if successful
            
        Raises:
            MoveError: If there is an error redoing the move
        """
        if self.current_index + 1 >= len(self.moves):
            return False
            
        next_move = self.moves[self.current_index + 1]
        if next_move.is_pass or next_move.is_resign:
            self.current_index += 1
            return True
            
        try:
            # Apply the move
            self.board.board[next_move.y, next_move.x] = next_move.color
            self.board.current_hash = next_move.previous_zobrist_hash
            self.board.current_hash ^= self.board.zobrist_table[next_move.y, next_move.x, next_move.color - 1]
            
            # Handle captures
            opponent = WHITE if next_move.color == BLACK else BLACK
            for y, x in next_move.captured_stones:
                self.board.board[y, x] = EMPTY
                self.board.current_hash ^= self.board.zobrist_table[y, x, opponent - 1]
                
            self.board.position_history = deepcopy(next_move.previous_position_history)
            self.board.position_history.add(self.board.current_hash)
            self.current_index += 1
            return True
        except Exception as e:
            raise MoveError(f"Error redoing move: {e}")
        
    def back(self) -> bool:
        """
        Move backward in the move stack (undo).
        
        Returns:
            bool: True if successful
            
        Raises:
            MoveError: If there is an error undoing the move
        """
        return self.pop() is not None
        
    def to_root(self) -> None:
        """
        Undo all moves and return to the root state.
        
        Raises:
            MoveError: If there is an error undoing moves
        """
        while self.pop() is not None:
            pass
        
    def to_end(self) -> None:
        """
        Redo all moves and go to the end of the stack.
        
        Raises:
            MoveError: If there is an error redoing moves
        """
        while self.forward():
            pass
        
    def __len__(self) -> int:
        """
        Return the total number of moves in the stack.
        
        Returns:
            int: Number of moves
        """
        return len(self.moves)
        
    def current_position(self) -> int:
        """
        Return the current position in the stack.
        
        Returns:
            int: Current position (1-based)
        """
        return self.current_index + 1 