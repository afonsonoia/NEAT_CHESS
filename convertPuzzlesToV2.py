import pickle
from classes import *

# -------------------------------------------

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
puzzles_file_path = os.path.join(BASE_DIR, 'aux_files', 'puzzles_generated.puzzle')

puzzles_file = open(puzzles_file_path, 'rb')
puzzles_arr = pickle.load(puzzles_file)
puzzles_file.close()
del puzzles_file

newPuzzlesStruct = []

for p in puzzles_arr:
    newPuzzle = PuzzleV2(p.fen, p.best_move_str, white=True, depth_checked=p.depth_checked)
    newPuzzlesStruct.append(newPuzzle)

# -------------------------------------------

puzzlesV2_file = open(puzzles_file_path, 'wb')
pickle.dump(newPuzzlesStruct, puzzlesV2_file)
puzzlesV2_file.close()
