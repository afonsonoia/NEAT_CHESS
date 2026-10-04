import time
from stockfish import Stockfish
import chess
import classes
from classes import theoryData
from aux_chess_funcs import *
from aux_openings_massive_dict import getTheoryDB
from openings_theory import get_starting_moves_white, store_full_dict
from aux_funcs_random import get_current_time_str
from aux_funcs_random import create_continue_file, check_continue_file

NIGHT_MODE = True
night_delay = 2

DEBUG = False
BACKUP_N_MOVES = 50
CHECKED_N_MOVES = 1000
tread_num = 1

depth_stockfish = 40
depth_weak_stockfish = 16

max_n_moves_opening = 10

min_opening_moves = 6       # brute force first moves
num_max_options = 5         # after min_opening_moves

engine_path = r'stockfish_16/stockfish-windows-x86-64-avx2.exe'


board = chess.Board()
stockfish_stronger = Stockfish(path=engine_path, depth=depth_stockfish, parameters={"Threads": tread_num})
stockfish_weaker = Stockfish(path=engine_path, depth=depth_weak_stockfish, parameters={"Threads": tread_num})

create_continue_file()


def get_fen_from_uci(main_fen, uci_str):
    aux_board = chess.Board(main_fen)
    move = chess.Move.from_uci(uci_str)
    aux_board.push(move)
    new_fen = aux_board.fen()
    aux_board.pop()
    return new_fen


def get_fen_from_move(main_fen, move):
    aux_board = chess.Board(main_fen)
    aux_board.push(move)
    new_fen = aux_board.fen()
    aux_board.pop()
    return new_fen


def make_move(board, uci):
    move = chess.Move.from_uci(uci)
    board.push(move)
    return board


def short_fen(board):
    full_fen = board.fen()
    aux = full_fen.split('-')
    fen = aux[0][:-1]
    return fen


def debug_print(txt):
     t = get_current_time_str()
     print(str(t) + ' - ' + str(txt))

first_run = False

theory_dict = getTheoryDB()
if not theory_dict:
    theory_dict = theoryData()
    first_run = True


# Frontiers are lists of FENs
new_frontier = []

if theory_dict.getDataBaseDepth() > 0:
    new_frontier = theory_dict.getLastFrontier()

reachedNewContent = False

for nm in range(max_n_moves_opening):
    num_move = nm + 1

    if theory_dict.getDataBaseDepth() >= num_move:
        continue

    current_frontier = new_frontier
    new_frontier = []

    if first_run:
        first_run = False
        board = chess.Board()
        current_frontier = [board.fen()]
        total_analyzed = 0

    print(f"\n\nStart running move: {num_move} - total: {len(current_frontier)} - total analyzed pos: {theory_dict.getNumPosAnalyzed()}\n")

    current_level_n_moves_processed = 0
    for fen in current_frontier:
        old_frontier_size = len(current_frontier)   # to later insert into analyzed positions in DB

        cond1 = (not reachedNewContent) and (current_level_n_moves_processed % (10*BACKUP_N_MOVES) == 0) and (not check_continue_file())
        cond2 = reachedNewContent and (not check_continue_file())

        if cond1 or cond2:
            print("Ended program - continue file stop")
            exit()
        if reachedNewContent and NIGHT_MODE:
            time.sleep(night_delay)
        board = chess.Board(fen)
        current_level_n_moves_processed += 1

        if board.outcome():
            continue

        # check if worth saving
        if reachedNewContent and (current_level_n_moves_processed % BACKUP_N_MOVES == 0):
            store_full_dict(theory_dict)
            print(f"\nMove: {num_move} - Processed: {current_level_n_moves_processed} / {len(current_frontier)} - Theory amount:"
                  f" {theory_dict.getNumPosDB()} Total Analyzed {theory_dict.getNumPosAnalyzed() + current_level_n_moves_processed}")

        elif not reachedNewContent and (current_level_n_moves_processed % CHECKED_N_MOVES == 0):
            print(f"Move: {num_move} - Checked {current_level_n_moves_processed} / {len(current_frontier)} moves")

        # make decision and store in dictionary (WITHOUT WRITING FILE)
        stockfish_stronger.set_fen_position(fen)
        if not theory_dict.getDictResponse(fen=fen):
            reachedNewContent = True
            best_move = stockfish_stronger.get_top_moves(1)[0]['Move']
            theory_dict.insertNew(fen=fen, bestMove=best_move, depth=num_move)
            print(f"{fen.ljust(65)} {best_move}")

        # add to frontier
        fen = board.fen()
        if num_move <= min_opening_moves:
            for m in board.legal_moves:
                new_fen = get_fen_from_move(fen, m)
                new_frontier.append(new_fen)
        else:
            stockfish_weaker.set_fen_position(fen)
            best_n_moves = stockfish_weaker.get_top_moves(num_max_options)
            for sm in best_n_moves:
                new_fen = get_fen_from_uci(fen, sm['Move'])
                new_frontier.append(new_fen)

    # increase DB depth
    if num_move > theory_dict.getDataBaseDepth():
        num_analyzed = theory_dict.getNumPosAnalyzed() + len(current_frontier)
        theory_dict.setCompleteDatabaseDepth(num_move, num_analyzed)

    if reachedNewContent:
        store_full_dict(theory_dict)
