import pickle
import chess
import time
import os
import random
from classes import PuzzleV2, generateSortValuePuzzlesV2
from stockfish import Stockfish

DEPTH_stockfish = 24
THREADS = 2

engine_path = r'./stockfish_16/stockfish-windows-x86-64-avx2.exe'
puzzles_file_path = r'aux_files/puzzles_generated.puzzle'

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
    print("no file found")
    exit()

# stockfish setup
stockfish_stronger = Stockfish(path=engine_path, depth=DEPTH_stockfish, parameters={"Threads": THREADS})

print("starting checks\n")
print("checking white puzzles\n")

counter_puzzle = 1
for puzzle in puzzles_arrV2[0]:
    print(counter_puzzle)
    counter_puzzle += 1
    fen = puzzle.get_fen()
    best_move_puzzle = puzzle.get_best_move_str()

    # stockfish opinion
    stockfish_stronger.set_fen_position(fen)
    top_stockfish_moves = stockfish_stronger.get_top_moves(3)
    found_match = False
    for move in top_stockfish_moves:
        if move['Move'] == best_move_puzzle:
            found_match = True
            break

    if not found_match:
        print("WARNING: puzzle not correct according to stockfish")
        print(f"original puzzle: {fen} - {best_move_puzzle}\n")


