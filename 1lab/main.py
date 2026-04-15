import pygame as pg
import sys
from enum import Enum
from typing import Optional, List, Tuple
from abc import ABC, abstractmethod


class FigureCategory(Enum):
    INFANTRY = 1
    CASTLE = 2
    CAVALRY = 3
    CLERIC = 4
    ROYAL_ADVISOR = 5
    MONARCH = 6


class Team(Enum):
    LIGHT = 0
    DARK = 1


class GameAction:
    def __init__(self, unit, start_col: int, start_row: int, end_col: int, end_row: int,
                 action_kind: str, eliminated: Optional = None, castle_data: Optional = None):
        self.unit = unit
        self.sx = start_col
        self.sy = start_row
        self.ex = end_col
        self.ey = end_row
        self.kind = action_kind
        self.eliminated = eliminated
        self.castle = castle_data
        self.saved_state = {
            'moved': unit.moved,
            'double_step': unit.double_step if hasattr(unit, 'double_step') else None
        }


class MatchData:
    def __init__(self):
        self.field = [[None for _ in range(8)] for _ in range(8)]
        self.all_units = []
        self.light_ruler = None
        self.dark_ruler = None
        self.active_team = Team.LIGHT
        self.action_log = []
        self.record = []
        self.previous = None
        self.move_counter = 1
        self.finished = False
        self.champion = None
        self.en_passant_spot = None

    def change_turn(self):
        self.active_team = Team.DARK if self.active_team == Team.LIGHT else Team.LIGHT
        if self.active_team == Team.LIGHT:
            self.move_counter += 1
        self.en_passant_spot = None

    def get_unit(self, col: int, row: int):
        if 0 <= col < 8 and 0 <= row < 8:
            return self.field[row][col]
        return None

    def get_ruler(self, team: Team):
        return self.light_ruler if team == Team.LIGHT else self.dark_ruler


