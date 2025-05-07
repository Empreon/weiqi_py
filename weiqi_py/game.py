import numpy as np
from .board import Board, BLACK, WHITE, EMPTY
from .move import Move, MoveStack

class Game:
    def __init__(self, board_size=19, komi=6.5, score_system="area") -> None:
        self.board = Board(size=board_size)
        self.current_player = BLACK  # Black goes first
        self.komi = komi
        self.moves_history = []
        self.is_game_over = False
        self.passes = 0
        self.move_stack = MoveStack(self.board)
        self.score_system = score_system

    def play(self, y=None, x=None) -> bool:
        """Make a move at the given coordinates, or pass if coordinates are None"""
        if self.is_game_over: return False
        if y is None or x is None: 
            move = Move(color=self.current_player, is_pass=True)
            result = self.move_stack.push(move)
            if result:
                self.moves_history.append("pass")
                self.passes += 1
                if self.passes >= 2: self.is_game_over = True
                self.current_player = BLACK if self.current_player == WHITE else WHITE
            return result
        else: 
            move = Move(y=y, x=x, color=self.current_player)
            result = self.move_stack.push(move)
            if result: # Move was successful
                self.moves_history.append((y, x))
                self.passes = 0  # Reset pass counter
                self.current_player = BLACK if self.current_player == WHITE else WHITE
            return result
    
    def undo(self) -> bool:
        """Undo the last move"""
        if not self.moves_history: return False
        move = self.move_stack.pop() # Pop the last move from the stack
        if move:
            self.moves_history.pop()
            if move.is_pass: self.passes = max(0, self.passes - 1)
            if self.is_game_over: self.is_game_over = False
            self.current_player = move.color
            return True
        return False
    
    def get_legal_moves(self) -> list[tuple[int, int]]:
        """Get all legal moves for the current player"""
        return self.board.get_legal_moves(self.current_player)
    
    def get_score(self) -> tuple[int, int]:
        """Calculate the score based on the selected scoring system"""
        if self.score_system == "area": return self._get_area_score()
        elif self.score_system == "territory": return self._get_territory_score()
        else: raise ValueError(f"Invalid score system: {self.score_system}")
    
    def _flood_fill(self, board, size:int, visited, y:int, x:int, color:int) -> tuple[int, int]:
        """Common flood fill function for both scoring methods"""
        if y < 1 or y > size or x < 1 or x > size or visited[y, x] or board[y, x] != EMPTY: return 0, None
        visited[y, x] = True
        territory_size = 1
        owner = color
        neighbors = [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]
        for ny, nx in neighbors:
            if 1 <= ny <= size and 1 <= nx <= size:
                if board[ny, nx] == BLACK:
                    if owner == WHITE: owner = None  # Contested territory
                elif board[ny, nx] == WHITE:
                    if owner == BLACK: owner = None  # Contested territory
                elif not visited[ny, nx]:
                    size_increment, sub_owner = self._flood_fill(board, size, visited, ny, nx, owner)
                    territory_size += size_increment
                    if owner != sub_owner: owner = None
        return territory_size, owner
    
    def _get_area_score(self) -> tuple[int, int]:
        """Calculate the score using area scoring (using flood fill)"""
        board = self.board.board
        size = self.board.size
        visited = np.zeros_like(board, dtype=bool)
        black_territory = 0
        white_territory = 0
        for y in range(1, size + 1):
            for x in range(1, size + 1):
                if board[y, x] == EMPTY and not visited[y, x]:
                    territory_size, owner = self._flood_fill(board, size, visited, y, x, None)
                    if owner == BLACK: black_territory += territory_size
                    elif owner == WHITE: white_territory += territory_size
        black_territory += np.sum(board == BLACK)
        white_territory += np.sum(board == WHITE)
        white_territory += self.komi  # Add komi
        return black_territory, white_territory

    def _get_territory_score(self) -> tuple[int, int]:
        """Calculate the score using territory scoring (Japanese rules)"""
        board = self.board.board
        size = self.board.size
        black_territory = 0
        white_territory = 0
        black_prisoners = self.board.white_captures  # Black captures white stones
        white_prisoners = self.board.black_captures  # White captures black stones
        visited = np.zeros_like(board, dtype=bool)
        for y in range(1, size + 1):
            for x in range(1, size + 1):
                if board[y, x] == EMPTY and not visited[y, x]:
                    territory_size, owner = self._flood_fill(board, size, visited, y, x, None)
                    if owner == BLACK:
                        black_territory += territory_size
                    elif owner == WHITE:
                        white_territory += territory_size
        black_score = black_territory + black_prisoners
        white_score = white_territory + white_prisoners + self.komi
        return black_score, white_score

    def get_winner(self) -> int:
        """Determine the winner of the game"""
        if not self.is_game_over: return None
        black_score, white_score = self.get_score()
        if black_score > white_score: return BLACK
        elif white_score > black_score: return WHITE
        else: return 0  # Draw
    
    def copy(self) -> 'Game':
        """Create a deep copy of the game state"""
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
        return new_game
    
    def reset(self) -> None:
        """Reset the game to initial state"""
        self.board.reset()
        self.current_player = BLACK
        self.moves_history = []
        self.is_game_over = False
        self.passes = 0
        self.move_stack = MoveStack(self.board)  # Create a new move stack
        
    def get_current_state(self) -> int:
        """Get a compact representation of the current game state"""
        return self.board.current_hash