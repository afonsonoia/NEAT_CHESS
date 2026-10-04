
print(5*"\n")


def runStockfish(stockfish, fen, nmoves):
    stockfish.set_fen_position(fen)
    top_stockfish_moves = stockfish.get_top_moves(nmoves)
    return top_stockfish_moves


import os.path
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from classes import PuzzleV2, generateSortValuePuzzlesV2
import chess.pgn
from aux_funcs_random import create_continue_file, check_continue_file
from aux_chess_funcs import get_all_legal_moves_raw
import time
import random
from stockfish import Stockfish
import pickle

PUZZLE_GENERATOR = True
DISPLAY_MODE = True
DEBUG_PUZZLES = False

NIGHT_MODE = True
delays_night = 5
small_delay = 1

MAX_MOVES_MATE_PUZZLES = 12
DEPTH_stockfish = 30
THREADS = 1

CENTIPAWN_MIN_DIFERENCE_PUZZLE = 120

DISPLAY_EVERY_N_MOVES = 1

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
engine_path = os.path.join(BASE_DIR, 'stockfish_16', 'stockfish-windows-x86-64-avx2.exe')

stockfish_stronger = Stockfish(path=engine_path, depth=DEPTH_stockfish, parameters={"Threads": THREADS})

puzzles_file_path = os.path.join(BASE_DIR, 'aux_files', 'puzzles_generated.puzzle')

puzzles_arr = [[], []]

if PUZZLE_GENERATOR:
    DISPLAY_MODE = False

if os.path.isfile(puzzles_file_path):
    puzzles_file = open(puzzles_file_path, 'rb')
    puzzles_arr = pickle.load(puzzles_file)
    puzzles_file.close()

create_continue_file()

num_games = -1
num_puzzles_found = [0]
while check_continue_file():
    board = chess.Board()

    num_games += 1
    # DISPLAY
    print(f"\nGames: {num_games}\n")
    print(f"Puzzles found  W: {num_puzzles_found[0]}")
    print(f"Total puzzles  W: {len(puzzles_arr[0])}\n")
    print(100 * "-" + '\n')
    turn_ = 0
    move_counter = 0
    while not board.outcome():
        if move_counter%2 == 0:
            if (move_counter/2) % DISPLAY_EVERY_N_MOVES == 0:
                print(int(move_counter/2))
            time.sleep(small_delay)

        move_counter += 1
        if not check_continue_file():
            exit()

        move_made = False
        possible_moves = get_all_legal_moves_raw(board)

        if not board.turn:
            random_index = random.randint(0, len(possible_moves) - 1)
            board.push(possible_moves[random_index])
            continue

        new_puzzle = None

        if PUZZLE_GENERATOR:

            # check the current board position for possible puzzle
            current_depth = DEPTH_stockfish + 2
            finished = False
            while not finished:
                current_depth -= 2
                stockfish_aux = Stockfish(path=engine_path, depth=current_depth, parameters={"Threads": THREADS})
                with ThreadPoolExecutor() as executor:
                    future = executor.submit(runStockfish, stockfish_aux, board.fen(), 5)
                    try:
                        result = future.result(timeout=120)
                        top_stockfish_moves = result
                        finished = True
                        break
                    except TimeoutError:
                        # If the function did not complete within the timeout
                        print(f"Stockfish timed out - retrying with {current_depth}")

            if NIGHT_MODE:
                time.sleep(delays_night)

            # check results
            if DEBUG_PUZZLES:
                for t in top_stockfish_moves:
                    print(t)
            if len(top_stockfish_moves) >= 2:
                best_move = top_stockfish_moves[0]
                second_best = top_stockfish_moves[1]

                # --- checkmates ---
                if (best_move["Mate"] is not None) and (abs(best_move["Mate"]) <= 5):
                    if second_best["Mate"] is None:
                        print(" PUZZLE! ".center(100, " "))
                        print(board.fen())
                        print(best_move["Move"])
                        print(100 * "-" + '\n')
                        new_puzzle = PuzzleV2(board.fen(), best_move["Move"], board.turn)


                # general puzzle
                elif (best_move["Centipawn"] is not None) and (second_best["Centipawn"] is not None):
                    if abs(best_move["Centipawn"] - second_best["Centipawn"]) >= CENTIPAWN_MIN_DIFERENCE_PUZZLE:
                        print(" PUZZLE! ".center(100, " "))
                        print(board.fen())
                        print(best_move["Move"])
                        print(100 * "-" + '\n')
                        new_puzzle = PuzzleV2(board.fen(), best_move["Move"], board.turn)

            # if puzzle found
            aux_is_new = True
            if new_puzzle is not None:

                # check for doubled
                # check color
                if board.turn:
                    color = 0   # white
                    turn_ = 1
                else:
                    color = 1   # black
                    turn_ = 0
                for p in puzzles_arr[color]:
                    if p.get_fen() == board.fen():
                        # not a new puzzle
                        aux_is_new = False
                        print("NOT A NEW PUZZLE")

                # store puzzle
                if aux_is_new:
                    if board.turn:
                        num_puzzles_found[0] += 1
                        puzzles_arr[0].append(new_puzzle)
                    else:
                        num_puzzles_found[1] += 1
                        puzzles_arr[1].append(new_puzzle)
                    puzzles_arr[0].sort(key=generateSortValuePuzzlesV2) # sort
                    puzzles_file = open(puzzles_file_path, "wb")
                    pickle.dump(puzzles_arr, puzzles_file)
                    puzzles_file.close()
                    new_puzzle = None

                # continue using puzzle
                for move in possible_moves:
                    if move.__str__() == best_move["Move"]:
                        board.push(move)
                        if DEBUG_PUZZLES:
                            print("SUCESSFULLY PUSHED BEST MOVE")
                        move_made = True
                        break

        if DISPLAY_MODE:
            print("\n\n" + board.__str__() + "\n\n")

        if not move_made:
            decision = random.randint(0, len(possible_moves)-1)
            board.push(possible_moves[decision])
            if DISPLAY_MODE:
                time.sleep(1)



