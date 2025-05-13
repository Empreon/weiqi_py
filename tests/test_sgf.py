"""
Tests for the sgf module.
"""

import unittest
import os
import tempfile
from weiqi_py.sgf import SGFNode, SGFParser
from weiqi_py.game import Game
from weiqi_py.board import BLACK, WHITE

class TestSGFNode(unittest.TestCase):
    def setUp(self):
        """Set up a new SGF node before each test."""
        self.node = SGFNode()
        
    def test_initialization(self):
        """Test node initialization."""
        self.assertEqual(self.node.properties, {})
        self.assertEqual(self.node.children, [])
        self.assertIsNone(self.node.parent)
        
        # Test node with parent
        parent = SGFNode()
        child = SGFNode(parent=parent)
        self.assertEqual(child.parent, parent)
        
    def test_add_property(self):
        """Test adding properties to a node."""
        # Add a single property
        self.node.add_property("SZ", "19")
        self.assertIn("SZ", self.node.properties)
        self.assertEqual(self.node.properties["SZ"], ["19"])
        
        # Add another value to the same property
        self.node.add_property("SZ", "9")
        self.assertEqual(self.node.properties["SZ"], ["19", "9"])
        
        # Add a different property
        self.node.add_property("KM", "6.5")
        self.assertIn("KM", self.node.properties)
        self.assertEqual(self.node.properties["KM"], ["6.5"])
        
    def test_get_property(self):
        """Test getting property values."""
        # No property should return default
        self.assertIsNone(self.node.get_property("SZ"))
        self.assertEqual(self.node.get_property("SZ", "19"), "19")
        
        # Add a property and get it
        self.node.add_property("SZ", "19")
        self.assertEqual(self.node.get_property("SZ"), "19")
        
        # Add another value and get the first one
        self.node.add_property("SZ", "9")
        self.assertEqual(self.node.get_property("SZ"), "19")
        
    def test_get_property_list(self):
        """Test getting a list of property values."""
        # No property should return empty list
        self.assertEqual(self.node.get_property_list("AB"), [])
        
        # Add properties and get them
        self.node.add_property("AB", "aa")
        self.node.add_property("AB", "bb")
        self.assertEqual(self.node.get_property_list("AB"), ["aa", "bb"])
        
    def test_has_property(self):
        """Test checking if a property exists."""
        self.assertFalse(self.node.has_property("SZ"))
        
        self.node.add_property("SZ", "19")
        self.assertTrue(self.node.has_property("SZ"))
        
    def test_add_child(self):
        """Test adding child nodes."""
        # Add a new child
        child1 = self.node.add_child()
        self.assertIsInstance(child1, SGFNode)
        self.assertEqual(child1.parent, self.node)
        self.assertEqual(len(self.node.children), 1)
        
        # Add another child
        child2 = self.node.add_child()
        self.assertEqual(len(self.node.children), 2)
        
        # Add an existing node as child
        existing_node = SGFNode()
        child3 = self.node.add_child(existing_node)
        self.assertEqual(child3, existing_node)
        self.assertEqual(len(self.node.children), 3)


