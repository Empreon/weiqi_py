"""
Core game logic and state management for Weiqi (Go).

This module provides the main game interface, handling move validation,
scoring, and game state management.
"""

import numpy as np
from collections import deque
from typing import Optional, List, Tuple
from .board import Board, BLACK, WHITE, EMPTY, GoError
from .move import Move, MoveStack

class GameError(GoError): 
    """Base exception for game-related errors."""
    pass

class InvalidMoveError(GameError): 
    """Exception raised for invalid moves."""
    pass

class ScoringError(GameError): 
    """Exception raised for scoring-related errors."""
    pass

class Game:
    """
    Represents a complete Weiqi (Go) game.
    
    This class manages the game state, including the board, moves, scoring,
    and game rules enforcement.
    """
    
    def __init__(self, board_size: int = 19, komi: float = 6.5, score_system: str = "area") -> None:
        """
        Initialize a new game.
        
        Args:
            board_size (int): Size of the board (default: 19)
            komi (float): Komi value for white (default: 6.5)
            score_system (str): Scoring system to use ("area" or "territory")
            
        Raises:
            ValueError: If parameters are invalid
        """
        if not isinstance(board_size, int) or board_size < 5 or board_size > 25:
            raise ValueError(f"Invalid board size: {board_size}. Must be between 5 and 25.")
        if not isinstance(komi, (int, float)) or komi < 0:
            raise ValueError(f"Invalid komi: {komi}. Must be a non-negative number.")
        if score_system not in ["area", "territory"]:
            raise ValueError(f"Invalid scoring system: {score_system}. Must be 'area' or 'territory'.")
            
        self.board = Board(size=board_size)
        self.current_player = BLACK
        self.komi = komi
        self.moves_history: List[Tuple[int, int] | str] = []
        self.is_game_over = False
        self.passes = 0
        self.move_stack = MoveStack(self.board)
        self.score_system = score_system
        self.winner: Optional[int] = None

    def play(self, y: Optional[int] = None, x: Optional[int] = None) -> bool:
        """
        Make a move at the given coordinates, or pass if coordinates are None.
        
        Args:
            y (Optional[int]): Row coordinate
            x (Optional[int]): Column coordinate
            
        Returns:
            bool: True if the move was successful
            
        Raises:
            GameError: If the game is already over
            InvalidMoveError: If the move is invalid
            ValueError: If coordinates are invalid
        """
        if self.is_game_over:
            raise GameError("Game is already over, no more moves allowed")
            
        # Handle pass move
        if y is None or x is None:
            move = Move(color=self.current_player, is_pass=True)
            result = self.move_stack.push(move)
            if result:
                self.moves_history.append("pass")
                self.passes += 1
                if self.passes >= 2:
                    self.is_game_over = True
                    self._determine_winner()
                self.current_player = BLACK if self.current_player == WHITE else WHITE
            return result
            
        # Handle stone placement
        if not isinstance(y, int) or not isinstance(x, int):
            raise ValueError(f"Invalid coordinates: ({y}, {x}). Must be integers.")
            
        try:
            self.board.place_stone(y, x, self.current_player)
            move = Move(y=y, x=x, color=self.current_player)
            result = self.move_stack.push(move)
            if not result:
                raise InvalidMoveError(f"Failed to apply move at ({y}, {x})")
                
            self.moves_history.append((y, x))
            self.passes = 0
            self.current_player = BLACK if self.current_player == WHITE else WHITE
            return True
        except GoError as e:
            raise InvalidMoveError(str(e))
    
    def undo(self) -> bool:
        """
        Undo the last move.
        
        Returns:
            bool: True if a move was undone
            
        Raises:
            GameError: If there are no moves to undo
        """
        if not self.moves_history:
            raise GameError("No moves to undo")
            
        move = self.move_stack.pop()
        if move:
            self.moves_history.pop()
            if move.is_pass:
                self.passes = max(0, self.passes - 1)
            if self.is_game_over:
                self.is_game_over = False
                self.winner = None
            self.current_player = move.color
            return True
        return False
    
    def resign(self, color: Optional[int] = None) -> bool:
        """
        Resign the game for the given player or current player.
        
        Args:
            color (Optional[int]): Color of the resigning player
            
        Returns:
            bool: True if resignation was successful
            
        Raises:
            ValueError: If color is invalid
            GameError: If the game is already over
        """
        if self.is_game_over:
            raise GameError("Game is already over")
            
        resign_color = color if color is not None else self.current_player
        if resign_color not in [BLACK, WHITE]:
            raise ValueError(f"Invalid color for resignation: {resign_color}. Must be BLACK or WHITE.")
            
        move = Move(color=resign_color, is_resign=True)
        result = self.move_stack.push(move)
        if result:
            self.moves_history.append("resign")
            self.is_game_over = True
            self.winner = WHITE if resign_color == BLACK else BLACK
            return True
        return False
    
    def get_legal_moves(self) -> List[Tuple[int, int]]:
        """
        Get all legal moves for the current player.
        
        Returns:
            List[Tuple[int, int]]: List of valid move coordinates
            
        Raises:
            GameError: If the game is over
        """
        if self.is_game_over:
            raise GameError("Game is over, no legal moves available")
        return self.board.get_legal_moves(self.current_player)
    
    def _determine_winner(self) -> int:
        """
        Determine the winner of the game based on score.
        
        Returns:
            int: Winner (BLACK, WHITE, or 0 for tie)
        """
        black_score, white_score = self.get_score()
        if black_score > white_score:
            self.winner = BLACK
        elif white_score > black_score:
            self.winner = WHITE
        else:
            self.winner = 0
        return self.winner
    
    def get_score(self) -> Tuple[float, float]:
        """
        Calculate the score based on the selected scoring system.
        
        Returns:
            Tuple[float, float]: (black_score, white_score)
            
        Raises:
            ScoringError: If there is an error calculating the score
        """
        try:
            if self.score_system == "area":
                return self._get_area_score()
            elif self.score_system == "territory":
                return self._get_territory_score()
            else:
                raise ScoringError(f"Invalid score system: {self.score_system}")
        except Exception as e:
            raise ScoringError(f"Error calculating score: {e}")
    
    def _optimized_flood_fill(self, board: np.ndarray, size: int) -> Tuple[float, float, float, float]:
        """
        Optimized flood fill for territory calculation using BFS.
        
        Args:
            board (np.ndarray): The game board
            size (int): Board size
            
        Returns:
            Tuple[float, float, float, float]: (black_territory, white_territory, black_stones, white_stones)
        """
        black_mask = (board == BLACK)
        white_mask = (board == WHITE)
        black_stones = np.sum(black_mask)
        white_stones = np.sum(white_mask)
        
        visited = np.zeros_like(board, dtype=bool)
        black_territory = 0
        white_territory = 0
        directions = np.array([(-1, 0), (0, 1), (1, 0), (0, -1)])
        
        for y in range(1, size + 1):
            for x in range(1, size + 1):
                if board[y, x] == EMPTY and not visited[y, x]:
                    queue = deque([(y, x)])
                    territory = [(y, x)]
                    visited[y, x] = True
                    black_border = False
                    white_border = False
                    
                    while queue:
                        cy, cx = queue.popleft()
                        for dy, dx in directions:
                            ny, nx = cy + dy, cx + dx
                            if ny < 1 or ny > size or nx < 1 or nx > size:
                                continue
                            if board[ny, nx] == BLACK:
                                black_border = True
                            elif board[ny, nx] == WHITE:
                                white_border = True
                            elif board[ny, nx] == EMPTY and not visited[ny, nx]:
                                queue.append((ny, nx))
                                territory.append((ny, nx))
                                visited[ny, nx] = True
                                
                    territory_size = len(territory)
                    if black_border and not white_border:
                        black_territory += territory_size
                    elif white_border and not black_border:
                        white_territory += territory_size
                        
        return black_territory, white_territory, black_stones, white_stones
    
    def _get_area_score(self) -> Tuple[float, float]:
        """
        Calculate the score using area scoring (stones + territory).
        
        Returns:
            Tuple[float, float]: (black_score, white_score)
        """
        board = self.board.board
        size = self.board.size
        black_territory, white_territory, black_stones, white_stones = self._optimized_flood_fill(board, size)
        black_score = float(black_territory + black_stones)
        white_score = float(white_territory + white_stones + self.komi)
        return black_score, white_score

    def _get_territory_score(self) -> Tuple[float, float]:
        """
        Calculate the score using territory scoring (Japanese rules).
        
        Returns:
            Tuple[float, float]: (black_score, white_score)
        """
        board = self.board.board
        size = self.board.size
        black_territory, white_territory, _, _ = self._optimized_flood_fill(board, size)
        black_prisoners = self.board.white_captures
        white_prisoners = self.board.black_captures
        black_score = float(black_territory + black_prisoners)
        white_score = float(white_territory + white_prisoners + self.komi)
        return black_score, white_score

    def get_winner(self) -> Optional[int]:
        """
        Return the winner of the game.
        
        Returns:
            Optional[int]: Winner (BLACK, WHITE, or None if game is not over)
        """
        if not self.is_game_over:
            return None
        return self.winner
    
    def copy(self) -> 'Game':
        """
        Create a deep copy of the game state.
        
        Returns:
            Game: A new game instance with the same state
            
        Raises:
            GameError: If there is an error creating the copy
        """
        try:
            new_game = Game(board_size=self.board.size, komi=self.komi, score_system=self.score_system)
            new_game.board.board = self.board.board.copy()
            new_game.board.black_captures = self.board.black_captures
            new_game.board.white_captures = self.board.white_captures
            new_game.board.current_hash = self.board.current_hash
            new_game.board.position_history = self.board.position_history.copy()
            new_game.current_player = self.current_player
            new_game.moves_history = self.moves_history.copy()
            new_game.is_game_over = self.is_game_over
            new_game.passes = self.passes
            new_game.winner = self.winner
            return new_game
        except Exception as e:
            raise GameError(f"Error creating game copy: {e}")
    
    def reset(self) -> None:
        """
        Reset the game to initial state.
        
        This method clears all stones, resets capture counts, and reinitializes
        the group manager and position history.
        """
        self.board.reset()
        self.current_player = BLACK
        self.moves_history = []
        self.is_game_over = False
        self.passes = 0
        self.winner = None
        self.move_stack = MoveStack(self.board)
        
    def get_current_state(self) -> int:
        """
        Get a compact representation of the current game state.
        
        Returns:
            int: Current board position hash
        """
        return self.board.current_hash