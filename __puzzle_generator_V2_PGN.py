if __name__ == '__main__':

    from aux_PGN_reader import get_pgn_at_index, count_games, get_full_paths_in_folder
    import os.path
    from classes import PuzzleV2, generateSortValuePuzzlesV2
    import chess.pgn
    import pickle
    from io import StringIO
    import time
    from stockfish import Stockfish
    from aux_funcs_random import create_continue_file, check_continue_file, get_current_time_str_print, timeout, terminate_process_by_name

    # vars
    DISPLAY_PRE_CONTENT_N_GAMES = 1

    DEBUG_MODE = False

    NIGHT_MODE = True
    delays_night = 2

    MAX_MOVES_MATE_PUZZLES = 40
    DEPTH_stockfish = 24
    min_depth = 24

    decrement_depth = 2

    THREADS = 8
    TIMEOUT_SECONDS = 30

    CENTIPAWN_MAX_DIFERENCE_PUZZLE = 5
    CENTIPAWN_MIN_DIFERENCE_PUZZLE = 45

    NUMBER_LINES_STOCKFISH = 5


    def runStockfish_pure(stockfish, fen, nmoves):
        stockfish.set_fen_position(fen)
        top_stockfish_moves = stockfish.get_top_moves(nmoves)
        return top_stockfish_moves


    runStockfish = timeout(timeout=TIMEOUT_SECONDS)(runStockfish_pure)

    puzzles_file_path = r'.\aux_files\puzzles_generated.puzzle'
    pgn_folder_path = r'aux_files\_pgns_database'
    engine_path = r'.\stockfish_16\stockfish-windows-x86-64-avx2.exe'
    processed_moves_path = r'.\aux_files\processed_moves.fens'

    puzzles_arr = []
    num_games = 0
    num_puzzles_found = [0, 0]
    arr_processed_fens_raw = [[], []]  # processed / timeout

    top_stockfish_moves = None

    if os.path.isfile(puzzles_file_path):
        puzzles_file = open(puzzles_file_path, 'rb')
        puzzles_arr = pickle.load(puzzles_file)
        puzzles_file.close()

    if os.path.isfile(processed_moves_path):
        processed_file = open(processed_moves_path, 'rb')
        arr_processed_fens_raw = pickle.load(processed_file)
        processed_file.close()

    arr_processed_fens = arr_processed_fens_raw[0] + arr_processed_fens_raw[1]

    create_continue_file()

    new_content = False
    pgn_files = get_full_paths_in_folder(pgn_folder_path)

    last_processed_time = 0
    total_processed_games = 0

    for filepath in pgn_files:
        total_processed_games += num_games
        num_games = 0
        print(f"\n\nStarting file: {filepath}\n\n")
        for i in range(count_games(filepath)):
            num_games += 1
            # DISPLAY
            if new_content:
                print(
                    f"\n\n\n\n\n\nGames: {num_games} / {count_games(filepath)} - ({total_processed_games + num_games}) - {filepath[len(pgn_folder_path) + 1:]}\n")
                print(f"Puzzles found  W: {num_puzzles_found[0]} - B: {num_puzzles_found[1]}")
                print(f"Total puzzles: {len(puzzles_arr)}")
                print(f"Positions analised: {len(arr_processed_fens)}\n")
                print(100 * "-" + '\n')
            else:
                if (num_games % DISPLAY_PRE_CONTENT_N_GAMES == 0) and (num_games > 0):
                    print(
                        get_current_time_str_print() + f"Analised {num_games} / {count_games(filepath)} - ({total_processed_games + num_games}) games")

            # setup first position board
            pgn_raw = get_pgn_at_index(filepath, i)
            pgn = chess.pgn.read_game(StringIO(pgn_raw))

            # Create a chess board from the starting position
            board = chess.Board()
            moves_processed = 0  # processing moves not the initial board
            # Iterate through the moves in the PGN and display the board after each move
            for move in pgn.mainline_moves():
                # Capture the puzzle position and moving color BEFORE pushing the move.
                puzzle_fen = board.fen()  # This FEN has the correct active color.
                moving_color = board.turn  # True for white, False for black.

                # For logging purposes, increment moves_processed if it was black's move.
                if moving_color:
                    moves_processed += 1

                # Check CONTINUE file.
                if not check_continue_file():
                    print(get_current_time_str_print() + "Stopped - continue file not found")
                    time.sleep(3)
                    exit()

                # Push the move to update board for subsequent moves.
                board.push(move)

                # If this puzzle position was already processed, skip further analysis.
                if puzzle_fen in arr_processed_fens:
                    if new_content:
                        print(get_current_time_str_print() + "skiped")
                        last_processed_time = 0
                    continue
                else:
                    if DEBUG_MODE:
                        print(puzzle_fen)
                    new_content = True

                # Examine for a puzzle using the puzzle_fen (pre-move position).
                current_depth = DEPTH_stockfish
                finished = False
                i_time = time.time()
                TIMED_OUT = False

                while not finished:
                    if NIGHT_MODE:
                        time.sleep(delays_night)
                    TIMED_OUT = False
                    # check CONTINUE file
                    if not check_continue_file():
                        print(get_current_time_str_print() + "Stopped - continue file not found")
                        time.sleep(3)
                        exit()
                    stockfish_aux = Stockfish(path=engine_path, depth=current_depth, parameters={"Threads": THREADS})
                    try:
                        if DEBUG_MODE:
                            print(get_current_time_str_print() + "starting processing...")

                        # Use the puzzle_fen for analysis so the active color is correct.
                        top_stockfish_moves = runStockfish(stockfish_aux, puzzle_fen, NUMBER_LINES_STOCKFISH)

                        if DEBUG_MODE:
                            print(get_current_time_str_print() + "finished processing")
                        finished = True
                        arr_processed_fens_raw[0].append(puzzle_fen)
                        break
                    except Exception as error:
                        TIMED_OUT = True
                        if DEBUG_MODE:
                            print("force stop stockfish")
                        terminate_process_by_name("stockfish-windows-x86-64-avx2.exe")
                        if DEBUG_MODE:
                            print(error)
                        if DEBUG_MODE:
                            print(get_current_time_str_print() + "timeout - forced stop")
                        # If the function did not complete within the timeout, check if we're at min_depth.
                        if current_depth <= min_depth:
                            finished = True
                            break
                        # Otherwise, try with a lower depth.
                        current_depth -= decrement_depth
                        print(get_current_time_str_print() + f"Stockfish timed out - retrying with {current_depth}")

                # Add to processed timeout if not already added.
                if puzzle_fen not in arr_processed_fens_raw[0]:
                    arr_processed_fens_raw[1].append(puzzle_fen)

                arr_processed_fens.append(puzzle_fen)  # store the puzzle position even if it didn't finish processing.
                f_time = time.time()
                last_processed_time = round(f_time - i_time, 2)

                arr_puzzle_solutions = []

                if top_stockfish_moves and len(top_stockfish_moves) >= 3 and not TIMED_OUT:
                    best_move = top_stockfish_moves[0]
                    second_best = top_stockfish_moves[1]
                    third_best = top_stockfish_moves[2]
                    worst_move = top_stockfish_moves[-1]

                    # --- checkmates ---
                    if (best_move["Mate"] is not None) and (abs(best_move["Mate"]) <= MAX_MOVES_MATE_PUZZLES):
                        if worst_move["Mate"] is None and (abs(best_move["Mate"]) > 1):
                            print(get_current_time_str_print() + "PUZZLE! ".center(100, " "))
                            print(puzzle_fen)
                            print(best_move["Move"])
                            print(100 * "-" + '\n')

                            # main line append
                            arr_puzzle_solutions.append(best_move["Move"])

                            if second_best["Mate"] is not None and abs(second_best["Mate"]) <= MAX_MOVES_MATE_PUZZLES:
                                arr_puzzle_solutions.append(second_best["Move"])

                            if third_best["Mate"] is not None and abs(third_best["Mate"]) <= MAX_MOVES_MATE_PUZZLES:
                                arr_puzzle_solutions.append(third_best["Move"])

                    # general puzzle
                    elif (best_move["Centipawn"] is not None) and (worst_move["Centipawn"] is not None):
                        if abs(best_move["Centipawn"] - worst_move["Centipawn"]) >= CENTIPAWN_MIN_DIFERENCE_PUZZLE:


                            # main line append
                            arr_puzzle_solutions.append(best_move["Move"])

                            if second_best["Move"] is not None and abs(best_move["Centipawn"] - second_best["Centipawn"]) <= CENTIPAWN_MAX_DIFERENCE_PUZZLE:
                                arr_puzzle_solutions.append(second_best["Move"])

                            if third_best["Move"] is not None and abs(best_move["Centipawn"] - third_best["Centipawn"]) <= CENTIPAWN_MAX_DIFERENCE_PUZZLE:
                                arr_puzzle_solutions.append(third_best["Move"])


                if arr_puzzle_solutions:
                    print("PUZZLE! ".center(100, " "))
                    print(puzzle_fen)
                    print(arr_puzzle_solutions)
                    print(100 * "-" + '\n')

                    if top_stockfish_moves[0]["Mate"] is not None:
                        new_puzzle = PuzzleV2(puzzle_fen, arr_puzzle_solutions, moving_color, 100)
                    else:
                        new_puzzle = PuzzleV2(puzzle_fen, arr_puzzle_solutions, moving_color, current_depth)

                    # if puzzle found
                    aux_is_new = True
                    if new_puzzle is not None:
                        # check for duplicate puzzles
                        for p in puzzles_arr:
                            if p.get_fen() == puzzle_fen:
                                aux_is_new = False
                                print("NOT A NEW PUZZLE")
                                break

                        # store puzzle if new
                        if aux_is_new:
                            if moving_color:
                                num_puzzles_found[0] += 1
                            else:
                                num_puzzles_found[1] += 1
                            puzzles_arr.append(new_puzzle)
                            puzzles_arr.sort(key=generateSortValuePuzzlesV2)  # sort
                            puzzles_file = open(puzzles_file_path, "wb")
                            pickle.dump(puzzles_arr, puzzles_file)
                            puzzles_file.close()
                            new_puzzle = None

                if moves_processed > 0 and new_content:
                    print(get_current_time_str_print() + f"move: {moves_processed} - {last_processed_time}s")

                # Save processed move
                processed_file = open(processed_moves_path, "wb")
                pickle.dump(arr_processed_fens_raw, processed_file)
                processed_file.close()
