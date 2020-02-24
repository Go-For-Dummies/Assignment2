"""
This evaluation function
Eye for color: 4 points
Neareye for color: 2 point
Move blocked for opponent by capture of color's stone(s): 2 points
"""

EYEPOINTS = 4
NEAREYEPOINTS = 2
CAPTUREPOINTS = 2
DEBUGMODE = False

import numpy as np
from board_util import GoBoardUtil, BLACK, WHITE, EMPTY, BORDER, MAXSIZE
from simple_board import SimpleGoBoard

def point_to_coord(point, boardsize):
    """
    Transform point given as board array index 
    to (row, col) coordinate representation.
    Special case: PASS is not transformed
    """

    NS = boardsize + 1
    return divmod(point, NS)

def format_point(move):
    """
    Return move coordinates as a string such as 'a1', or 'pass'.
    """
    column_letters = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
    #column_letters = "abcdefghjklmnopqrstuvwxyz"
    row, col = move
    if not 0 <= row < MAXSIZE or not 0 <= col < MAXSIZE:
        raise ValueError
    return column_letters[col - 1] + str(row)

def eye_level(board, point, color):
    # Returns NEAREYEPOINTS if point is within 1 play of being an eye for color
    # Returns EYEPOINTS if point is an eye for color
    # Returns negative values for eyes or near-eyes of opponent color
    # Returns 0 if point is neither an eye nor a near-eye
    nbs = board.neighbors[point]
    color_adjacent = 4 - len(nbs) # Less than 4 neighbors means edge or corner
    enemy_adjacent = 4 - len(nbs)
    for nb in nbs:
            nb_color = board.board[nb]
            if nb_color == color:
                color_adjacent += 1
                enemy_adjacent -= 1
            elif nb_color == GoBoardUtil.opponent(color):
                enemy_adjacent += 1
                color_adjacent -= 1
            else: #neighbor is empty
                if nb_color != EMPTY: print("Error: Unexpected value for nb_color: {}".format(nb_color))
    if color_adjacent == 3:
        if DEBUGMODE: print("Near eye for color at {}".format(format_point(point_to_coord(point, board.size))))
        return NEAREYEPOINTS
    elif color_adjacent == 4:
        if DEBUGMODE: print("Eye for color at {}".format(format_point(point_to_coord(point, board.size))))
        return EYEPOINTS
    elif enemy_adjacent == 3:
        if DEBUGMODE: print("Near eye for opponent at {}".format(format_point(point_to_coord(point, board.size))))
        return -NEAREYEPOINTS
    elif enemy_adjacent == 4:
        if DEBUGMODE: print("Eye for opponent at {}".format(format_point(point_to_coord(point, board.size))))
        return -EYEPOINTS
    return 0

def capture_level(board, point, color):
    """
    Returns CAPTUREPOINTS if point is a capture for opponent, but playable for color
    Returns -CAPTUREPOINTS if point is a capture for color, but playable for opponent
    Returns 0 otherwise
    """
    colorCapture = False
    oppCapture = False
    # First check for suicides
    bothColors = [color, GoBoardUtil.opponent(color)]
    for c in bothColors:
        board.board[point] = c
        if not board._stone_has_liberty(point):
            # check suicide of whole block
            block = board._block_of(point)
            if not board._has_liberty(block):
                board.board[point] = EMPTY #Reset point
                return 0
    # Next check if it's a capture
    board.board[point] = GoBoardUtil.opponent(color)
    if board._detect_captures(point, color):
        oppCapture = True
    board.board[point] = color
    if board._detect_captures(point, GoBoardUtil.opponent(color)):
        colorCapture = True
    board.board[point] = EMPTY #Reset point
    if oppCapture == True and colorCapture == False:
        if DEBUGMODE: print("OppCapture at {}".format(format_point(point_to_coord(point, board.size))))
        return CAPTUREPOINTS
    if oppCapture == False and colorCapture == True:
        if DEBUGMODE: print("colorCapture at {}".format(format_point(point_to_coord(point, board.size))))
        return -CAPTUREPOINTS
    return 0

def statisticaly_evaluate(board, color, CaptureMode = False):
    """
    Calculates an integer score for how advantageous the board is for
    player color. Score is determined by how many empty points are
    only playable for one player, or are within 1 move of being only
    playable for one player.
    """
    spaces = board.get_empty_points()
    score = 0
    for point in spaces:
        eyeScore = eye_level(board, point, color)
        score += eyeScore
        if eyeScore == 0 and CaptureMode is True:
            score += capture_level(board, point, color)
    return score
