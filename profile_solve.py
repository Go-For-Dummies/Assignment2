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
        ('b', 'a4')
    ]
    for m in moves:
        con.play_cmd(m)

setup()
cProfile.run("solve()", sort='cumtime')
