from classes import PuzzleV2
import time
import pickle
import os
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
puzzles_file_path = os.path.join(BASE_DIR, 'aux_files', 'puzzles_generated.puzzle')


def update_puzzlesV2_file(puzzlesV2_arr):
    puzzles_file = open(puzzles_file_path, "wb")
    pickle.dump(puzzlesV2_arr, puzzles_file)
    puzzles_file.close()

success_read = False
while not success_read:
    try:
        puzzles_file = open(puzzles_file_path, 'rb')
        puzzles_arrV2 = pickle.load(puzzles_file)
        puzzles_file.close()
        success_read = True
    except:
        time.sleep(random.random()*1)


new_puzzlesV2 = []
for puzzle in puzzles_arrV2:
    new_puzzle = puzzle
    new_puzzle.counterTotal = 0
    new_puzzle.counterPassed = 0
    new_puzzle.difficulty = 200  # %
    new_puzzle.dificulty = 200
    new_puzzlesV2.append(new_puzzle)

random.shuffle(new_puzzlesV2)

update_puzzlesV2_file(new_puzzlesV2)
