"""
gtp_connection.py
Module for playing games of Go using GoTextProtocol

Parts of this code were originally based on the gtp module
in the Deep-Go project by Isaac Henrion and Amos Storkey
at the University of Edinburgh.
"""
import traceback
from sys import stdin, stdout, stderr
from board_util import GoBoardUtil, BLACK, WHITE, EMPTY, BORDER, PASS, \
                       MAXSIZE, TIMELIMIT, coord_to_point
import numpy as np
import re
import signal
from transposition_table import TranspositionTable, TTUtil
from heuristic import statisticaly_evaluate

class GtpConnection():

    def __init__(self, go_engine, board, debug_mode=False):
        """
        Manage a GTP connection for a Go-playing engine

        Parameters
        ----------
        go_engine:
            a program that can reply to a set of GTP commandsbelow
        board:
            Represents the current board state.
        """
        self._debug_mode = debug_mode
        self.go_engine = go_engine
        self.board = board
        self.commands = {
            "protocol_version": self.protocol_version_cmd,
            "quit": self.quit_cmd,
            "name": self.name_cmd,
            "boardsize": self.boardsize_cmd,
            "showboard": self.showboard_cmd,
            "clear_board": self.clear_board_cmd,
            "komi": self.komi_cmd,
            "version": self.version_cmd,
            "known_command": self.known_command_cmd,
            "genmove": self.genmove_cmd,
            "list_commands": self.list_commands_cmd,
            "play": self.play_cmd,
            "legal_moves": self.legal_moves_cmd,
            "solve": self.solve,
            "evaluate": self.evaluate,
            "checkhash": self.check_hash,
            "timelimit": self.timelimit,
            "gogui-rules_game_id": self.gogui_rules_game_id_cmd,
            "gogui-rules_board_size": self.gogui_rules_board_size_cmd,
            "gogui-rules_legal_moves": self.gogui_rules_legal_moves_cmd,
            "gogui-rules_side_to_move": self.gogui_rules_side_to_move_cmd,
            "gogui-rules_board": self.gogui_rules_board_cmd,
            "gogui-rules_final_result": self.gogui_rules_final_result_cmd,
            "gogui-analyze_commands": self.gogui_analyze_cmd
        }

        # used for argument checking
        # values: (required number of arguments,
        #          error message on argnum failure)
        self.argmap = {
            "boardsize": (1, 'Usage: boardsize INT'),
            "komi": (1, 'Usage: komi FLOAT'),
            "known_command": (1, 'Usage: known_command CMD_NAME'),
            "genmove": (1, 'Usage: genmove {w,b}'),
            "play": (2, 'Usage: play {b,w} MOVE'),
            "legal_moves": (1, 'Usage: legal_moves {w,b}'),
            "timelimit": (1, 'Usage: timelimit INT')
        }

    def write(self, data):
        stdout.write(data)

    def flush(self):
        stdout.flush()

    def start_connection(self):
        """
        Start a GTP connection.
        This function continuously monitors standard input for commands.
        """
        line = stdin.readline()
        while line:
            self.get_cmd(line)
            line = stdin.readline()

    def get_cmd(self, command):
        """
        Parse command string and execute it
        """
        if len(command.strip(' \r\t')) == 0:
            return
        if command[0] == '#':
            return
        # Strip leading numbers from regression tests
        if command[0].isdigit():
            command = re.sub("^\d+", "", command).lstrip()

        elements = command.split()
        if not elements:
            return
        command_name = elements[0]
        args = elements[1:]
        if self.has_arg_error(command_name, len(args)):
            return
        if command_name in self.commands:
            try:
                self.commands[command_name](args)
            except Exception as e:
                self.debug_msg("Error executing command {}\n".format(str(e)))
                self.debug_msg("Stack Trace:\n{}\n".
                               format(traceback.format_exc()))
                raise e
        else:
            self.debug_msg("Unknown command: {}\n".format(command_name))
            self.error('Unknown command')
            stdout.flush()

    def has_arg_error(self, cmd, argnum):
        """
        Verify the number of arguments of cmd.
        argnum is the number of parsed arguments
        """
        if cmd in self.argmap and self.argmap[cmd][0] != argnum:
            self.error(self.argmap[cmd][1])
            return True
        return False

    def debug_msg(self, msg):
        """ Write msg to the debug stream """
        if self._debug_mode:
            stderr.write(msg)
            stderr.flush()

    def error(self, error_msg):
        """ Send error msg to stdout """
        stdout.write('? {}\n\n'.format(error_msg))
        stdout.flush()

    def respond(self, response=''):
        """ Send response to stdout """
        stdout.write('= {}\n\n'.format(response))
        stdout.flush()

    def reset(self, size):
        """
        Reset the board to empty board of given size
        """
        self.board.reset(size)

    def board2d(self):
        return str(GoBoardUtil.get_twoD_board(self.board))

    def protocol_version_cmd(self, args):
        """ Return the GTP protocol version being used (always 2) """
        self.respond('2')

    def quit_cmd(self, args):
        """ Quit game and exit the GTP interface """
        self.respond()
        exit()

    def name_cmd(self, args):
        """ Return the name of the Go engine """
        self.respond(self.go_engine.name)

    def version_cmd(self, args):
        """ Return the version of the  Go engine """
        self.respond(self.go_engine.version)

    def clear_board_cmd(self, args):
        """ clear the board """
        self.reset(self.board.size)
        self.respond()

    def boardsize_cmd(self, args):
        """
        Reset the game with new boardsize args[0]
        """
        self.reset(int(args[0]))
        self.respond()

    def showboard_cmd(self, args):
        self.respond('\n' + self.board2d())

    def komi_cmd(self, args):
        """
        Set the engine's komi to args[0]
        """
        self.go_engine.komi = float(args[0])
        self.respond()

    def known_command_cmd(self, args):
        """
        Check if command args[0] is known to the GTP interface
        """
        if args[0] in self.commands:
            self.respond("true")
        else:
            self.respond("false")

    def list_commands_cmd(self, args):
        """ list all supported GTP commands """
        self.respond(' '.join(list(self.commands.keys())))

    def legal_moves_cmd(self, args):
        """
        List legal moves for color args[0] in {'b','w'}
        """
        board_color = args[0].lower()
        color = color_to_int(board_color)
        moves = GoBoardUtil.generate_legal_moves(self.board, color)
        gtp_moves = []
        for move in moves:
            coords = point_to_coord(move, self.board.size)
            gtp_moves.append(format_point(coords))
        sorted_moves = ' '.join(sorted(gtp_moves))
        self.respond(sorted_moves)

    def evaluate(self, args):
        """
        Calculates how advantageous the current board is for the current
        player and returns an integer score (higher is better)
        """
        score = statisticaly_evaluate(self.board, self.board.current_player)
        current = "black" if self.board.current_player == BLACK else "white"
        self.respond("{} for {}".format(score, current))

    def check_hash(self, args):
        """
        Prints hash for TT and then prints hash for 2D TT
        They should always be the same
        """
        tt = TranspositionTable(self.board.size)
        state_code = tt.code(self.board)
        print("1D code: {}".format(state_code))
        twoD_board = GoBoardUtil.get_twoD_board(self.board)
        print(twoD_board)
        twoD_code = tt.code_2d(twoD_board)
        print("2D code: {}".format(twoD_code))

    def timelimit(self, args):
        """
        Sets the maximum time to allow for genmove and solve commands
        """
        global TIMELIMIT
        TIMELIMIT = int(args[0])
        self.respond()

    def solve(self, args):
        """
        Responds "= winner move" with winning color as winner
        Only includes move if winner == current player
        """
        try:
            color = self.board.current_player
            global TIMELIMIT
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(TIMELIMIT))
            tt = TranspositionTable(self.board.size)
            board_copy = self.board.copy()
            solution = negamax(board_copy, tt)
            signal.alarm(0)
            win, move = solution
            if not win:
                color = GoBoardUtil.opponent(color)
            winner = "b" if color == BLACK else "w"
            if move == 0:
                self.respond("{}".format(winner))
            else:
                move = point_to_coord(move, self.board.size)
                move = format_point(move).lower()
                self.respond("{} {}".format(winner, move))
        except TimeoutError:
            self.respond("unknown")

    def play_cmd(self, args):
        """
        play a move args[1] for given color args[0] in {'b','w'}
        """
        try:
            board_color = args[0].lower()
            board_move = args[1]
            if board_color != "b" and board_color != "w":
                self.respond(
                    "illegal move: \"{}\" wrong color".format(board_color))
                return
            color = color_to_int(board_color)
            if args[1].lower() == 'pass':
                self.respond(
                    "illegal move: \"{} {}\" wrong coordinate".format(args[0], args[1]))
                return
            coord = move_to_coord(args[1], self.board.size)
            if coord:
                move = coord_to_point(coord[0], coord[1], self.board.size)
            else:
                self.error("Error executing move {} converted from {}"
                           .format(move, args[1]))
                return
            if not self.board.play_move(move, color):
                self.respond("illegal move: \"{} {}\" ".format(
                    args[0], board_move))
                return
            else:
                self.debug_msg("Move: {}\nBoard:\n{}\n".
                               format(board_move, self.board2d()))
            self.respond()
        except Exception as e:
            self.respond('illegal move: \"{} {}\" {}'.format(
                args[0], args[1], str(e)))

    def genmove_cmd(self, args):
        """
        Generate a move for the color args[0] in {'b', 'w'}, for the game of gomoku.
        """
        global TIMELIMIT
        board_color = args[0].lower()
        color = color_to_int(board_color)
        if self.go_engine.get_move(self.board, color) is None:
            self.respond("resign")
            return
        else:
            try:
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(TIMELIMIT))
                tt = TranspositionTable(self.board.size)
                board_copy = self.board.copy()
                solution = negamax(board_copy, tt)
                signal.alarm(0)
                win, move = solution
                if not win:
                    self.genmove_random(color)
                else:
                    self.board.play_move(move, color)
                    move_coord = point_to_coord(move, self.board.size)
                    move_as_string = format_point(move_coord)
                    self.respond(move_as_string)
            except TimeoutError:
                self.genmove_random(color)

    def genmove_random(self, color):
        move = self.go_engine.get_move(self.board, color)
        move_coord = point_to_coord(move, self.board.size)
        move_as_string = format_point(move_coord)
        if self.board.is_legal(move, color):
            self.board.play_move(move, color)
            self.respond(move_as_string)

    def gogui_rules_game_id_cmd(self, args):
        self.respond("NoGo")

    def gogui_rules_board_size_cmd(self, args):
        self.respond(str(self.board.size))

    def legal_moves_cmd(self, args):
        """
            List legal moves for color args[0] in {'b','w'}
            """
        board_color = args[0].lower()
        color = color_to_int(board_color)
        moves = GoBoardUtil.generate_legal_moves(self.board, color)
        gtp_moves = []
        for move in moves:
            coords = point_to_coord(move, self.board.size)
            gtp_moves.append(format_point(coords))
        sorted_moves = ' '.join(sorted(gtp_moves))
        self.respond(sorted_moves)

    def gogui_rules_legal_moves_cmd(self, args):
        empties = self.board.get_empty_points()
        color = self.board.current_player
        legal_moves = []
        for move in empties:
            if self.board.is_legal(move, color):
                legal_moves.append(move)

        gtp_moves = []
        for move in legal_moves:
            coords = point_to_coord(move, self.board.size)
            gtp_moves.append(format_point(coords))
        sorted_moves = ' '.join(sorted(gtp_moves))
        self.respond(sorted_moves)

    def gogui_rules_side_to_move_cmd(self, args):
        color = "black" if self.board.current_player == BLACK else "white"
        self.respond(color)

    def gogui_rules_board_cmd(self, args):
        size = self.board.size
        str = ''
        for row in range(size-1, -1, -1):
            start = self.board.row_start(row + 1)
            for i in range(size):
                point = self.board.board[start + i]
                if point == BLACK:
                    str += 'X'
                elif point == WHITE:
                    str += 'O'
                elif point == EMPTY:
                    str += '.'
                else:
                    assert False
            str += '\n'
        self.respond(str)

    def gogui_rules_final_result_cmd(self, args):
        empties = self.board.get_empty_points()
        color = self.board.current_player
        legal_moves = []
        for move in empties:
            if self.board.is_legal(move, color):
                legal_moves.append(move)
        if not legal_moves:
            result = "black" if self.board.current_player == WHITE else "white"
        else:
            result = "unknown"
        self.respond(result)

    def gogui_analyze_cmd(self, args):
        self.respond("pstring/Legal Moves For ToPlay/gogui-rules_legal_moves\n"
                     "pstring/Side to Play/gogui-rules_side_to_move\n"
                     "pstring/Final Result/gogui-rules_final_result\n"
                     "pstring/Board Size/gogui-rules_board_size\n"
                     "pstring/Rules GameID/gogui-rules_game_id\n"
                     "pstring/Show Board/gogui-rules_board\n"
                     )


