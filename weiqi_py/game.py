import numpy as np
from collections import deque
from .board import Board, BLACK, WHITE, EMPTY
from .move import Move, MoveStack

class GameError(Exception): pass
class InvalidMoveError(GameError): pass
class ScoringError(GameError): pass

class Game:
    def __init__(self, board_size=19, komi=6.5, score_system="area") -> None:
        if not isinstance(board_size, int) or board_size < 5 or board_size > 25: raise ValueError(f"Invalid board size: {board_size}.")
        if not isinstance(komi, (int, float)): raise ValueError(f"Invalid komi: {komi}.")
        if score_system not in ["area", "territory"]: raise ValueError(f"Invalid scoring system: {score_system}.")
        self.board = Board(size=board_size)
        self.current_player = BLACK  # Black goes first
        self.komi = komi
        self.moves_history = []
        self.is_game_over = False
        self.passes = 0
        self.move_stack = MoveStack(self.board)
        self.score_system = score_system
        self.winner = None

    def play(self, y=None, x=None) -> bool:
        """Make a move at the given coordinates, or pass if coordinates are None"""
        if self.is_game_over: raise GameError("Game is already over, no more moves allowed")
        if y is None or x is None: # Pass move
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
        if not isinstance(y, int) or not isinstance(x, int): raise InvalidMoveError(f"Invalid coordinates: ({y}, {x}).")
        if not (1 <= y <= self.board.size and 1 <= x <= self.board.size): raise InvalidMoveError(f"Coordinates out of bounds: ({y}, {x}).")
        if self.board.board[y, x] != EMPTY: raise InvalidMoveError(f"Position ({y}, {x}) is already occupied.")
        move = Move(y=y, x=x, color=self.current_player)
        result = self.move_stack.push(move)
        if not result:
            if not self.board.is_valid_move(y, x, self.current_player):
                if self._would_be_suicide(y, x, self.current_player): raise InvalidMoveError(f"Suicide move at ({y}, {x}).")
                else: raise InvalidMoveError(f"Move at ({y}, {x}) violates ko rule.")
            raise InvalidMoveError(f"Invalid move at ({y}, {x}) for unknown reason")
        self.moves_history.append((y, x))
        self.passes = 0  # Reset pass counter
        self.current_player = BLACK if self.current_player == WHITE else WHITE
        return True
    
    def _would_be_suicide(self, y, x, color):
        """Determine if a move would be a suicide move"""
        temp_board = self.board.board.copy()
        temp_board[y, x] = color
        group = set([(y, x)])
        queue = [(y, x)]
        while queue:
            cy, cx = queue.pop(0)
            for dy, dx in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
                ny, nx = cy + dy, cx + dx
                if temp_board[ny, nx] == EMPTY:
                    return False  # Not suicide, has a liberty
                if temp_board[ny, nx] == color and (ny, nx) not in group:
                    group.add((ny, nx))
                    queue.append((ny, nx))
        return True
    
    def undo(self) -> bool:
        """Undo the last move"""
        if not self.moves_history: return False
        move = self.move_stack.pop()
        if move:
            self.moves_history.pop()
            if move.is_pass: self.passes = max(0, self.passes - 1)
            if self.is_game_over:
                self.is_game_over = False
                self.winner = None
            self.current_player = move.color
            return True
        return False
    
    def resign(self, color=None) -> bool:
        """Resign the game for the given player or current player"""
        if self.is_game_over: return False
        resign_color = color if color is not None else self.current_player
        if resign_color not in [BLACK, WHITE]: raise ValueError(f"Invalid color for resignation: {resign_color}.")
        move = Move(color=resign_color, is_resign=True)
        result = self.move_stack.push(move)
        if result:
            self.moves_history.append("resign")
            self.is_game_over = True
            self.winner = WHITE if resign_color == BLACK else BLACK
            return True
        return False
    
    def get_legal_moves(self) -> list[tuple[int, int]]:
        """Get all legal moves for the current player"""
        if self.is_game_over: return []
        return self.board.get_legal_moves(self.current_player)
    
    def _determine_winner(self) -> int:
        """Determine the winner of the game"""
        black_score, white_score = self.get_score()
        if black_score > white_score: self.winner = BLACK
        elif white_score > black_score: self.winner = WHITE
        else: self.winner = 0  # Draw
        return self.winner
    
    def get_score(self) -> tuple[int, int]:
        """Calculate the score based on the selected scoring system"""
        try:
            if self.score_system == "area": return self._get_area_score()
            elif self.score_system == "territory": return self._get_territory_score()
            else: raise ScoringError(f"Invalid score system: {self.score_system}")
        except Exception as e: raise ScoringError(f"Error calculating score: {e}")
    
    def _optimized_flood_fill(self, board, size: int) -> tuple[float, float]:
        """Optimized flood fill for territory calculation using BFS"""
        black_mask = (board == BLACK)
        white_mask = (board == WHITE)
        black_stones = np.sum(black_mask)
        white_stones = np.sum(white_mask)
        visited = np.zeros_like(board, dtype=bool)
        black_territory = 0
        white_territory = 0
        directions = np.array([(-1, 0), (0, 1), (1, 0), (0, -1)])
        for y in range(1, size + 1): # Process all empty points
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
                            if ny < 1 or ny > size or nx < 1 or nx > size: continue
                            if board[ny, nx] == BLACK: black_border = True
                            elif board[ny, nx] == WHITE: white_border = True
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
    
    def _get_area_score(self) -> tuple[float, float]:
        """Calculate the score using area scoring (stones + territory)"""
        board = self.board.board
        size = self.board.size
        black_territory, white_territory, black_stones, white_stones = self._optimized_flood_fill(board, size)
        black_score = black_territory + black_stones
        white_score = white_territory + white_stones + self.komi
        return black_score, white_score

    def _get_territory_score(self) -> tuple[float, float]:
        """Calculate the score using territory scoring (Japanese rules)"""
        board = self.board.board
        size = self.board.size
        black_territory, white_territory, _, _ = self._optimized_flood_fill(board, size)
        black_prisoners = self.board.white_captures
        white_prisoners = self.board.black_captures
        black_score = black_territory + black_prisoners
        white_score = white_territory + white_prisoners + self.komi
        return black_score, white_score

    def get_winner(self) -> int:
        """Return the winner of the game"""
        if not self.is_game_over: return None
        return self.winner
    
    def copy(self) -> 'Game':
        """Create a deep copy of the game state"""
        try:
            new_game = Game(board_size=self.board.size, komi=self.komi, score_system=self.score_system)
            new_game.board.board = self.board.board.copy()
            new_game.board.black_captures = self.board.black_captures
            new_game.board.white_captures = self.board.white_captures
            new_game.board.current_hash = self.board.current_hash
            # Create a copy of the position history set to avoid sharing references
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
        """Reset the game to initial state"""
        self.board.reset()
        self.current_player = BLACK
        self.moves_history = []
        self.is_game_over = False
        self.passes = 0
        self.winner = None
        self.move_stack = MoveStack(self.board)  # Create a new move stack
        
    def get_current_state(self) -> int:
        """Get a compact representation of the current game state"""
        return self.board.current_hash