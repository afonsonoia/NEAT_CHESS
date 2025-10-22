import pickle
import chess
import time
from stockfish import Stockfish
import os
import random
from classes import PuzzleV2, generateSortValuePuzzlesV2
from aux_chess_funcs import get_all_legal_moves_str


DEPTH_stockfish = 30
THREADS = 2

depth_insert_puzzle = 100   # puzzle value for depth

engine_path = r'./stockfish_16/stockfish-windows-x86-64-avx2.exe'
puzzles_file_path = r'aux_files/puzzles_generated.puzzle'

# stockfish setup
stockfish_stronger = Stockfish(path=engine_path, depth=DEPTH_stockfish, parameters={"Threads": THREADS})

new_fen = input("fen: ")

# check if already in database
if os.path.isfile(puzzles_file_path):
    sucess_read = False
    while not sucess_read:
        try:
            puzzles_file = open(puzzles_file_path, 'rb')
            puzzles_arrV2 = pickle.load(puzzles_file)
            puzzles_file.close()
            sucess_read = True
        except:
            time.sleep(random.random()*2)
else:
    puzzles_arrV2 = [[], []]

# check if it is a valid fen/best_move
try:
    board = chess.Board(fen=new_fen)
except:
    print("\nERROR: invalid fen")
    exit()

# check if puzzle already exists
for npuzzle in puzzles_arrV2[0]:
    told_fen = npuzzle.get_fen().split(' ')[0]
    tnew_fen = new_fen.split(' ')[0]
    if told_fen == tnew_fen:
        print("Not a new puzzle!")
        exit()

best_move = input("best move: ")

if best_move not in get_all_legal_moves_str(board):
    print("\nERROR: invalid best move")
    exit()

print("checking...")

new_puzzle = PuzzleV2(new_fen, best_move, True, depth_insert_puzzle)

# stockfish check
stockfish_stronger.set_fen_position(new_fen)
top_stockfish_moves = stockfish_stronger.get_top_moves(2)
found_match = False
for move in top_stockfish_moves:
    if move['Move'] == best_move:
        found_match = True
        break

if not found_match:
    print("\nWARNING: puzzle not correct according to stockfish\n")
    if input("Are you sure you want to insert it?\n") != "yes":
        exit()

puzzles_arrV2[0].append(new_puzzle)

print("inserting...")
time.sleep(3)

# save
sucess_write = False
while not sucess_write:
    try:
        puzzles_file = open(puzzles_file_path, 'wb')
        puzzles_arrV2[0].sort(key=generateSortValuePuzzlesV2)
        pickle.dump(puzzles_arrV2, puzzles_file)
        puzzles_file.close()
        sucess_write = True
    except:
        time.sleep(random.random()*1)

