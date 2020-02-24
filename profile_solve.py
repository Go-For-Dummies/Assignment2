import cProfile
from Nogo import Nogo
from gtp_connection import GtpConnection
from simple_board import SimpleGoBoard

board = SimpleGoBoard(7)
con = GtpConnection(Nogo(), board)

def solve():
    con.solve([])

def setup():
    con.boardsize_cmd(['4'])
    moves = [
        ('b', 'a4'),
        ('w', 'a2'),
        ('b', 'b1'),
        ('w', 'b3'),
        ('b', 'c2'),
        ('w', 'd1'),
        ('b', 'd3'),
    ]
    for m in moves:
        con.play_cmd(m)

setup()
cProfile.run("solve()", sort='cumtime')
