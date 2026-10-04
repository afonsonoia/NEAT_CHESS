from aux_PGN_reader import get_pgn_at_index, count_games, get_full_paths_in_folder
import os
from classes import PuzzleV2, generateSortValuePuzzlesV2
import chess.pgn
import pickle
from io import StringIO
import time
from stockfish import Stockfish
from aux_funcs_random import create_continue_file, check_continue_file, get_current_time_str_print, timeout, terminate_process_by_name

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
processed_moves_path = os.path.join(BASE_DIR, 'aux_files', 'processed_moves.fens')

if os.path.isfile(processed_moves_path):
    processed_file = open(processed_moves_path, 'rb')
    arr_processed_fens_raw = pickle.load(processed_file)
    processed_file.close()

    arr_processed_fens = arr_processed_fens_raw[0] + arr_processed_fens_raw[1]

    for fen in arr_processed_fens:
        print("fen:", fen)





