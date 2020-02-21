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
    MAX_ZOBRIST_RANDOM = 1073741823

    def __init__(self, size):
        self.table = {}
        self.board_size = size
        self.zobrist_table = np.zeros(shape=(size, size), dtype=np.int32)
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

    def lookup(self, code):
        if code in self.table:
            return self.table[code]
        else:
            return None

    def store(self, code, data):
        self.table[code] = data