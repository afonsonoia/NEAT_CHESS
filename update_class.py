from classes import PuzzleV2
import time
import pickle
import os
from classes import *
import random
from stockfish import Stockfish
from aux_funcs_random import create_continue_file, check_continue_file

puzzles_file_path = r'aux_files/puzzles_generated.puzzle'


def update_puzzlesV2_file(puzzlesV2_arr):
    puzzles_file = open(puzzles_file_path, "wb")
    pickle.dump(puzzlesV2_arr, puzzles_file)
    puzzles_file.close()


sucess_read = False
while not sucess_read:
    try:
        puzzles_file = open(puzzles_file_path, 'rb')
        puzzles_arrV2 = pickle.load(puzzles_file)
        puzzles_file.close()
        sucess_read = True
    except:
        time.sleep(random.random()*1)

new_arr_puzzles = [[], []]
counter = 0
for old_puzzle in puzzles_arrV2[0]:
    counter += 1
    print(f"updating puzzle: {counter}/{len(puzzles_arrV2[0])}")
    fen = old_puzzle.get_fen()
    best_move_str = old_puzzle.get_best_move_str()
    depth_checked = old_puzzle.depth_checked
    new_arr_puzzles[0].append(PuzzleV2(fen=fen, best_move_str=best_move_str, white=True, depth_checked=depth_checked))

print("\nSaving to file...")
update_puzzlesV2_file(new_arr_puzzles)
print("\nFinished!")