class TestSGFParser(unittest.TestCase):
    def setUp(self):
        """Set up a parser before each test."""
        self.parser = SGFParser()
        self.sample_sgf = "(;GM[1]FF[4]SZ[19]CA[UTF-8];B[pd];W[dp];B[pp];W[dc])"
        
    def test_parse_sgf(self):
        """Test parsing SGF strings."""
        root = self.parser.parse_sgf(self.sample_sgf)
        
        # Check root properties
        self.assertEqual(root.get_property("GM"), "1")
        self.assertEqual(root.get_property("FF"), "4")
        self.assertEqual(root.get_property("SZ"), "19")
        
        # Check moves
        current = root
        move_sequence = []
        while current.children:
            current = current.children[0]
            if current.has_property("B"):
                move_sequence.append(("B", current.get_property("B")))
            elif current.has_property("W"):
                move_sequence.append(("W", current.get_property("W")))
                
        expected_moves = [("B", "pd"), ("W", "dp"), ("B", "pp"), ("W", "dc")]
        self.assertEqual(move_sequence, expected_moves)
        
    def test_parse_file(self):
        """Test parsing SGF from a file."""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
            temp.write(self.sample_sgf)
            temp.flush()
            temp_name = temp.name
            
        try:
            root = self.parser.parse_file(temp_name)
            
            # Check a few properties to verify parsing worked
            self.assertEqual(root.get_property("SZ"), "19")
            self.assertEqual(len(root.children), 1)
            self.assertEqual(root.children[0].get_property("B"), "pd")
        finally:
            os.unlink(temp_name)
            
    def test_sgf_to_game(self):
        """Test converting SGF to Game."""
        root = self.parser.parse_sgf(self.sample_sgf)
        game = self.parser.sgf_to_game(root)
        
        # Check game properties
        self.assertEqual(game.board.size, 19)
        self.assertEqual(len(game.moves_history), 4)
        
        # The board should reflect the moves
        # Convert SGF coords to board coords
        moves = [
            (16, 4),  # pd
            (4, 16),  # dp
            (16, 16), # pp
            (4, 4)    # dc
        ]
        
        # Check key stone placements
        self.assertEqual(game.board.board[moves[0][0], moves[0][1]], BLACK)
        self.assertEqual(game.board.board[moves[1][0], moves[1][1]], WHITE)
        self.assertEqual(game.board.board[moves[2][0], moves[2][1]], BLACK)
        self.assertEqual(game.board.board[moves[3][0], moves[3][1]], WHITE)
        
    def test_game_to_sgf(self):
        """Test converting Game to SGF."""
        # Create a game with some moves
        game = Game(board_size=9)
        game.play(3, 3)  # Black
        game.play(3, 6)  # White
        game.play(6, 3)  # Black
        game.play(6, 6)  # White
        
        # Convert to SGF
        sgf_string = self.parser.game_to_sgf(game)
        
        # Basic checks on the SGF string
        self.assertIn("SZ[9]", sgf_string)
        self.assertIn("B[cc]", sgf_string)  # 3,3 in SGF coordinates
        self.assertIn("W[cf]", sgf_string)  # 3,6 in SGF coordinates
        self.assertIn("B[fc]", sgf_string)  # 6,3 in SGF coordinates
        self.assertIn("W[ff]", sgf_string)  # 6,6 in SGF coordinates
        
        # Parse the generated SGF back to a game
        root = self.parser.parse_sgf(sgf_string)
        new_game = self.parser.sgf_to_game(root)
        
        # Check the new game
        self.assertEqual(new_game.board.size, 9)
        self.assertEqual(len(new_game.moves_history), 4)
        self.assertEqual(new_game.board.board[3, 3], BLACK)
        self.assertEqual(new_game.board.board[3, 6], WHITE)
        self.assertEqual(new_game.board.board[6, 3], BLACK)
        self.assertEqual(new_game.board.board[6, 6], WHITE)
        
    def test_save_sgf(self):
        """Test saving a game to an SGF file."""
        # Create a game with some moves
        game = Game(board_size=9)
        game.play(3, 3)  # Black
        game.play(3, 6)  # White
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp_name = temp.name
            
        try:
            self.assertTrue(self.parser.save_sgf(game, temp_name))
            
            # Read back the file
            with open(temp_name, 'r') as f:
                sgf_content = f.read()
                
            # Basic checks on the content
            self.assertIn("SZ[9]", sgf_content)
            self.assertIn("B[cc]", sgf_content)  # 3,3 in SGF coordinates
            self.assertIn("W[cf]", sgf_content)  # 3,6 in SGF coordinates
            
            # Parse the file and convert to game
            root = self.parser.parse_file(temp_name)
            loaded_game = self.parser.sgf_to_game(root)
            
            # Check the loaded game
            self.assertEqual(loaded_game.board.size, 9)
            self.assertEqual(loaded_game.board.board[3, 3], BLACK)
            self.assertEqual(loaded_game.board.board[3, 6], WHITE)
        finally:
            os.unlink(temp_name)
            
    def test_special_characters(self):
        """Test handling of special characters in SGF."""
        sgf_with_special = "(;C[This is a comment with special chars: \\] and \\\\];B[pd])"
        root = self.parser.parse_sgf(sgf_with_special)
        
        # Check the comment was parsed correctly with escapes handled
        self.assertEqual(root.get_property("C"), "This is a comment with special chars: ] and \\")
        
        # Regenerate SGF and check escaping is preserved
        game = self.parser.sgf_to_game(root)
        new_sgf = self.parser.game_to_sgf(game)
        
        # SGF should have properly escaped characters
        self.assertIn("\\]", new_sgf)
        self.assertIn("\\\\", new_sgf)

if __name__ == '__main__':
    unittest.main() 