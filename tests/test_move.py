"""
Tests for the move module.
"""

import unittest
from weiqi_py.move import Move, MoveStack, MoveError
from weiqi_py.board import Board, BLACK, WHITE, EMPTY

class TestMove(unittest.TestCase):
    def test_initialization(self):
        """Test Move initialization."""
        # Standard move
        move = Move(y=3, x=4, color=BLACK)
        self.assertEqual(move.y, 3)
        self.assertEqual(move.x, 4)
        self.assertEqual(move.color, BLACK)
        self.assertFalse(move.is_pass)
        self.assertFalse(move.is_resign)
        
        # Pass move
        pass_move = Move(color=WHITE, is_pass=True)
        self.assertIsNone(pass_move.y)
        self.assertIsNone(pass_move.x)
        self.assertEqual(pass_move.color, WHITE)
        self.assertTrue(pass_move.is_pass)
        self.assertFalse(pass_move.is_resign)
        
        # Resign move
        resign_move = Move(color=BLACK, is_resign=True)
        self.assertIsNone(resign_move.y)
        self.assertIsNone(resign_move.x)
        self.assertEqual(resign_move.color, BLACK)
        self.assertFalse(resign_move.is_pass)
        self.assertTrue(resign_move.is_resign)
        
        # Invalid moves
        with self.assertRaises(ValueError):
            Move(color=3)  # Invalid color
            
        with self.assertRaises(ValueError):
            Move(is_pass=True, is_resign=True)  # Can't be both pass and resign
            
        with self.assertRaises(ValueError):
            Move()  # Must specify something
            
    def test_string_representation(self):
        """Test string representation of moves."""
        # Standard move
        move = Move(y=3, x=4, color=BLACK)
        self.assertIn("Black", str(move))
        self.assertIn("3", str(move))
        self.assertIn("4", str(move))
        
        # Pass move
        pass_move = Move(color=WHITE, is_pass=True)
        self.assertIn("White", str(pass_move))
        self.assertIn("Pass", str(pass_move))
        
        # Resign move
        resign_move = Move(color=BLACK, is_resign=True)
        self.assertIn("Black", str(resign_move))
        self.assertIn("Resign", str(resign_move))


