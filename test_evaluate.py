from Nogo import Nogo
from gtp_connection import GtpConnection
from simple_board import SimpleGoBoard
from board_util import GoBoardUtil

board = SimpleGoBoard(7)
con = GtpConnection(Nogo(), board)

def evaluate():
    con.evaluate([])

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
    con.showboard_cmd([])
    con.evaluate([])
    con.boardsize_cmd(['9'])
    moves = [
        ('b', 'a1'),
        ('w', 'a2'),
        ('b', 'b1'),
        ('w', 'b3'),
        ('b', 'c3'),
        ('w', 'c1'),
        ('b', 'd2'),
        ('w', 'c2'),
        ('b', 'e2'),
        ('w', 'd3'),
        ('b', 'f3'),
        ('w', 'a4'),
        ('b', 'd4'),
        ('w', 'e4'),
        ('b', 'f4'),
        ('w', 'b5'),
        ('b', 'e5'),
        ('w', 'c5'),
        ('b', 'h5'),
        ('w', 'd5')
    ]

    for m in moves:
        con.play_cmd(m)
    con.showboard_cmd([])
    bard = GoBoardUtil.get_twoD_board(con.board)
    print(bard)
    con.evaluate([])
    con.play_cmd(('b', 'g2'))
    con.showboard_cmd([])
    con.evaluate([])
    con.play_cmd(('w', 'f1'))
    con.showboard_cmd([])
    con.evaluate([])

setup()
