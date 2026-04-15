import copy
import sys

class Piece:
    def __init__(self, color):
        self.color = color
        self.symbol = '?'
        self.has_moved = False

    def get_moves(self, board, r, c):
        return []

    def get_ray_moves(self, board, r, c, directions, max_steps=7):
        moves = []
        for dr, dc in directions:
            for step in range(1, max_steps + 1):
                nr, nc = r + dr * step, c + dc * step
                if not (0 <= nr < 8 and 0 <= nc < 8): break
                target = board.get_piece(nr, nc)
                if target is None:
                    moves.append((nr, nc))
                else:
                    if target.color != self.color:
                        moves.append((nr, nc))
                    break
        return moves

class Pawn(Piece):
    def __init__(self, color):
        super().__init__(color)
        self.symbol = 'P' if color == 'white' else 'p'

    def get_moves(self, board, r, c):
        moves = []
        direction = -1 if self.color == 'white' else 1
        start_row = 6 if self.color == 'white' else 1
        
        if 0 <= r + direction < 8 and board.get_piece(r + direction, c) is None:
            moves.append((r + direction, c))
            if r == start_row and board.get_piece(r + 2 * direction, c) is None:
                moves.append((r + 2 * direction, c))
        
        for dc in [-1, 1]:
            if 0 <= r + direction < 8 and 0 <= c + dc < 8:
                target = board.get_piece(r + direction, c + dc)
                if target and target.color != self.color:
                    moves.append((r + direction, c + dc))
                
                last_move = board.last_move
                if last_move:
                    p, start, end = last_move
                    if isinstance(p, Pawn) and p.color != self.color:
                        if end == (r, c + dc) and abs(start[0] - end[0]) == 2:
                            moves.append((r + direction, c + dc))
        return moves

class Knight(Piece):
    def __init__(self, color):
        super().__init__(color)
        self.symbol = 'N' if color == 'white' else 'n'

    def get_moves(self, board, r, c):
        moves = []
        jumps = [(2,1), (1,2), (-1,2), (-2,1), (-2,-1), (-1,-2), (1,-2), (2,-1)]
        for dr, dc in jumps:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                target = board.get_piece(nr, nc)
                if target is None or target.color != self.color:
                    moves.append((nr, nc))
        return moves

class Bishop(Piece):
    def __init__(self, color):
        super().__init__(color)
        self.symbol = 'B' if color == 'white' else 'b'
    def get_moves(self, board, r, c):
        return self.get_ray_moves(board, r, c, [(-1,-1), (-1,1), (1,-1), (1,1)])

class Rook(Piece):
    def __init__(self, color):
        super().__init__(color)
        self.symbol = 'R' if color == 'white' else 'r'
    def get_moves(self, board, r, c):
        return self.get_ray_moves(board, r, c, [(-1,0), (1,0), (0,-1), (0,1)])

class Queen(Piece):
    def __init__(self, color):
        super().__init__(color)
        self.symbol = 'Q' if color == 'white' else 'q'
    def get_moves(self, board, r, c):
        return self.get_ray_moves(board, r, c, [(-1,-1), (-1,1), (1,-1), (1,1), (-1,0), (1,0), (0,-1), (0,1)])

class King(Piece):
    def __init__(self, color):
        super().__init__(color)
        self.symbol = 'K' if color == 'white' else 'k'
    def get_moves(self, board, r, c):
        return self.get_ray_moves(board, r, c, [(-1,-1), (-1,1), (1,-1), (1,1), (-1,0), (1,0), (0,-1), (0,1)], 1)

