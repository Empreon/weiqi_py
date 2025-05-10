from copy import deepcopy
from .board import BLACK, WHITE, EMPTY, DIRECTIONS

class Move:
    def __init__(self, y=None, x=None, color=None, is_pass=False, is_resign=False) -> None:
        self.y = y
        self.x = x
        self.color = color
        self.is_pass = is_pass
        self.is_resign = is_resign
        self.captured_stones = []
        self.previous_zobrist_hash = None
        self.previous_position_history = None
        
    def __str__(self) -> str:
        if self.is_pass: return f"{'Black' if self.color == BLACK else 'White'} Pass"
        elif self.is_resign: return f"{'Black' if self.color == BLACK else 'White'} Resign"
        else: return f"{'Black' if self.color == BLACK else 'White'} ({self.y},{self.x})"

class MoveStack:
    """Stack-based representation of moves for efficient MCTS tree traversal"""
    def __init__(self, board) -> None:
        self.board = board
        self.moves = []
        self.current_index = -1
        
    def push(self, move:Move) -> bool:
        """Push a move onto the stack and apply it to the board"""
        move.previous_zobrist_hash = self.board.current_hash
        move.previous_position_history = deepcopy(self.board.position_history)
        if move.is_pass or move.is_resign:
            self.moves = self.moves[:self.current_index + 1]
            self.moves.append(move)
            self.current_index += 1
            return True
        opponent = WHITE if move.color == BLACK else BLACK
        potential_captures = []
        temp_board = self.board.board.copy()
        temp_board[move.y, move.x] = move.color
        for dy, dx in DIRECTIONS:
            ny, nx = move.y + dy, move.x + dx
            if 1 <= ny <= self.board.size and 1 <= nx <= self.board.size:
                if temp_board[ny, nx] == opponent:
                    group = self.board._get_group(ny, nx)
                    liberties = self.board._get_liberties(frozenset(group))
                    if len(liberties) == 1 and (move.y, move.x) in liberties: potential_captures.extend(group)
        if not self.board.place_stone(move.y, move.x, move.color): return False
        for y, x in potential_captures:
            if self.board.board[y, x] == EMPTY: move.captured_stones.append((y, x))
        self.moves = self.moves[:self.current_index + 1]
        self.moves.append(move)
        self.current_index += 1
        return True
        
    def pop(self) -> Move:
        """Pop a move from the stack and undo it on the board"""
        if self.current_index < 0: return None
        move = self.moves[self.current_index]
        self.current_index -= 1
        if move.is_pass or move.is_resign: return move
        self.board.board[move.y, move.x] = EMPTY
        opponent = WHITE if move.color == BLACK else BLACK
        for y, x in move.captured_stones: self.board.board[y, x] = opponent
        self.board.current_hash = move.previous_zobrist_hash
        self.board.position_history = move.previous_position_history
        # self.board._get_liberties.cache_clear()
        # self.board._get_group.cache_clear()
        return move
        
    def peek(self) -> Move:
        """Peek at the current move without popping"""
        if self.current_index < 0: return None
        return self.moves[self.current_index]
        
    def peek_next(self) -> Move:
        """Peek at the next move without pushing"""
        if self.current_index + 1 >= len(self.moves): return None
        return self.moves[self.current_index + 1]
        
    def forward(self) -> bool:
        """Move forward in the move stack (redo)"""
        if self.current_index + 1 >= len(self.moves): return False
        next_move = self.moves[self.current_index + 1]
        if next_move.is_pass or next_move.is_resign:
            self.current_index += 1
            return True
        self.board.board[next_move.y, next_move.x] = next_move.color
        self.board.current_hash = next_move.previous_zobrist_hash
        self.board.current_hash ^= self.board.zobrist_table[next_move.y, next_move.x, next_move.color - 1]
        opponent = WHITE if next_move.color == BLACK else BLACK
        for y, x in next_move.captured_stones:
            self.board.board[y, x] = EMPTY
            self.board.current_hash ^= self.board.zobrist_table[y, x, opponent - 1]
        self.board.position_history = deepcopy(next_move.previous_position_history)
        self.board.position_history.add(self.board.current_hash)
        self.current_index += 1
        # self.board._get_liberties.cache_clear()
        # self.board._get_group.cache_clear()
        return True
        
    def back(self) -> bool:
        """Move backward in the move stack (undo)"""
        return self.pop() is not None
        
    def to_root(self) -> None:
        """Undo all moves and return to the root state"""
        while self.pop() is not None: pass
        
    def to_end(self) -> None:
        """Redo all moves and go to the end of the stack"""
        while self.forward(): pass
        
    def __len__(self) -> int:
        """Return the total number of moves in the stack"""
        return len(self.moves)
        
    def current_position(self) -> int:
        """Return the current position in the stack"""
        return self.current_index + 1 