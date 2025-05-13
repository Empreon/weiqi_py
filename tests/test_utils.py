"""
Tests for the utils module.
"""

import unittest
from weiqi_py.utils import coord_to_sgf, sgf_to_coord, UtilsError

class TestUtils(unittest.TestCase):
    def test_coord_to_sgf(self):
        """Test converting board coordinates to SGF format."""
        # Test standard conversions
        self.assertEqual(coord_to_sgf(1, 1, 19), "aa")
        self.assertEqual(coord_to_sgf(1, 19, 19), "sa")
        self.assertEqual(coord_to_sgf(19, 1, 19), "as")
        self.assertEqual(coord_to_sgf(19, 19, 19), "ss")
        
        # Test corner cases
        self.assertEqual(coord_to_sgf(1, 1, 9), "aa")
        self.assertEqual(coord_to_sgf(9, 9, 9), "ii")
        
        # Test different board sizes
        self.assertEqual(coord_to_sgf(5, 5, 13), "ee")
        self.assertEqual(coord_to_sgf(13, 13, 13), "mm")
        
        # Test invalid coordinates
        with self.assertRaises(UtilsError):
            coord_to_sgf(0, 1, 19)
        with self.assertRaises(UtilsError):
            coord_to_sgf(1, 0, 19)
        with self.assertRaises(UtilsError):
            coord_to_sgf(20, 1, 19)
        with self.assertRaises(UtilsError):
            coord_to_sgf(1, 20, 19)
            
    def test_sgf_to_coord(self):
        """Test converting SGF format to board coordinates."""
        # Test standard conversions
        self.assertEqual(sgf_to_coord("aa", 19), (1, 1))
        self.assertEqual(sgf_to_coord("sa", 19), (1, 19))
        self.assertEqual(sgf_to_coord("as", 19), (19, 1))
        self.assertEqual(sgf_to_coord("ss", 19), (19, 19))
        
        # Test corner cases
        self.assertEqual(sgf_to_coord("aa", 9), (1, 1))
        self.assertEqual(sgf_to_coord("ii", 9), (9, 9))
        
        # Test different board sizes
        self.assertEqual(sgf_to_coord("ee", 13), (5, 5))
        self.assertEqual(sgf_to_coord("mm", 13), (13, 13))
        
        # Test invalid SGF strings
        with self.assertRaises(UtilsError):
            sgf_to_coord("", 19)
        with self.assertRaises(UtilsError):
            sgf_to_coord("a", 19)
        with self.assertRaises(UtilsError):
            sgf_to_coord("ta", 19)  # 't' is outside 19x19 grid
        with self.assertRaises(UtilsError):
            sgf_to_coord("at", 19)  # 't' is outside 19x19 grid
            
    def test_coordinate_roundtrip(self):
        """Test converting coordinates back and forth."""
        # Test various board sizes
        board_sizes = [9, 13, 19]
        
        for size in board_sizes:
            for y in range(1, size + 1):
                for x in range(1, size + 1):
                    sgf = coord_to_sgf(y, x, size)
                    y2, x2 = sgf_to_coord(sgf, size)
                    self.assertEqual((y, x), (y2, x2))

if __name__ == '__main__':
    unittest.main() 