class TestMoveStack(unittest.TestCase):
    def setUp(self):
        """Set up a new board and move stack before each test."""
        self.board = Board(size=9)
        self.move_stack = MoveStack(self.board)
        
    def test_push_pop(self):
        """Test pushing and popping moves."""
        # Push a move
        move1 = Move(y=3, x=3, color=BLACK)
        self.assertTrue(self.move_stack.push(move1))
        self.assertEqual(self.board.board[3, 3], BLACK)
        self.assertEqual(len(self.move_stack), 1)
        
        # Push another move
        move2 = Move(y=3, x=4, color=WHITE)
        self.assertTrue(self.move_stack.push(move2))
        self.assertEqual(self.board.board[3, 4], WHITE)
        self.assertEqual(len(self.move_stack), 2)
        
        # Pop a move
        popped = self.move_stack.pop()
        self.assertEqual(popped, move2)
        self.assertEqual(self.board.board[3, 4], EMPTY)
        self.assertEqual(len(self.move_stack), 2)  # Length doesn't change
        self.assertEqual(self.move_stack.current_index, 0)
        
        # Pop another move
        popped = self.move_stack.pop()
        self.assertEqual(popped, move1)
        self.assertEqual(self.board.board[3, 3], EMPTY)
        self.assertEqual(self.move_stack.current_index, -1)
        
        # Pop from empty stack
        self.assertIsNone(self.move_stack.pop())
        
    def test_pass_and_resign(self):
        """Test pass and resign moves."""
        # Push a pass move
        pass_move = Move(color=BLACK, is_pass=True)
        self.assertTrue(self.move_stack.push(pass_move))
        self.assertEqual(len(self.move_stack), 1)
        
        # Push a resign move
        resign_move = Move(color=WHITE, is_resign=True)
        self.assertTrue(self.move_stack.push(resign_move))
        self.assertEqual(len(self.move_stack), 2)
        
        # Pop a move
        popped = self.move_stack.pop()
        self.assertEqual(popped, resign_move)
        
        # Pop another move
        popped = self.move_stack.pop()
        self.assertEqual(popped, pass_move)
        
    def test_forward_back(self):
        """Test forward and back navigation."""
        # Push some moves
        move1 = Move(y=3, x=3, color=BLACK)
        move2 = Move(y=3, x=4, color=WHITE)
        self.move_stack.push(move1)
        self.move_stack.push(move2)
        
        # Go back twice
        self.assertTrue(self.move_stack.back())
        self.assertTrue(self.move_stack.back())
        self.assertEqual(self.board.board[3, 3], EMPTY)
        self.assertEqual(self.board.board[3, 4], EMPTY)
        
        # Go forward
        self.assertTrue(self.move_stack.forward())
        self.assertEqual(self.board.board[3, 3], BLACK)
        self.assertEqual(self.board.board[3, 4], EMPTY)
        
        # Go forward again
        self.assertTrue(self.move_stack.forward())
        self.assertEqual(self.board.board[3, 3], BLACK)
        self.assertEqual(self.board.board[3, 4], WHITE)
        
        # Can't go forward anymore
        self.assertFalse(self.move_stack.forward())
        
    def test_to_root_and_end(self):
        """Test to_root and to_end navigation."""
        # Push some moves
        moves = [
            Move(y=3, x=3, color=BLACK),
            Move(y=3, x=4, color=WHITE),
            Move(y=4, x=3, color=BLACK),
            Move(y=4, x=4, color=WHITE)
        ]
        for move in moves:
            self.move_stack.push(move)
            
        # Go to root
        self.move_stack.to_root()
        self.assertEqual(self.move_stack.current_index, -1)
        for y in range(1, 10):
            for x in range(1, 10):
                self.assertEqual(self.board.board[y, x], EMPTY)
                
        # Go to end
        self.move_stack.to_end()
        self.assertEqual(self.move_stack.current_index, 3)
        self.assertEqual(self.board.board[3, 3], BLACK)
        self.assertEqual(self.board.board[3, 4], WHITE)
        self.assertEqual(self.board.board[4, 3], BLACK)
        self.assertEqual(self.board.board[4, 4], WHITE)
        
    def test_peek_and_peek_next(self):
        """Test peeking at current and next moves."""
        # Push some moves
        move1 = Move(y=3, x=3, color=BLACK)
        move2 = Move(y=3, x=4, color=WHITE)
        self.move_stack.push(move1)
        self.move_stack.push(move2)
        
        # Go back one move
        self.move_stack.back()
        
        # Peek at current move
        current = self.move_stack.peek()
        self.assertEqual(current, move1)
        
        # Peek at next move
        next_move = self.move_stack.peek_next()
        self.assertEqual(next_move, move2)
        
        # Go back to root
        self.move_stack.back()
        
        # Peek from empty position
        self.assertIsNone(self.move_stack.peek())
        self.assertEqual(self.move_stack.peek_next(), move1)
        
    def test_captures(self):
        """Test capturing stones and move state preservation."""
        # Set up a capture scenario
        # Black stone surrounded by white stones
        self.board.place_stone(4, 4, BLACK)
        move1 = Move(y=4, x=3, color=WHITE)
        move2 = Move(y=3, x=4, color=WHITE)
        move3 = Move(y=5, x=4, color=WHITE)
        # Last move will capture
        move4 = Move(y=4, x=5, color=WHITE)
        
        # Push first three moves
        self.move_stack.push(move1)
        self.move_stack.push(move2)
        self.move_stack.push(move3)
        
        # Push capturing move
        self.move_stack.push(move4)
        self.assertEqual(self.board.board[4, 4], EMPTY)
        self.assertGreater(len(move4.captured_stones), 0)
        
        # Undo the capture
        self.move_stack.pop()
        self.assertEqual(self.board.board[4, 4], BLACK)
        
        # Redo the capture
        self.move_stack.forward()
        self.assertEqual(self.board.board[4, 4], EMPTY)
        
    def test_current_position(self):
        """Test current position tracking."""
        self.assertEqual(self.move_stack.current_position(), 0)
        
        # Push some moves
        self.move_stack.push(Move(y=3, x=3, color=BLACK))
        self.assertEqual(self.move_stack.current_position(), 1)
        
        self.move_stack.push(Move(y=3, x=4, color=WHITE))
        self.assertEqual(self.move_stack.current_position(), 2)
        
        # Go back
        self.move_stack.back()
        self.assertEqual(self.move_stack.current_position(), 1)
        
        # Go to root
        self.move_stack.to_root()
        self.assertEqual(self.move_stack.current_position(), 0)

if __name__ == '__main__':
    unittest.main() 