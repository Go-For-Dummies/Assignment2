import random
import numpy as np
from board_util import EMPTY, BORDER


class TranspositionTable:
    """
    Zobrist-like transposition table for Go/Nogo. 

    Each position on the board is assigned a random integer on
    (0 - MAX_ZOBRIST_RANDOM). MAX_ZOBRIST_RANDOM is python maximum 
    integer divided by 2.

    Because there is only 2 possible pieces for each 
    position (black==1 or white==2), the board hash is caclulated by 
    taking the random integer for that position, multiplying it by the
    integer value of the piece at that position, and xor with the previous
    code value. 
    """
    # MAX_ZOBRIST_RANDOM = 1073741823
    MAX_ZOBRIST_RANDOM = 4611686018427387903    

    def __init__(self, size):
        self.table = {}
        self.board_size = size
        self.zobrist_table = np.zeros(shape=(size, size), dtype=np.int64)
        for i in range(size):
            for j in range(size):
                self.zobrist_table[i, j] = random.randint(
                    0, TranspositionTable.MAX_ZOBRIST_RANDOM)

    def code(self, board):
        c = 0
        for i in range(self.board_size):
            for j in range(self.board_size):
                point = board.pt(i+1, j+1)
                color = board.get_color(point)
                if color is not EMPTY and color is not BORDER:
                    c = c ^ (self.zobrist_table[i, j] * color)
        return c

    def code_2d(self, board2d):
        c = 0
        for i in range(len(board2d)):
            for j in range(len(board2d)):
                color = board2d[i, j]
                if color is not EMPTY and color is not BORDER:
                    c = c ^ (self.zobrist_table[i, j] * color)
        return c

    def lookup(self, code):
        if code in self.table:
            return self.table[code]
        else:
            return None

    def store(self, code, data):
        self.table[code] = data
        return data

class TTUtil(object):
    @staticmethod
    def symmetries(twoD_array):
        arrays = [twoD_array]
        for i in range(3): # Each rotation is a symmetrical board
            twoD_array = np.rot90(twoD_array)
            arrays.append(twoD_array)
        for i in range(4): # Each rotation flipped across x axis is symmetrical
            arrays.append(np.fliplr(arrays[i]))
        return arrays
