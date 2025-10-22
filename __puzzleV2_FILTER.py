from classes import PuzzleV2
import time
import pickle
import os
import random
from stockfish import Stockfish
from aux_funcs_random import create_continue_file, check_continue_file

DEPTH = 32
THREADS = 8
increment = 4
CENTIPAWN_MIN_DIFERENCE_PUZZLE = 35

NIGHT_MODE = False
night_delay = 15

processed_file_path = r'./aux_files/processed_moves.fens'
puzzles_file_path = r'./aux_files/puzzles_generated.puzzle'
engine_path = r'./stockfish_16/stockfish-windows-x86-64-avx2.exe'


def remove_element_at_position(matrix, i):
    try:
        # Attempt to remove the element at the specified position
        matrix.pop(i)
    except IndexError:
        # Handle the case where the specified position is out of bounds
        print(f"Invalid position ({i}). List not modified.")
        exit()


def update_depth_by_fen(arr_puzzlesV2, fen, new_depth, sudo=False):
    index_to_update = -1
    for i in range(len(arr_puzzlesV2)):
        if arr_puzzlesV2[i].get_fen() == fen:
            index_to_update = i
            break
    if index_to_update == -1:
        print("couldn't find fen to remove in array - update_depth_by_fen()")
        return

    arr_puzzlesV2[index_to_update].update_depth_checked(new_depth, sudo=sudo)
    return arr_puzzlesV2


def remove_puzzle_by_fen(arr_puzzlesV2, fen):
    index_to_remove = -1
    for i in range(len(arr_puzzlesV2)):
        if arr_puzzlesV2[i].get_fen() == fen:
            index_to_remove = i
            break
    if index_to_remove == -1:
        print("couldn't find fen to remove in array - remove_puzzle_by_fen()")
        return

    print(f"Removed puzzle: {fen} ***** {arr_puzzlesV2[i].best_move_str}")
    arr_puzzlesV2.pop(index_to_remove)
    return arr_puzzlesV2


def update_puzzlesV2_file(puzzlesV2_arr):
    puzzles_file = open(puzzles_file_path, "wb")
    pickle.dump(puzzlesV2_arr, puzzles_file)
    puzzles_file.close()


if not os.path.isfile(puzzles_file_path):
    print("no file found")
    exit()

sucess_read = False
while not sucess_read:
    try:
        puzzles_file = open(puzzles_file_path, 'rb')
        puzzles_arrV2 = pickle.load(puzzles_file)
        puzzles_file.close()
        sucess_read = True
    except:
        time.sleep(random.random()*1)

sucess_read = False
while not sucess_read:
    try:
        processed_file = open(processed_file_path, 'rb')
        processed_arr = pickle.load(processed_file)
        processed_file.close()
        sucess_read = True
    except:
        time.sleep(random.random()*1)


lowerDepth = -1
amount = 0

for puzzle in puzzles_arrV2:
    if (lowerDepth == -1) or (puzzle.depth_checked < lowerDepth):
        lowerDepth = puzzle.depth_checked
        amount = 0
    if puzzle.depth_checked == lowerDepth:
        amount += 1

print(f"Lower depth found: {lowerDepth} - amount: {amount}")

if DEPTH <= lowerDepth:
    print("\nFinished")
    exit()


def runStockfish(stockfish, fen, nmoves):
    stockfish.set_fen_position(fen)
    top_stockfish_moves = stockfish.get_top_moves(nmoves)
    return top_stockfish_moves


depth_local = min(lowerDepth + increment, DEPTH)

stockfish_engine = Stockfish(path=engine_path, depth=depth_local, parameters={"Threads": THREADS})

print(f"Running depth: {depth_local}")

create_continue_file()

counter = 0
new_puzzles_arr_V2 = []


for p in puzzles_arrV2:
    new_puzzles_arr_V2.append(p)


while check_continue_file():
    index = -1
    puzzle = None

    if len(puzzles_arrV2) == 0:
        print("Finished")
        exit()

    for p in range(len(puzzles_arrV2)):
        index = p
        if puzzles_arrV2[index].depth_checked == lowerDepth:
            puzzle = puzzles_arrV2[index]
            remove_element_at_position(puzzles_arrV2, index)
            break

    if puzzle is None:
        print("Finished")
        exit()

    if NIGHT_MODE:
        time.sleep(night_delay)

    fen = puzzle.get_fen()

    # check CONTINUE file
    if not check_continue_file():
        print("Continue file - stopped")
        exit()

    # changed my mind about 100 depth for mates
    # if puzzle.depth_checked == 100:
    #    new_puzzles_arr_V2 = update_depth_by_fen(new_puzzles_arr_V2, fen, depth_local, sudo=True)
    #    update_puzzlesV2_file(new_puzzles_arr_V2)
    #    continue

    if puzzle.depth_checked == lowerDepth:
        counter += 1
        print(f"Checking: {counter}/{amount}")
        top_stockfish_moves = runStockfish(stockfish_engine, fen, 2)

        if top_stockfish_moves and len(top_stockfish_moves) >= 2:
            best_move = top_stockfish_moves[0]
            second_best = top_stockfish_moves[1]

            if best_move['Move'] != puzzle.get_best_move_str():

                print(f"Deleted (1): {fen}")
                new_puzzles_arr_V2 = remove_puzzle_by_fen(new_puzzles_arr_V2, fen)
                update_puzzlesV2_file(new_puzzles_arr_V2)
                continue

            if best_move["Mate"] is not None:
                new_puzzles_arr_V2 = update_depth_by_fen(new_puzzles_arr_V2, fen, depth_local)
                update_puzzlesV2_file(new_puzzles_arr_V2)
                continue

            if second_best["Mate"] is not None:
                new_puzzles_arr_V2 = remove_puzzle_by_fen(new_puzzles_arr_V2, fen)
                print(f"Deleted (3): {fen}")
                update_puzzlesV2_file(new_puzzles_arr_V2)
                continue

            elif abs(best_move["Centipawn"] - second_best["Centipawn"]) < CENTIPAWN_MIN_DIFERENCE_PUZZLE:
                new_puzzles_arr_V2 = remove_puzzle_by_fen(new_puzzles_arr_V2, fen)
                print(f"Deleted (2): {fen}")
                update_puzzlesV2_file(new_puzzles_arr_V2)
                continue

            # update new depth - passed all tests
            new_puzzles_arr_V2 = update_depth_by_fen(new_puzzles_arr_V2, fen, depth_local)
            update_puzzlesV2_file(new_puzzles_arr_V2)
            continue

        else:
            print("warning: don't know what to do")