def negamax(board, tt, bbl = [], wbl = [], bneyes = [], wneyes = [], beyes = [], weyes = [],
            weight = None, HeuristicMode = True, SymmetryCheck = True):
    """
    Simple boolean negamax implementation with transposition table optimization

    Returns (true, winning_move) if current player can win with perfect play
    Else returns (false, 0) if current player will lose against perfect play
    Does not prune symmetrically or implement heuristics, simple DFS only.
    Runs full tree instead of using hash table to reduce to a (much smaller) DAG
    """
    # Check transposition table to see whether we have encountered this position
    state_code = tt.code(board)
    ret = tt.lookup(state_code)
    if ret is not None: 
        return ret
    if SymmetryCheck is True:
        # Check symmetrical equivalents of current board position
        twoD_board = GoBoardUtil.get_twoD_board(board)
        symmetries = TTUtil.symmetries(twoD_board)
        for tdb in symmetries:
            code = tt.code_2d(tdb)
            ret = tt.lookup(code)
            if ret is not None:
                return ret
    current_color = board.current_player
    empty_points = list(board.get_empty_points())
    if current_color is BLACK: # Remove known illegal moves
        for pt in bbl:
            if pt in empty_points:
                empty_points.remove(pt)
    if current_color is WHITE:
        for pt in wbl:
            if pt in empty_points:
                empty_points.remove(pt)
  
    if len(empty_points) == 0:
        return tt.store(state_code, (False, 0))

    if HeuristicMode is True:
        if weight is None:
            [weight, bneyes, wneyes, beyes, weyes] = statisticaly_evaluate(board, current_color)
        ordered_moves = []
        for move in empty_points: # Heuristic check to order moves
            board.fast_play_move(move, current_color)
            (newweight, newbneyes, newwneyes, newbeyes, newweyes) = statisticaly_evaluate(board, current_color, move, 
                                                    weight, list(bneyes), list(wneyes), list(beyes), list(weyes))
            board.undo_move(move, current_color)
            ordered_moves.append((move, newweight, newbneyes, newwneyes, newbeyes, newweyes))
        ordered_moves.sort(key=lambda weighted: -weighted[1])

        for (move, nw, bne, wne, be, we) in ordered_moves:
            try: # Illegal moves will raise ValueError
                board.play_move(move, current_color)
                isWin = not negamax(board, tt, list(bbl), list(wbl), bne, wne, be, we, -nw)[0]
                board.undo_move(move, current_color)
                if isWin:
                    return tt.store(state_code, (True, move))
            except ValueError: # Add illegal move to bl so we don't try it again
                if current_color is BLACK:
                    bbl.append(move)
                if current_color is WHITE:
                    wbl.append(move)

    else:
        for move in empty_points:
            try: # Illegal moves will raise ValueError
                board.play_move(move, current_color)
                isWin = not negamax(board, tt, list(bbl), list(wbl))[0]
                board.undo_move(move, current_color)
                if isWin:
                    return tt.store(state_code, (True, move))
            except ValueError: # Add illegal move to bl so we don't try it again
                if current_color is BLACK:
                    bbl.append(move)
                if current_color is WHITE:
                    wbl.append(move)
    
    return tt.store(state_code, (False, 0))


