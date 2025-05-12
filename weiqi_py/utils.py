"""
Utility functions for coordinate conversion between board coordinates and SGF format.
"""

from typing import Tuple
from .board import GoError

class UtilsError(GoError):
    """Base exception for utility-related errors."""
    pass

def coord_to_sgf(y: int, x: int, board_size: int) -> str:
    """
    Convert board coordinates to SGF format.
    
    Args:
        y (int): Row coordinate (1-based)
        x (int): Column coordinate (1-based)
        board_size (int): Size of the board
        
    Returns:
        str: SGF coordinate string (e.g., 'ab' for coordinates (1,2))
        
    Raises:
        UtilsError: If coordinates are out of board range
    """
    if not (1 <= y <= board_size) or not (1 <= x <= board_size): 
        raise UtilsError(f"Coordinates ({y},{x}) out of range for board size {board_size}")
    col = chr(ord('a') + x - 1)
    row = chr(ord('a') + y - 1)
    return col + row

def sgf_to_coord(sgf: str, board_size: int) -> Tuple[int, int]:
    """
    Convert SGF format to board coordinates.
    
    Args:
        sgf (str): SGF coordinate string (e.g., 'ab' for coordinates (1,2))
        board_size (int): Size of the board
        
    Returns:
        Tuple[int, int]: Board coordinates (row, col) in 1-based indexing
        
    Raises:
        UtilsError: If SGF string is invalid or coordinates are out of range
    """
    if not sgf or len(sgf) < 2: 
        raise UtilsError("SGF coordinate string is too short")
    try:
        col = ord(sgf[0]) - ord('a') + 1
        row = ord(sgf[1]) - ord('a') + 1
        if not (1 <= col <= board_size) or not (1 <= row <= board_size):
            raise UtilsError(f"Converted coordinates ({row},{col}) out of range for board size {board_size}")
        return row, col
    except (IndexError, TypeError):
        raise UtilsError(f"Invalid SGF coordinate format: {sgf}")