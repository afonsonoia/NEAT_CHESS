from stockfish import Stockfish


DEPTH_stockfish = 38
THREADS = 8

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
engine_path = os.path.join(BASE_DIR, 'stockfish_16', 'stockfish-windows-x86-64-avx2.exe')
puzzles_file_path = os.path.join(BASE_DIR, 'aux_files', 'puzzles_generated.puzzle')

# stockfish setup
stockfish_stronger = Stockfish(path=engine_path, depth=DEPTH_stockfish, parameters={"Threads": THREADS})

new_fen = input("fen: ")


stockfish_stronger.set_fen_position(new_fen)
moves = stockfish_stronger.get_top_moves()

for move in moves:
    print(move)