class Jester(Piece):
    def __init__(self, color):
        super().__init__(color)
        self.symbol = 'J' if color == 'white' else 'j'
    def get_moves(self, board, r, c):
        moves = []
        for dr, dc in [(-2,-2), (-2,2), (2,-2), (2,2)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                target = board.get_piece(nr, nc)
                if target is None or target.color != self.color:
                    moves.append((nr, nc))
        return moves

class Pegasus(Piece):
    def __init__(self, color):
        super().__init__(color)
        self.symbol = 'E' if color == 'white' else 'e'
    def get_moves(self, board, r, c):
        moves = []
        jumps = [(3,1), (1,3), (-1,3), (-3,1), (-3,-1), (-1,-3), (1,-3), (3,-1)]
        for dr, dc in jumps:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                target = board.get_piece(nr, nc)
                if target is None or target.color != self.color:
                    moves.append((nr, nc))
        return moves

class Cannon(Piece):
    def __init__(self, color):
        super().__init__(color)
        self.symbol = 'C' if color == 'white' else 'c'
    def get_moves(self, board, r, c):
        moves = []
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            jumped = False
            for step in range(1, 8):
                nr, nc = r + dr * step, c + dc * step
                if not (0 <= nr < 8 and 0 <= nc < 8): break
                target = board.get_piece(nr, nc)
                
                if not jumped:
                    if target is None:
                        moves.append((nr, nc))
                    else:
                        jumped = True
                else:
                    if target is not None:
                        if target.color != self.color:
                            moves.append((nr, nc))
                        break
        return moves

class Checker(Piece):
    def __init__(self, color):
        super().__init__(color)
        self.symbol = 'M' if color == 'white' else 'm'
    
    def get_moves(self, board, r, c):
        moves = []
        direction = -1 if self.color == 'white' else 1
        
        for dc in [-1, 1]:
            nr, nc = r + direction, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and board.get_piece(nr, nc) is None:
                moves.append((nr, nc))
                
        for dr in [-2, 2]:
            for dc in [-2, 2]:
                nr, nc = r + dr, c + dc
                mid_r, mid_c = r + dr//2, c + dc//2
                if 0 <= nr < 8 and 0 <= nc < 8:
                    if board.get_piece(nr, nc) is None:
                        mid_piece = board.get_piece(mid_r, mid_c)
                        if mid_piece and mid_piece.color != self.color:
                            moves.append((nr, nc))
        return moves

class Board:
    def __init__(self, mode="chess"):
        self._grid = [[None for _ in range(8)] for _ in range(8)]
        self.mode = mode
        self.current_turn = 'white'
        self._history = [] 
        self.last_move = None
        self.setup_board()

    def setup_board(self):
        if self.mode == "chess":
            order = [Cannon, Pegasus, Bishop, Queen, King, Bishop, Jester, Cannon]
            for c in range(8):
                self._grid[1][c] = Pawn('black')
                self._grid[6][c] = Pawn('white')
                self._grid[0][c] = order[c]('black')
                self._grid[7][c] = order[c]('white')
        elif self.mode == "checkers":
            for r in range(3):
                for c in range(8):
                    if (r + c) % 2 != 0: self._grid[r][c] = Checker('black')
            for r in range(5, 8):
                for c in range(8):
                    if (r + c) % 2 != 0: self._grid[6-(7-r)][c] = Checker('white')

    def get_piece(self, r, c):
        return self._grid[r][c]

    def save_state(self):
        state = {
            'grid': copy.deepcopy(self._grid),
            'turn': self.current_turn,
            'last_move': copy.deepcopy(self.last_move)
        }
        self._history.append(state)

    def undo(self):
        if not self._history:
            print("Некуда откатываться.")
            return False
        state = self._history.pop()
        self._grid = state['grid']
        self.current_turn = state['turn']
        self.last_move = state['last_move']
        print("Ход отменен.")
        return True

    def move(self, start_pos, end_pos):
        r1, c1 = start_pos
        r2, c2 = end_pos
        piece = self.get_piece(r1, c1)

        if not piece or piece.color != self.current_turn:
            print("Неверный выбор фигуры!")
            return False

        moves = piece.get_moves(self, r1, c1)
        if end_pos not in moves:
            print("Недопустимый ход!")
            return False

        self.save_state()

        if isinstance(piece, Pawn) and c1 != c2 and self.get_piece(r2, c2) is None:
            self._grid[r1][c2] = None 

        self._grid[r2][c2] = piece
        self._grid[r1][c1] = None
        piece.has_moved = True
        self.last_move = (piece, start_pos, end_pos)

        if isinstance(piece, Pawn) and (r2 == 0 or r2 == 7):
            print("Пешка превращается в Ферзя!")
            self._grid[r2][c2] = Queen(piece.color)

        if self.mode == "checkers" and abs(r1 - r2) == 2:
            self._grid[r1 + (r2 - r1)//2][c1 + (c2 - c1)//2] = None

        self.current_turn = 'black' if self.current_turn == 'white' else 'white'
        return True

    def parse_pos(self, pos_str):
        if len(pos_str) != 2: return None
        col = ord(pos_str[0].lower()) - ord('a')
        row = 8 - int(pos_str[1])
        if 0 <= row < 8 and 0 <= col < 8: return (row, col)
        return None

    def get_threatened_squares(self, color):
        threats = set()
        enemy = 'black' if color == 'white' else 'white'
        for r in range(8):
            for c in range(8):
                p = self.get_piece(r, c)
                if p and p.color == enemy:
                    for move in p.get_moves(self, r, c):
                        threats.add(move)
        return threats

    def display(self, highlights=None, show_threats_for=None):
        highlights = highlights or []
        threats = self.get_threatened_squares(show_threats_for) if show_threats_for else set()

        header = "    " + " ".join(f" {chr(ord('a') + c)} " for c in range(8))
        print(f"\n{header}")
        print("  " + "-" * 33)
        
        for r in range(8):
            row_cells = []
            for c in range(8):
                p = self.get_piece(r, c)
                pos = (r, c)
                
                symbol = p.symbol if p else '.'
                

                if pos in highlights:
                    cell = f"[{symbol}]" if p else " x "
                elif pos in threats and p and p.color == show_threats_for:
                    if isinstance(p, King): 
                        cell = f"*{symbol}*"
                    else: 
                        cell = f"!{symbol}!"
                else:
                    cell = f" {symbol} "
                
                row_cells.append(cell)
                
            row_str = f"{8 - r} | " + " ".join(row_cells)
            print(row_str)
            
        print("  " + "-" * 33)
        print(f"Ход: {'Белые' if self.current_turn == 'white' else 'Черные'}")

def main():
    mode = input("Выбери режим (chess/checkers): ").strip().lower()
    if mode not in ['chess', 'checkers']: mode = 'chess'
    
    board = Board(mode=mode)
    
    while True:
        board.display()
        print("\nКоманды:")
        print("Ход: 'e2 e4'")
        print("Откат: 'undo'")
        print("Подсказка ходов: 'hint e2'")
        print("Подсказка угроз: 'threats'")
        print("Выход: 'quit'")
        
        cmd = input("> ").strip().lower().split()
        if not cmd: continue
        
        if cmd[0] == 'quit':
            break
        elif cmd[0] == 'undo':
            board.undo()
        elif cmd[0] == 'threats':
            board.display(show_threats_for=board.current_turn)
            input("Нажми Enter, чтобы продолжить")
        elif cmd[0] == 'hint' and len(cmd) == 2:
            pos = board.parse_pos(cmd[1])
            if pos:
                piece = board.get_piece(*pos)
                if piece:
                    moves = piece.get_moves(board, *pos)
                    board.display(highlights=moves)
                    input("Нажми Enter, чтобы продолжить")
                else:
                    print("Клетка пуста.")
        elif len(cmd) == 2:
            start = board.parse_pos(cmd[0])
            end = board.parse_pos(cmd[1])
            if start and end:
                board.move(start, end)
            else:
                print("Неверный формат координат (пример: e2 e4)")
        else:
            print("Неизвестная команда.")

if __name__ == "__main__":
    main()
