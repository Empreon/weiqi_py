"""
Tests for the board module.
"""

import unittest
import numpy as np
from weiqi_py.board import Board, BLACK, WHITE, EMPTY, GroupManager, InvalidMoveError

class TestBoard(unittest.TestCase):
    def setUp(self):
        """Set up a new board before each test."""
        self.board = Board(size=9)
        
    def test_initialization(self):
        """Test board initialization with different sizes."""
        # Test default size
        board = Board()
        self.assertEqual(board.size, 19)
        
        # Test custom size
        board = Board(size=13)
        self.assertEqual(board.size, 13)
        
        # Test invalid size
        with self.assertRaises(ValueError):
            Board(size=4)
        with self.assertRaises(ValueError):
            Board(size=26)
            
    def test_board_reset(self):
        """Test board reset functionality."""
        # Place some stones
        self.board.place_stone(3, 3, BLACK)
        self.board.place_stone(3, 4, WHITE)
        
        # Reset the board
        self.board.reset()
        
        # Check board is empty
        for y in range(1, self.board.size + 1):
            for x in range(1, self.board.size + 1):
                self.assertEqual(self.board.board[y, x], EMPTY)
                
        # Check counters are reset
        self.assertEqual(self.board.black_captures, 0)
        self.assertEqual(self.board.white_captures, 0)
        
    def test_place_stone(self):
        """Test stone placement."""
        # Valid placement
        self.assertTrue(self.board.place_stone(5, 5, BLACK))
        self.assertEqual(self.board.board[5, 5], BLACK)
        
        # Invalid placements
        with self.assertRaises(InvalidMoveError):
            self.board.place_stone(5, 5, WHITE)  # Occupied
        
        with self.assertRaises(InvalidMoveError):
            self.board.place_stone(0, 5, BLACK)  # Out of bounds
            
        with self.assertRaises(ValueError):
            self.board.place_stone(5, 5, 3)  # Invalid color
            
    def test_capture(self):
        """Test capturing stones."""
        # Set up a capture scenario
        self.board.place_stone(4, 4, BLACK)
        self.board.place_stone(4, 3, WHITE)
        self.board.place_stone(3, 4, WHITE)
        self.board.place_stone(5, 4, WHITE)
        self.board.place_stone(4, 5, WHITE)
        
        # Black stone should be captured
        self.assertEqual(self.board.board[4, 4], EMPTY)
        self.assertEqual(self.board.white_captures, 1)
        
    def test_suicide_rule(self):
        """Test suicide rule."""
        # Set up a suicide scenario
        self.board.place_stone(1, 2, BLACK)
        self.board.place_stone(2, 1, BLACK)
        self.board.place_stone(1, 3, WHITE)
        self.board.place_stone(2, 2, WHITE)
        self.board.place_stone(3, 1, WHITE)
        
        # Suicide move should be invalid
        with self.assertRaises(InvalidMoveError):
            self.board.place_stone(1, 1, WHITE)
            
    def test_ko_rule(self):
        """Test ko rule."""
        # Set up a ko scenario
        self.board.place_stone(4, 4, BLACK)
        self.board.place_stone(4, 3, WHITE)
        self.board.place_stone(3, 4, WHITE)
        self.board.place_stone(5, 4, WHITE)
        self.board.place_stone(4, 5, BLACK)
        self.board.place_stone(3, 3, BLACK)
        self.board.place_stone(5, 3, BLACK)
        
        # White captures
        self.board.place_stone(4, 4, WHITE)
        
        # Ko recapture should be invalid
        with self.assertRaises(InvalidMoveError):
            self.board.place_stone(4, 3, BLACK)
            
    def test_get_legal_moves(self):
        """Test getting legal moves."""
        # Empty board should have all points as legal
        legal_moves = self.board.get_legal_moves(BLACK)
        self.assertEqual(len(legal_moves), self.board.size * self.board.size)
        
        # Place a stone
        self.board.place_stone(5, 5, BLACK)
        
        # That position should no longer be legal
        legal_moves = self.board.get_legal_moves(WHITE)
        self.assertNotIn((5, 5), legal_moves)
        
    def test_string_representation(self):
        """Test string representation of the board."""
        self.board.place_stone(1, 1, BLACK)
        self.board.place_stone(1, 2, WHITE)
        
        board_str = str(self.board)
        self.assertIn("B", board_str)
        self.assertIn("W", board_str)
        

class TestGroupManager(unittest.TestCase):
    def setUp(self):
        """Set up a new board and group manager before each test."""
        self.size = 9
        self.board = np.zeros((self.size + 2, self.size + 2), dtype=np.int8)
        self.group_manager = GroupManager(self.size)
        
    def test_create_group(self):
        """Test creating a new group."""
        # Place a stone
        y, x = 3, 3
        self.board[y, x] = BLACK
        
        # Create a group for it
        group_id = self.group_manager.create_group(y, x, BLACK, self.board)
        
        # Check group was created correctly
        self.assertEqual(self.group_manager.get_group_id(y, x), group_id)
        self.assertIn((y, x), self.group_manager.get_group_stones(group_id))
        self.assertEqual(len(self.group_manager.get_group_liberties(group_id)), 4)
        
    def test_merge_groups(self):
        """Test merging groups."""
        # Create two adjacent groups
        self.board[3, 3] = BLACK
        self.board[3, 4] = BLACK
        
        group1 = self.group_manager.create_group(3, 3, BLACK, self.board)
        group2 = self.group_manager.create_group(3, 4, BLACK, self.board)
        
        # Merge the groups with a new stone
        self.board[3, 5] = BLACK
        merged_id = self.group_manager.merge_groups({group1, group2}, (3, 5), self.board)
        
        # Check groups were merged correctly
        self.assertEqual(len(self.group_manager.group_stones[merged_id]), 3)
        self.assertIn((3, 3), self.group_manager.group_stones[merged_id])
        self.assertIn((3, 4), self.group_manager.group_stones[merged_id])
        self.assertIn((3, 5), self.group_manager.group_stones[merged_id])
        
    def test_remove_group(self):
        """Test removing a group."""
        # Create a group
        self.board[5, 5] = BLACK
        group_id = self.group_manager.create_group(5, 5, BLACK, self.board)
        
        # Remove the group
        self.group_manager.remove_group(group_id)
        
        # Check group was removed
        with self.assertRaises(KeyError):
            self.group_manager.get_group_stones(group_id)
        self.assertIsNone(self.group_manager.get_group_id(5, 5))

if __name__ == '__main__':
    unittest.main() 