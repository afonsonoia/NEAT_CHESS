import pickle
import os
import time
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
puzzles_file_path = os.path.join(BASE_DIR, 'aux_files', 'puzzles_generated.puzzle')


def remove_puzzle_by_fen(arr_puzzlesV2, fen):
    index_to_remove = -1
    for c_i in range(len(arr_puzzlesV2)):
        for i in range(len(arr_puzzlesV2[c_i])):
            if arr_puzzlesV2[c_i][i].get_fen() == fen:
                index_to_remove = i
                print("Sucess!")
                break
    if index_to_remove == -1:
        print("couldn't find fen to remove in array - remove_puzzle_by_fen()")
        return

    arr_puzzlesV2[0].pop(index_to_remove)
    return arr_puzzlesV2


def update_puzzlesV2_file(puzzlesV2_arr):
    os.makedirs(os.path.dirname(puzzles_file_path), exist_ok=True)
    puzzles_file = open(puzzles_file_path, "wb")
    pickle.dump(puzzlesV2_arr, puzzles_file)
    puzzles_file.close()


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

fen = input("Fen to exclude: ")
puzzles_arrV2 = remove_puzzle_by_fen(puzzles_arrV2, fen)

update_puzzlesV2_file(puzzles_arrV2)








