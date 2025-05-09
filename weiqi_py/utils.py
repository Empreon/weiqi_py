def coord_to_sgf(y:int, x:int, board_size:int) -> str:
    """Convert board coordinates to SGF format"""
    if not (1 <= y <= board_size) or not (1 <= x <= board_size):
        raise ValueError(f"Coordinates ({y},{x}) out of range for board size {board_size}")
    col = chr(ord('a') + x - 1)
    row = chr(ord('a') + board_size - y)
    return col + row

def sgf_to_coord(sgf:str, board_size:int) -> tuple[int, int]:
    """Convert SGF format to board coordinates"""
    if not sgf or len(sgf) < 2: raise ValueError("SGF coordinate string is too short")
    try:
        col = ord(sgf[0]) - ord('a') + 1
        row = board_size - (ord(sgf[1]) - ord('a'))
        if not (1 <= col <= board_size) or not (1 <= row <= board_size):
            raise ValueError(f"Converted coordinates ({row},{col}) out of range for board size {board_size}")
        return row, col
    except (IndexError, TypeError):
        raise ValueError(f"Invalid SGF coordinate format: {sgf}")