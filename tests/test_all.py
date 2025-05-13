"""
Test all modules in the tests directory.
"""

import sys
import os

# Add the parent directory to sys.path so Python can find the weiqi_py module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from test_board import TestBoard, TestGroupManager
from test_game import TestGame
from test_move import TestMove
from test_sgf import TestSGFNode, TestSGFParser
from test_utils import TestUtils


def run_tests():
    """Run all tests in the tests directory."""
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestBoard))
    suite.addTest(unittest.makeSuite(TestGroupManager))
    """suite.addTest(unittest.makeSuite(TestGame))
    suite.addTest(unittest.makeSuite(TestMove))
    suite.addTest(unittest.makeSuite(TestSGFNode))
    suite.addTest(unittest.makeSuite(TestSGFParser))
    suite.addTest(unittest.makeSuite(TestUtils))"""
    runner = unittest.TextTestRunner()
    runner.run(suite)

if __name__ == "__main__":
    run_tests()