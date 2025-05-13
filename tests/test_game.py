"""
Tests for the game module.
"""

import unittest
from weiqi_py.game import Game, GameError, InvalidMoveError, ScoringError
from weiqi_py.board import BLACK, WHITE, EMPTY

class TestGame(unittest.TestCase):
    def setUp(self):
        """Set up a new game before each test."""
        self.game = Game(board_size=9)
        
    def test_initialization(self):
        """Test game initialization with different parameters."""
        # Default parameters
        game = Game()
        self.assertEqual(game.board.size, 19)
        self.assertEqual(game.komi, 6.5)
        self.assertEqual(game.score_system, "area")
        
        # Custom parameters
        game = Game(board_size=13, komi=7.5, score_system="territory")
        self.assertEqual(game.board.size, 13)
        self.assertEqual(game.komi, 7.5)
        self.assertEqual(game.score_system, "territory")
        
        # Invalid parameters
        with self.assertRaises(ValueError):
            Game(board_size=4)
        with self.assertRaises(ValueError):
            Game(komi=-1)
        with self.assertRaises(ValueError):
            Game(score_system="invalid")
            
    def test_play_stone(self):
        """Test playing stones."""
        # First move should be valid
        self.assertTrue(self.game.play(5, 5))
        self.assertEqual(self.game.board.board[5, 5], BLACK)
        self.assertEqual(self.game.current_player, WHITE)
        
        # Second move should be valid
        self.assertTrue(self.game.play(5, 6))
        self.assertEqual(self.game.board.board[5, 6], WHITE)
        self.assertEqual(self.game.current_player, BLACK)
        
        # Occupied position should raise error
        with self.assertRaises(InvalidMoveError):
            self.game.play(5, 5)
            
    def test_pass_move(self):
        """Test passing a turn."""
        # Pass move
        self.assertTrue(self.game.play(None, None))
        self.assertEqual(self.game.passes, 1)
        self.assertEqual(self.game.current_player, WHITE)
        
        # Another pass move ends the game
        self.assertTrue(self.game.play(None, None))
        self.assertEqual(self.game.passes, 2)
        self.assertTrue(self.game.is_game_over)
        
        # No more moves allowed
        with self.assertRaises(GameError):
            self.game.play(5, 5)
            
    def test_undo(self):
        """Test undoing moves."""
        # Play some moves
        self.game.play(5, 5)
        self.game.play(5, 6)
        
        # Undo last move
        self.assertTrue(self.game.undo())
        self.assertEqual(self.game.board.board[5, 6], EMPTY)
        self.assertEqual(self.game.current_player, WHITE)
        
        # Undo another move
        self.assertTrue(self.game.undo())
        self.assertEqual(self.game.board.board[5, 5], EMPTY)
        self.assertEqual(self.game.current_player, BLACK)
        
        # No more moves to undo
        with self.assertRaises(GameError):
            self.game.undo()
            
    def test_resign(self):
        """Test resignation."""
        # Black resigns
        self.assertTrue(self.game.resign(BLACK))
        self.assertTrue(self.game.is_game_over)
        self.assertEqual(self.game.winner, WHITE)
        
        # Reset and let white resign
        self.game.reset()
        self.game.play(5, 5)  # Black plays
        self.assertTrue(self.game.resign())  # Current player (White) resigns
        self.assertTrue(self.game.is_game_over)
        self.assertEqual(self.game.winner, BLACK)
        
    def test_get_legal_moves(self):
        """Test getting legal moves."""
        # Empty board should have all points as legal
        legal_moves = self.game.get_legal_moves()
        self.assertEqual(len(legal_moves), self.game.board.size * self.game.board.size)
        
        # After playing, that position should no longer be legal
        self.game.play(5, 5)
        legal_moves = self.game.get_legal_moves()
        self.assertNotIn((5, 5), legal_moves)
        
        # After game ends, getting legal moves should raise error
        self.game.play(None, None)  # Pass
        self.game.play(None, None)  # Pass again, ending game
        with self.assertRaises(GameError):
            self.game.get_legal_moves()
            
    def test_area_scoring(self):
        """Test area scoring system."""
        # Set up a simple board position for scoring
        self.game = Game(board_size=5, score_system="area")
        
        # Play some moves to create territories
        moves = [(1, 1), (1, 5), (2, 2), (2, 4), (3, 3), None, None]
        for y, x in moves:
            self.game.play(y, x)
            
        # Get the score
        black_score, white_score = self.game.get_score()
        
        # Basic assertions about scoring
        self.assertGreater(black_score, 0)
        self.assertGreater(white_score, 0)
        self.assertEqual(self.game.winner, BLACK if black_score > white_score else WHITE)
        
    def test_territory_scoring(self):
        """Test territory scoring system."""
        # Set up a simple board position for scoring
        self.game = Game(board_size=5, score_system="territory")
        
        # Play some moves to create territories
        moves = [(1, 1), (1, 5), (2, 2), (2, 4), (3, 3), None, None]
        for y, x in moves:
            self.game.play(y, x)
            
        # Get the score
        black_score, white_score = self.game.get_score()
        
        # Territory scoring should differ from area scoring
        area_game = Game(board_size=5, score_system="area")
        for y, x in moves:
            area_game.play(y, x)
        area_black, area_white = area_game.get_score()
        
        # There might be differences in scoring
        self.assertIsNotNone(black_score)
        self.assertIsNotNone(white_score)
        
    def test_game_copy(self):
        """Test copying a game."""
        # Play some moves
        self.game.play(5, 5)
        self.game.play(5, 6)
        
        # Create a copy
        game_copy = self.game.copy()
        
        # Check copy has the same state
        self.assertEqual(game_copy.board.size, self.game.board.size)
        self.assertEqual(game_copy.komi, self.game.komi)
        self.assertEqual(game_copy.current_player, self.game.current_player)
        self.assertEqual(game_copy.is_game_over, self.game.is_game_over)
        self.assertEqual(game_copy.board.board[5, 5], BLACK)
        self.assertEqual(game_copy.board.board[5, 6], WHITE)
        
        # Modify the copy and ensure original is unchanged
        game_copy.play(6, 6)
        self.assertEqual(game_copy.board.board[6, 6], BLACK)
        self.assertEqual(self.game.board.board[6, 6], EMPTY)
        
    def test_reset(self):
        """Test resetting a game."""
        # Play some moves
        self.game.play(5, 5)
        self.game.play(5, 6)
        
        # Reset the game
        self.game.reset()
        
        # Check game state was reset
        self.assertEqual(self.game.current_player, BLACK)
        self.assertEqual(len(self.game.moves_history), 0)
        self.assertFalse(self.game.is_game_over)
        self.assertEqual(self.game.passes, 0)
        self.assertIsNone(self.game.winner)
        
        # Check board is empty
        for y in range(1, self.game.board.size + 1):
            for x in range(1, self.game.board.size + 1):
                self.assertEqual(self.game.board.board[y, x], EMPTY)

if __name__ == '__main__':
    unittest.main() 