from aux_PGN_reader import get_pgn_at_index, count_games, get_full_paths_in_folder
import os.path
from classes import PuzzleV2, generateSortValuePuzzlesV2
import chess.pgn
import time
import pickle
from io import StringIO
import time
from stockfish import Stockfish
from aux_funcs_random import create_continue_file, check_continue_file, get_current_time_str_print, timeout, terminate_process_by_name

puzzles_file_path = r'.\aux_files\puzzles_generated_white.puzzle'
processed_moves_path = r'.\aux_files\processed_moves.fens'

puzzles_arr = [[], []]
num_games = 0
num_puzzles_found = [0]
arr_processed_fens_raw = [[], []]   # processed / timeout

if os.path.isfile(puzzles_file_path):
    puzzles_file = open(puzzles_file_path, 'rb')
    puzzles_arr = pickle.load(puzzles_file)
    puzzles_file.close()

if os.path.isfile(processed_moves_path):
    processed_file = open(processed_moves_path, 'rb')
    arr_processed_fens_raw = pickle.load(processed_file)
    processed_file.close()

arr_processed_fens = arr_processed_fens_raw[0] + arr_processed_fens_raw[1]


print("Sucessfuly load data from files\n")
counter = 0
for white_puzzle in puzzles_arr[0]:
    time.sleep(0.05)
    counter+=1
    print("\n" + 70*"-" + "\n")
    print("game: " + str(counter))
    print(white_puzzle.get_fen())
    print(white_puzzle.get_best_move_str())