class GameUnit(ABC):
    def __init__(self, match: MatchData, kind: FigureCategory, col: int, row: int, team: Team):
        self.match = match
        self.kind = kind
        self.x = col
        self.y = row
        self.team = team
        self.moved = False
        self.active = True

    def get_icon(self) -> str:
        icons = {
            (FigureCategory.MONARCH, Team.LIGHT): "♔",
            (FigureCategory.ROYAL_ADVISOR, Team.LIGHT): "♕",
            (FigureCategory.CASTLE, Team.LIGHT): "♖",
            (FigureCategory.CLERIC, Team.LIGHT): "♗",
            (FigureCategory.CAVALRY, Team.LIGHT): "♘",
            (FigureCategory.INFANTRY, Team.LIGHT): "♙",
            (FigureCategory.MONARCH, Team.DARK): "♚",
            (FigureCategory.ROYAL_ADVISOR, Team.DARK): "♛",
            (FigureCategory.CASTLE, Team.DARK): "♜",
            (FigureCategory.CLERIC, Team.DARK): "♝",
            (FigureCategory.CAVALRY, Team.DARK): "♞",
            (FigureCategory.INFANTRY, Team.DARK): "♟",
        }
        return icons.get((self.kind, self.team), "?")

    @abstractmethod
    def can_reach(self, target_x: int, target_y: int) -> bool:
        pass

    def perform_move(self, dest_x: int, dest_y: int) -> bool:
        if not self.can_reach(dest_x, dest_y):
            return False

        captured = self.match.get_unit(dest_x, dest_y)
        action = GameAction(self, self.x, self.y, dest_x, dest_y, 'normal', captured)

        self.match.field[self.y][self.x] = None
        if captured:
            captured.active = False
            self.match.all_units.remove(captured)

        old_x, old_y = self.x, self.y
        self.x = dest_x
        self.y = dest_y
        self.match.field[self.y][self.x] = self
        self.moved = True

        if self.kind == FigureCategory.INFANTRY and abs(dest_y - old_y) == 2:
            self.match.en_passant_spot = (dest_x, (old_y + dest_y) // 2)

        if self.kind == FigureCategory.INFANTRY and (self.y == 0 or self.y == 7):
            self._transform()

        self.match.action_log.append(action)
        self.match.record.append(self._format_action(action))
        self.match.previous = (action.sx, action.sy, dest_x, dest_y)

        self.match.change_turn()
        self._check_ending()

        return True

    def _format_action(self, action: GameAction) -> str:
        start = chr(action.sx + 97) + str(8 - action.sy)
        end = chr(action.ex + 97) + str(8 - action.ey)
        symbol = self.get_icon()
        return f"{symbol}{start}-{end}"

    def _transform(self):
        transform_map = {
            "QUEEN": FigureCategory.ROYAL_ADVISOR,
            "KNIGHT": FigureCategory.CAVALRY,
            "BISHOP": FigureCategory.CLERIC,
            "ROOK": FigureCategory.CASTLE
        }
        choice = "QUEEN"
        new_unit = create_unit(self.match, transform_map[choice], self.x, self.y, self.team)
        self.match.field[self.y][self.x] = new_unit
        self.match.all_units.remove(self)
        self.match.all_units.append(new_unit)

    def _check_ending(self):
        ruler = self.match.get_ruler(self.match.active_team)
        if ruler and self._is_mate(ruler):
            self.match.finished = True
            self.match.champion = Team.LIGHT if self.match.active_team == Team.DARK else Team.DARK

    def _is_mate(self, ruler):
        if not self._square_threatened(ruler.x, ruler.y, ruler.team):
            return False

        for unit in self.match.all_units:
            if unit.team == ruler.team and unit.active:
                for row in range(8):
                    for col in range(8):
                        if unit.can_reach(col, row):
                            if self._move_saves(unit, col, row, ruler):
                                return False
        return True

    def _move_saves(self, unit, to_x, to_y, ruler):
        old_x, old_y = unit.x, unit.y
        captured = self.match.get_unit(to_x, to_y)

        self.match.field[old_y][old_x] = None
        if captured:
            self.match.all_units.remove(captured)
        unit.x, unit.y = to_x, to_y
        self.match.field[to_y][to_x] = unit

        in_check = self._square_threatened(ruler.x, ruler.y, ruler.team)

        unit.x, unit.y = old_x, old_y
        self.match.field[old_y][old_x] = unit
        self.match.field[to_y][to_x] = captured
        if captured:
            self.match.all_units.append(captured)

        return not in_check

    def _square_threatened(self, col: int, row: int, team: Team) -> bool:
        for unit in self.match.all_units:
            if unit.team != team and unit.active:
                if unit._can_attack(col, row):
                    return True
        return False

    def _can_attack(self, col: int, row: int) -> bool:
        return self.can_reach(col, row)

    def _path_free(self, target_x: int, target_y: int) -> bool:
        dx = 0 if target_x == self.x else (1 if target_x > self.x else -1)
        dy = 0 if target_y == self.y else (1 if target_y > self.y else -1)

        cur_x, cur_y = self.x + dx, self.y + dy
        while (cur_x, cur_y) != (target_x, target_y):
            if self.match.get_unit(cur_x, cur_y) is not None:
                return False
            cur_x += dx
            cur_y += dy
        return True


class Infantry(GameUnit):
    def __init__(self, match: MatchData, col: int, row: int, team: Team):
        super().__init__(match, FigureCategory.INFANTRY, col, row, team)
        self.double_step = 0

    def can_reach(self, target_x: int, target_y: int) -> bool:
        direction = 1 if self.team == Team.LIGHT else -1
        dx = target_x - self.x
        dy = target_y - self.y

        if dx == 0 and dy == -direction:
            return self.match.get_unit(target_x, target_y) is None

        if dx == 0 and dy == -2 * direction and not self.moved:
            mid_y = self.y - direction
            return (self.match.get_unit(target_x, target_y) is None and
                    self.match.get_unit(target_x, mid_y) is None)

        if abs(dx) == 1 and dy == -direction:
            target = self.match.get_unit(target_x, target_y)
            if target and target.team != self.team:
                return True

            if self.match.en_passant_spot == (target_x, self.y):
                return True

        return False


class Castle(GameUnit):
    def __init__(self, match: MatchData, col: int, row: int, team: Team):
        super().__init__(match, FigureCategory.CASTLE, col, row, team)

    def can_reach(self, target_x: int, target_y: int) -> bool:
        if (self.x == target_x) != (self.y == target_y):
            if self._path_free(target_x, target_y):
                target = self.match.get_unit(target_x, target_y)
                return target is None or target.team != self.team
        return False


class Cavalry(GameUnit):
    def __init__(self, match: MatchData, col: int, row: int, team: Team):
        super().__init__(match, FigureCategory.CAVALRY, col, row, team)

    def can_reach(self, target_x: int, target_y: int) -> bool:
        dx = abs(target_x - self.x)
        dy = abs(target_y - self.y)
        if (dx == 2 and dy == 1) or (dx == 1 and dy == 2):
            target = self.match.get_unit(target_x, target_y)
            return target is None or target.team != self.team
        return False


class Cleric(GameUnit):
    def __init__(self, match: MatchData, col: int, row: int, team: Team):
        super().__init__(match, FigureCategory.CLERIC, col, row, team)

    def can_reach(self, target_x: int, target_y: int) -> bool:
        if abs(target_x - self.x) == abs(target_y - self.y):
            if self._path_free(target_x, target_y):
                target = self.match.get_unit(target_x, target_y)
                return target is None or target.team != self.team
        return False


class RoyalAdvisor(GameUnit):
    def __init__(self, match: MatchData, col: int, row: int, team: Team):
        super().__init__(match, FigureCategory.ROYAL_ADVISOR, col, row, team)

    def can_reach(self, target_x: int, target_y: int) -> bool:
        if (self.x == target_x) != (self.y == target_y) or abs(target_x - self.x) == abs(target_y - self.y):
            if self._path_free(target_x, target_y):
                target = self.match.get_unit(target_x, target_y)
                return target is None or target.team != self.team
        return False


class Monarch(GameUnit):
    def __init__(self, match: MatchData, col: int, row: int, team: Team):
        super().__init__(match, FigureCategory.MONARCH, col, row, team)
        if team == Team.LIGHT:
            match.light_ruler = self
        else:
            match.dark_ruler = self

    def can_reach(self, target_x: int, target_y: int) -> bool:
        dx = abs(target_x - self.x)
        dy = abs(target_y - self.y)

        if max(dx, dy) == 1:
            target = self.match.get_unit(target_x, target_y)
            if (target is None or target.team != self.team) and not self._square_threatened(target_x, target_y, self.team):
                return True

        if not self.moved and dy == 0 and dx == 2:
            rook_x = 0 if target_x == 2 else 7
            rook = self.match.get_unit(rook_x, self.y)
            if (rook and rook.kind == FigureCategory.CASTLE and not rook.moved and
                not self._square_threatened(self.x, self.y, self.team)):
                step = -1 if target_x == 2 else 1
                for pos in range(self.x + step, target_x + step, step):
                    if self.match.get_unit(pos, self.y) is not None:
                        return False
                    if self._square_threatened(pos, self.y, self.team):
                        return False
                return True

        return False

    def _square_threatened(self, col: int, row: int, team: Team) -> bool:
        for unit in self.match.all_units:
            if unit.team != team and unit.active:
                if unit._can_attack(col, row):
                    return True
        return False


def create_unit(match: MatchData, kind: FigureCategory, col: int, row: int, team: Team):
    creators = {
        FigureCategory.INFANTRY: Infantry,
        FigureCategory.CASTLE: Castle,
        FigureCategory.CAVALRY: Cavalry,
        FigureCategory.CLERIC: Cleric,
        FigureCategory.ROYAL_ADVISOR: RoyalAdvisor,
        FigureCategory.MONARCH: Monarch,
    }
    creator = creators.get(kind)
    if creator:
        unit = creator(match, col, row, team)
        match.all_units.append(unit)
        match.field[row][col] = unit
        return unit
    return None


class ChessEngine:
    def __init__(self):
        pg.init()
        self.data = MatchData()
        self.display = pg.display.set_mode((1000, 700))
        pg.display.set_caption("Chess Master")
        self.clock = pg.time.Clock()
        self.selected = None
        self.available_spots = []
        self.threatened_units = []
        self.is_running = True
        self.in_menu = True
        self.history_stack = []

        self._load_assets()
        self._setup_field()

    def _load_assets(self):
        try:
            self.piece_font = pg.font.SysFont("segoeuisymbol", 64)
            if self.piece_font is None:
                self.piece_font = pg.font.Font(None, 64)
            self.big_font = pg.font.Font(None, 72)
            self.title_font = pg.font.Font(None, 84)
            self.btn_font = pg.font.Font(None, 48)
            self.small_font = pg.font.Font(None, 36)
        except:
            self.piece_font = pg.font.Font(None, 64)
            self.big_font = pg.font.Font(None, 72)
            self.title_font = pg.font.Font(None, 84)
            self.btn_font = pg.font.Font(None, 48)
            self.small_font = pg.font.Font(None, 36)

        self.board_surface = self._create_board()

    def _create_board(self):
        board = pg.Surface((560, 560))
        shades = [(210, 180, 140), (140, 110, 70)]
        for row in range(8):
            for col in range(8):
                color = shades[(col + row) % 2]
                pg.draw.rect(board, color, (col * 70, row * 70, 70, 70))
        return board

    def _setup_field(self):
        back_line = [
            FigureCategory.CASTLE, FigureCategory.CAVALRY, FigureCategory.CLERIC,
            FigureCategory.ROYAL_ADVISOR, FigureCategory.MONARCH, FigureCategory.CLERIC,
            FigureCategory.CAVALRY, FigureCategory.CASTLE
        ]

        for col, kind in enumerate(back_line):
            create_unit(self.data, kind, col, 0, Team.DARK)
        for col in range(8):
            create_unit(self.data, FigureCategory.INFANTRY, col, 1, Team.DARK)
        for col in range(8):
            create_unit(self.data, FigureCategory.INFANTRY, col, 6, Team.LIGHT)
        for col, kind in enumerate(back_line):
            create_unit(self.data, kind, col, 7, Team.LIGHT)

    def start(self):
        while self.is_running:
            self._process_input()
            self._render()
            self.clock.tick(60)

        pg.quit()
        sys.exit()

    def _process_input(self):
        for ev in pg.event.get():
            if ev.type == pg.QUIT:
                if not self.in_menu:
                    self._save_record()
                self.is_running = False

            elif ev.type == pg.MOUSEBUTTONDOWN:
                if self.in_menu:
                    self._menu_click()
                elif not self.data.finished:
                    self._board_click()

            elif ev.type == pg.KEYDOWN:
                if not self.in_menu:
                    if ev.key == pg.K_z and (pg.key.get_mods() & pg.KMOD_CTRL):
                        self._undo_multiple()
                    elif ev.key == pg.K_ESCAPE:
                        self.in_menu = True

    def _menu_click(self):
        mx, my = pg.mouse.get_pos()

        start_btn = pg.Rect(400, 250, 200, 60)
        quit_btn = pg.Rect(400, 350, 200, 60)

        if start_btn.collidepoint(mx, my):
            self._reset_game()
        elif quit_btn.collidepoint(mx, my):
            self.is_running = False

    def _reset_game(self):
        self.data = MatchData()
        self.selected = None
        self.available_spots = []
        self.threatened_units = []
        self.history_stack = []
        self.in_menu = False
        self._setup_field()

    def _board_click(self):
        mx, my = pg.mouse.get_pos()
        grid_x = (mx - 220) // 70
        grid_y = (my - 70) // 70

        if not (0 <= grid_x < 8 and 0 <= grid_y < 8):
            return

        if self.selected is None:
            unit = self.data.get_unit(grid_x, grid_y)
            if unit and unit.team == self.data.active_team and unit.active:
                self.selected = unit
                self._find_moves(unit)
        else:
            if (grid_x, grid_y) in self.available_spots:
                self._save_state_to_history()
                if self.selected.perform_move(grid_x, grid_y):
                    self.selected = None
                    self.available_spots = []
                    self._update_threats()
            else:
                self.selected = None
                self.available_spots = []

    def _save_state_to_history(self):
        import copy
        state = {
            'field': [[self.data.field[row][col] for col in range(8)] for row in range(8)],
            'all_units': self.data.all_units.copy(),
            'action_log': self.data.action_log.copy(),
            'record': self.data.record.copy(),
            'move_counter': self.data.move_counter,
            'active_team': self.data.active_team,
            'en_passant_spot': self.data.en_passant_spot
        }
        self.history_stack.append(state)
        if len(self.history_stack) > 20:
            self.history_stack.pop(0)

    def _undo_multiple(self):
        if not self.history_stack:
            print("Nothing to undo!")
            return

        state = self.history_stack.pop()

        self.data.field = [[state['field'][row][col] for col in range(8)] for row in range(8)]
        self.data.all_units = state['all_units'].copy()
        self.data.action_log = state['action_log'].copy()
        self.data.record = state['record'].copy()
        self.data.move_counter = state['move_counter']
        self.data.active_team = state['active_team']
        self.data.en_passant_spot = state['en_passant_spot']
        self.data.finished = False
        self.data.champion = None

        for unit in self.data.all_units:
            unit.match = self.data

        self.selected = None
        self.available_spots = []
        self._update_threats()
        print(f"Undo completed. {len(self.history_stack)} states remaining")

    def _find_moves(self, unit):
        self.available_spots = []
        for row in range(8):
            for col in range(8):
                if unit.can_reach(col, row):
                    self.available_spots.append((col, row))

    def _update_threats(self):
        self.threatened_units = []
        current = self.data.active_team

        for unit in self.data.all_units:
            if unit.team == current and unit.active:
                if unit._square_threatened(unit.x, unit.y, unit.team):
                    self.threatened_units.append(unit)

    def _save_record(self):
        try:
            with open('game_record.txt', 'w', encoding='utf-8') as f:
                for i, move in enumerate(self.data.record, 1):
                    num = (i + 1) // 2
                    if i % 2 == 1:
                        f.write(f"{num:2}. {move:15}")
                    else:
                        f.write(f"{move}\n")
                if len(self.data.record) % 2 == 1:
                    f.write("\n")
        except Exception as e:
            print(f"Error saving record: {e}")

    def _render(self):
        self.display.fill((30, 30, 40))

        if self.in_menu:
            self._draw_menu()
        else:
            self._draw_game()

        pg.display.flip()

    def _draw_menu(self):
        title = self.title_font.render("CHESS MASTER", True, (255, 200, 100))
        title_rect = title.get_rect(center=(500, 150))
        self.display.blit(title, title_rect)

        start_btn = pg.Rect(400, 250, 200, 60)
        quit_btn = pg.Rect(400, 350, 200, 60)

        pg.draw.rect(self.display, (60, 150, 60), start_btn)
        pg.draw.rect(self.display, (150, 60, 60), quit_btn)

        start_text = self.btn_font.render("START", True, (255, 255, 255))
        start_rect = start_text.get_rect(center=start_btn.center)
        self.display.blit(start_text, start_rect)

        quit_text = self.btn_font.render("QUIT", True, (255, 255, 255))
        quit_rect = quit_text.get_rect(center=quit_btn.center)
        self.display.blit(quit_text, quit_rect)

    def _draw_game(self):
        self.display.blit(self.board_surface, (220, 70))

        for row in range(8):
            for col in range(8):
                unit = self.data.get_unit(col, row)
                if unit:
                    cell_x = 220 + col * 70
                    cell_y = 70 + row * 70
                    piece_text = self.piece_font.render(unit.get_icon(), True, (255, 255, 255))
                    piece_rect = piece_text.get_rect()
                    piece_rect.center = (cell_x + 35, cell_y + 35)
                    self.display.blit(piece_text, piece_rect)

                if self.selected and (col, row) in self.available_spots:
                    self._draw_marker(col, row, (100, 255, 100, 128))

        if self.selected:
            self._draw_marker(self.selected.x, self.selected.y, (255, 255, 0, 150))

        for unit in self.threatened_units:
            self._draw_marker(unit.x, unit.y, (255, 50, 50, 150))

        self._draw_info()

        if self.data.finished:
            self._draw_result()

    def _draw_marker(self, col, row, color):
        marker = pg.Surface((70, 70), pg.SRCALPHA)
        if len(color) == 4:
            r, g, b, a = color
            marker.fill((r, g, b, a))
        else:
            marker.fill(color)
            marker.set_alpha(128)
        self.display.blit(marker, (220 + col * 70, 70 + row * 70))

    def _draw_info(self):
        turn_txt = f"Turn: {'WHITE' if self.data.active_team == Team.LIGHT else 'BLACK'}"
        text = self.small_font.render(turn_txt, True, (255, 255, 255))
        self.display.blit(text, (20, 50))

        move_txt = f"Move #{self.data.move_counter}"
        text = self.small_font.render(move_txt, True, (255, 255, 255))
        self.display.blit(text, (20, 100))

        pg.draw.line(self.display, (70, 70, 90), (10, 150), (190, 150), 2)

        controls = [
            "Commands:",
            "Ctrl+Z - undo (multi-step)",
            "ESC - menu"
        ]

        y = 170
        for line in controls:
            text = self.small_font.render(line, True, (170, 170, 210))
            self.display.blit(text, (20, y))
            y += 30

        threat_txt = f"Threatened: {len(self.threatened_units)}"
        text = self.small_font.render(threat_txt, True, (255, 140, 0))
        self.display.blit(text, (20, 290))

        undo_txt = f"Undo states: {len(self.history_stack)}"
        text = self.small_font.render(undo_txt, True, (100, 200, 255))
        self.display.blit(text, (20, 330))

        if self.data.record:
            last_txt = "Last move:"
            text = self.small_font.render(last_txt, True, (200, 200, 100))
            self.display.blit(text, (20, 370))

            last_move = self.data.record[-1]
            text = self.small_font.render(last_move, True, (220, 220, 220))
            self.display.blit(text, (20, 400))

    def _draw_result(self):
        cover = pg.Surface((1000, 700))
        cover.set_alpha(200)
        cover.fill((0, 0, 0))
        self.display.blit(cover, (0, 0))

        winner_txt = f"{'WHITE' if self.data.champion == Team.LIGHT else 'BLACK'} WINS!"
        text = self.big_font.render(winner_txt, True, (255, 200, 50))
        text_rect = text.get_rect(center=(500, 300))
        self.display.blit(text, text_rect)

        restart_txt = self.small_font.render("Press ESC for menu", True, (200, 200, 200))
        restart_rect = restart_txt.get_rect(center=(500, 400))
        self.display.blit(restart_txt, restart_rect)


def main():
    ChessEngine().start()


if __name__ == "__main__":
    main()
