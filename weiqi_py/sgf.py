import re
from datetime import datetime
from .board import BLACK, WHITE, EMPTY
from .game import Game
from .utils import coord_to_sgf, sgf_to_coord

class SGFNode:
    def __init__(self, parent=None) -> None:
        self.properties = {}
        self.children = []
        self.parent = parent
        
    def add_property(self, key:str, value:str) -> None:
        """Add a property to the node"""
        if key not in self.properties: self.properties[key] = []
        self.properties[key].append(value)
        
    def get_property(self, key:str, default:str=None) -> str:
        """Get a property value by key"""
        if key in self.properties and self.properties[key]: return self.properties[key][0]
        return default
        
    def get_property_list(self, key:str) -> list[str]:
        """Get a list of property values by key"""
        if key in self.properties: return self.properties[key]
        return []
        
    def has_property(self, key:str) -> bool:
        """Check if the node has a property"""
        return key in self.properties
        
    def add_child(self, node=None) -> "SGFNode":
        """Add a child node"""
        if node is None: node = SGFNode(parent=self)
        self.children.append(node)
        return node


class SGFParser:
    def __init__(self) -> None: pass
        
    def parse_file(self, filepath:str) -> SGFNode:
        """Parse an SGF file"""
        with open(filepath, 'r', encoding='utf-8') as f: content = f.read()
        return self.parse_sgf(content)
        
    def parse_sgf(self, sgf_string:str) -> SGFNode:
        """Parse an SGF string"""
        sgf_string = re.sub(r'\s+', ' ', sgf_string)
        if sgf_string.count('(') > 1:
            parts = sgf_string.split('(')
            sgf_string = '(' + parts[1]
        sgf_string = sgf_string.strip()
        if sgf_string.startswith('('): sgf_string = sgf_string[1:]
        if sgf_string.endswith(')'): sgf_string = sgf_string[:-1]
        root = SGFNode()
        current_node = root
        nodes = re.split(r'(?<=[;\)])\s*(?=\[|;|\(|\))', sgf_string)
        for node in nodes:
            node = node.strip()
            if not node: continue
            if node.startswith(';'):
                if current_node != root: current_node = current_node.add_child()
                properties = re.findall(r'([A-Za-z]+)(?:\[(.*?)\])+', node)
                for key, value in properties:
                    value = value.replace('\\\\', '\\').replace('\\]', ']')
                    current_node.add_property(key, value)
            elif node.startswith('('):
                parent = current_node.parent or root
                current_node = parent.add_child()
            elif node == ')':
                if current_node.parent: current_node = current_node.parent
        return root
        
    def sgf_to_game(self, sgf_root:SGFNode) -> Game:
        """Convert an SGF game tree to a Game object"""
        board_size = 19
        if sgf_root.has_property('SZ'): board_size = int(sgf_root.get_property('SZ'))
        komi = 6.5
        if sgf_root.has_property('KM'):
            try: komi = float(sgf_root.get_property('KM'))
            except ValueError: pass
        game = Game(board_size=board_size, komi=komi)
        current_node = sgf_root
        if sgf_root.has_property('HA') and sgf_root.has_property('AB'):
            handicap = int(sgf_root.get_property('HA'))
            if handicap > 0:
                stones = sgf_root.get_property_list('AB')
                for stone in stones:
                    if not stone: continue
                    row, col = sgf_to_coord(stone, board_size)
                    if 1 <= row <= board_size and 1 <= col <= board_size: game.board.place_stone(row, col, BLACK)
                game.current_player = WHITE
        invalid_moves_count = 0
        while current_node.children:
            current_node = current_node.children[0]
            if current_node.has_property('B'):
                color = BLACK
                move_str = current_node.get_property('B')
            elif current_node.has_property('W'):
                color = WHITE
                move_str = current_node.get_property('W')
            else: continue
            if not move_str or move_str == '':
                if game.current_player == color: game.play(None, None)
                else: print(f"Warning: Skipping pass move for {color}, expected {game.current_player}")
                continue
            try:
                row, col = sgf_to_coord(move_str, board_size)
                if not (1 <= row <= board_size and 1 <= col <= board_size):
                    print(f"Warning: Invalid coordinates ({row},{col}), skipping")
                    invalid_moves_count += 1
                    continue
                if game.current_player != color:
                    print(f"Warning: Incorrect player turn (got {color}, expected {game.current_player}), skipping")
                    invalid_moves_count += 1
                    continue
                if not game.play(row, col):
                    print(f"Warning: Invalid move at ({row},{col}) for {color}, skipping")
                    invalid_moves_count += 1
            except Exception as e:
                print(f"Error processing move {move_str}: {e}")
                invalid_moves_count += 1
        if invalid_moves_count > 0: print(f"Completed parsing with {invalid_moves_count} invalid/skipped moves")
        return game
        
    def game_to_sgf(self, game:Game) -> str:
        """Convert a Game object to SGF format"""
        root = SGFNode()
        root.add_property('FF', '4')
        root.add_property('GM', '1')
        root.add_property('SZ', str(game.board.size))
        root.add_property('KM', str(game.komi))
        root.add_property('DT', datetime.now().strftime('%Y-%m-%d'))
        root.add_property('RU', 'Japanese')
        current_node = root
        current_color = BLACK
        for move in game.moves_history:
            node = SGFNode(parent=current_node)
            current_node.add_child(node)
            if move == "pass":
                if current_color == BLACK: node.add_property('B', '')
                else: node.add_property('W', '')
            elif move == "resign": pass
            else:
                y, x = move
                sgf_coord = coord_to_sgf(y, x, game.board.size)
                if current_color == BLACK: node.add_property('B', sgf_coord)
                else: node.add_property('W', sgf_coord)
            current_node = node
            current_color = BLACK if current_color == WHITE else WHITE
        if game.is_game_over:
            black_score, white_score = game.get_score()
            result = f"B+{black_score - white_score}" if black_score > white_score else f"W+{white_score - black_score}"
            root.add_property('RE', result)
        return self._generate_sgf(root)
        
    def _generate_sgf(self, node:SGFNode) -> str:
        """Generate SGF string from a node tree"""
        result = "("
        if node.properties:
            result += ";"
            for key, values in node.properties.items():
                for value in values:
                    escaped_value = value.replace('\\', '\\\\').replace(']', '\\]')
                    result += f"{key}[{escaped_value}]"
        if node.children:
            for child in node.children: result += self._generate_sgf(child)
        elif node.properties: pass    
        result += ")"
        return result
        
    def save_sgf(self, game:Game, filepath:str) -> bool:
        """Save a game to an SGF file"""
        sgf_string = self.game_to_sgf(game)
        try:
            with open(filepath, 'w', encoding='utf-8') as f: f.write(sgf_string)
            return True
        except Exception as e:
            print(f"Error saving SGF: {e}")
            return False 