def timeout_handler(signum, frame):
    raise TimeoutError

def point_to_coord(point, boardsize):
    """
    Transform point given as board array index
    to (row, col) coordinate representation.
    Special case: PASS is not transformed
    """
    if point == PASS:
        return PASS
    else:
        NS = boardsize + 1
        return divmod(point, NS)


def format_point(move):
    """
    Return move coordinates as a string such as 'a1', or 'pass'.
    """
    column_letters = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
    #column_letters = "abcdefghjklmnopqrstuvwxyz"
    if move == PASS:
        return "pass"
    row, col = move
    if not 0 <= row < MAXSIZE or not 0 <= col < MAXSIZE:
        raise ValueError
    return column_letters[col - 1] + str(row)


def move_to_coord(point_str, board_size):
    """
    Convert a string point_str representing a point, as specified by GTP,
    to a pair of coordinates (row, col) in range 1 .. board_size.
    Raises ValueError if point_str is invalid
    """
    if not 2 <= board_size <= MAXSIZE:
        raise ValueError("board_size out of range")
    s = point_str.lower()
    if s == "pass":
        return PASS
    try:
        col_c = s[0]
        if (not "a" <= col_c <= "z") or col_c == "i":
            raise ValueError
        col = ord(col_c) - ord("a")
        if col_c < "i":
            col += 1
        row = int(s[1:])
        if row < 1:
            raise ValueError
    except (IndexError, ValueError):
        # e.g. "a0"
        raise ValueError("wrong coordinate")
    if not (col <= board_size and row <= board_size):
        # e.g. "a20"
        raise ValueError("wrong coordinate")
    return row, col


def color_to_int(c):
    """convert character to the appropriate integer code"""
    color_to_int = {"b": BLACK, "w": WHITE, "e": EMPTY,
                    "BORDER": BORDER}
    return color_to_int[c]
