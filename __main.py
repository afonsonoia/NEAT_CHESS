import multiprocessing
import random
import pickle
import time
import os
import chess
import chess.pgn
from os.path import join
import math

def sleeping_secure():
    from aux_funcs_random import check_continue_file
    while not check_continue_file():
        print("Stoped")
        time.sleep(600)


def eval_func_puzzles(genome, config, NUM_ATTEMPTS: int, generation_number: int):
    import chess
    import random
    import pickle
    import time
    import os
    from classes import Bot

    records = {}

    # Candidate puzzle files using relative paths
    puzzle_candidates = [
        os.path.join('human_puzzles', 'all_files', 'twic_and_gms.puzzle'),
        os.path.join('human_puzzles', 'human_moves_stream.puzzle'),
        os.path.join('human_puzzles', 'human_moves.puzzle'),
        os.path.join('aux_files', 'puzzles_generated.puzzle'),
        os.path.join('_secure_backups', 'auto puzzles', 'puzzles_generated.puzzle'),
    ]
    puzzles_file_path = None
    for cand in puzzle_candidates:
        if os.path.isfile(cand):
            puzzles_file_path = cand
            break
        script_dir = os.path.dirname(__file__) if '__file__' in globals() else '.'
        cand_script = os.path.join(script_dir, cand)
        if os.path.isfile(cand_script):
            puzzles_file_path = os.path.relpath(cand_script)
            break

    if puzzles_file_path is None:
        puzzles_file_path = os.path.join('human_puzzles', 'human_moves_stream.puzzle')

    partial_puzzles_folder_path = os.path.join('aux_files', '__puzzles_results')
    percentage_update_puzzles_diff = 0

    sleeping_secure()

    i_attempts = NUM_ATTEMPTS
    ACCUMULATIVE_POINTS = True
    DEBUG_PRINTS = False

    BEST_POINTS = 0
    POINTS = 0
    bot = Bot(genome, config)

    updatePuzzles = False
    if (random.random() * 100) < percentage_update_puzzles_diff:
        updatePuzzles = True

    PREFETCH_SIZE = 1000
    SKIP_PROB = 0

    try:
        # Open file ONCE at the beginning
        puzzles_file = open(puzzles_file_path, 'rb')
    except FileNotFoundError:
        print(f"\n[CRITICAL ERROR] File not found: {puzzles_file_path}")
        return 0

    end_of_file = False

    # -------------------------------------------------------------
    # MASTER LOOP: Continue pulling batches until attempts run out
    # -------------------------------------------------------------
    while NUM_ATTEMPTS > 0 and not end_of_file:

        ram_puzzles_buffer = []

        # 1. Pull a batch of N puzzles from disk
        for _ in range(PREFETCH_SIZE):
            try:
                item = pickle.load(puzzles_file)
                if isinstance(item, list):
                    ram_puzzles_buffer.extend(item)
                    end_of_file = True
                    break
                else:
                    ram_puzzles_buffer.append(item)
            except EOFError:
                end_of_file = True
                break

        # If end of file reached and buffer is empty, exit loop
        if not ram_puzzles_buffer:
            break

        # 2. Evaluate puzzles of this specific batch
        for puzzle in ram_puzzles_buffer:

            if NUM_ATTEMPTS <= 0:
                break

            if random.random() < SKIP_PROB:
                continue

            # --- REAL EVALUATION ---
            board = chess.Board(fen=puzzle.get_fen())
            color_int = 1 if puzzle.white else -1

            decision = bot.make_decision(board, color_int).__str__()
            best_moves_list = puzzle.get_best_moves_list_strs()

            if decision in best_moves_list:
                if DEBUG_PRINTS:
                    print(f"Genius! Bot predicted {decision} perfectly!")

                if updatePuzzles:
                    records[puzzle.get_fen()] = 1

                if ACCUMULATIVE_POINTS:
                    BEST_POINTS = max(BEST_POINTS, POINTS) + 1
                    POINTS = BEST_POINTS
                else:
                    POINTS += 1
            else:
                if DEBUG_PRINTS and random.random() < 0.05:
                    print(f"Error: Bot tried '{decision}' | But correct moves were: {best_moves_list}")

                if updatePuzzles:
                    records[puzzle.get_fen()] = -1

                NUM_ATTEMPTS -= 1  # Lost an attempt due to mistake!
                if not ACCUMULATIVE_POINTS:
                    BEST_POINTS = max(POINTS, BEST_POINTS)
                    POINTS = 0

    # Close file safely when attempts finish
    puzzles_file.close()

    # -----------------------------------------------------------------
    # SAVING
    # -----------------------------------------------------------------
    if BEST_POINTS > 0:
        puzzles_per_attempt = round((BEST_POINTS / i_attempts), 2)
    else:
        puzzles_per_attempt = 0

    sleeping_secure()

    if updatePuzzles and records:
        sucess_write = False
        while not sucess_write:
            try:
                str_num = "".join([str(random.randint(1, 9)) for _ in range(10)])
                name = str_num + ".pickle"
                full_path = os.path.join(partial_puzzles_folder_path, name)

                with open(full_path, "wb") as f:
                    pickle.dump(records, f)
                sucess_write = True
            except Exception as e:
                print(f"\n[SAVING ERROR] Failure: {e}")
                time.sleep(random.random() * 0.1)

        sleeping_secure()

    return BEST_POINTS


# return result + n_moves
def aux_single_game(bot1, bot2, record_game: bool, alt_record_path=False):
    from classes import get_numeric_board_pawns_calculation
    n_moves = 0
    board = chess.Board()

    if alt_record_path:
        path_records = "_pgns_to_merge_2"
    else:
        path_records = "_pgns_to_merge"

    while not board.outcome():
        if board.turn:
            n_moves += 1
            board.push(bot1.make_decision(board, my_color=1))
        else:
            board.push(bot2.make_decision(board, my_color=-1))

    result = None
    draw_diff_pieces_in_pawns = 0

    if board.outcome().winner is None:
        result = 0
        numeric_board = get_numeric_board_pawns_calculation(board.__str__())
        for val in numeric_board:
            draw_diff_pieces_in_pawns += val

    elif board.outcome().winner:
        result = 1
    else:
        result = -1

    if record_game:
        game_record = chess.pgn.Game()
        if alt_record_path:
            game_record.headers["Event"] = "Neural Networks Trainning Vs Human"
        else:
            game_record.headers["Event"] = "Neural Networks Trainning"

        if bot1.champ_num:
            game_record.headers["White"] = "Champion " + str(bot1.champ_num)
        else:
            game_record.headers["White"] = "Regular NN"

        if bot2.champ_num:
            game_record.headers["Black"] = "Champion " + str(bot2.champ_num)
        else:
            game_record.headers["Black"] = "Regular NN"

        node = game_record
        for move in board.move_stack:
            node = node.add_variation(move)

        num_game = "".join([str(random.randint(1, 9)) for _ in range(50)])

        if alt_record_path:
            name_file = "human_game_" + num_game + ".pgn"
        else:
            name_file = "nn_" + num_game + ".pgn"
        os.makedirs(path_records, exist_ok=True)
        path_file = join(path_records, name_file)

        with open(path_file, "w", encoding="utf-8") as f:
            f.write(str(game_record))

        print(f"PGN saved to: {path_file}")

    return [result, n_moves, draw_diff_pieces_in_pawns]


def eval_function_simple(genome, config, champions_arr: list, generation_number: int):
    from classes import Bot
    from math import log2

    MAX_VALUE_SPEED = 0.5
    PERCENTAGE_RECORD_GAME = 0.0001
    BONUS_DOUBLE_WIN = 0.1
    BONUS_BOT_WIN_CHAMP = 1.0

    bot = Bot(genome, config)

    if len(champions_arr) == 0:
        return [0.0, bot]

    # Uniform Stratified Sampling (from weakest to strongest)
    k_games = max(int(log2(len(champions_arr) ** 2)), 1)
    if k_games >= len(champions_arr):
        selected_champions = champions_arr
    elif k_games == 1:
        selected_champions = [champions_arr[-1]]
    else:
        step = (len(champions_arr) - 1) / (k_games - 1)
        selected_indices = sorted(list(set(round(i * step) for i in range(k_games))))
        selected_champions = [champions_arr[idx] for idx in selected_indices]

    total_score = 3 * len(selected_champions)
    valid_champion = True

    for champion in selected_champions:
        RECORD_GAMES = False

        if random.random() * 100 < PERCENTAGE_RECORD_GAME:
            RECORD_GAMES = True

        local_score = 0
        sleeping_secure()
        won_a_game = False
        lost_a_game = False
        base_score = 1
        won_both_games = True

        results = aux_single_game(bot, champion, RECORD_GAMES)
        if results[0] == 1:
            won_a_game = True
            local_score += base_score + round(MAX_VALUE_SPEED / results[1], 5)
        elif results[0] == -1:
            lost_a_game = True
            won_both_games = False
            local_score -= base_score - round(MAX_VALUE_SPEED / results[1], 5)
        elif results[0] == 0:
            won_both_games = False
            local_score += min(0.8, results[2] / 20)

        results = aux_single_game(champion, bot, RECORD_GAMES)
        if results[0] == -1:
            won_a_game = True
            local_score += base_score + round(MAX_VALUE_SPEED / results[1], 5)
        elif results[0] == 1:
            lost_a_game = True
            won_both_games = False
            local_score -= base_score - round(MAX_VALUE_SPEED / results[1], 5)
        else:
            won_both_games = False
            local_score += min(0.8, (-1 * results[2]) / 20)

        if lost_a_game and champion == selected_champions[-1]:
            local_score -= 1

        total_score += float(local_score)

        if won_both_games:
            total_score += BONUS_DOUBLE_WIN

        if lost_a_game or not won_a_game:
            valid_champion = False
        else:
            total_score += BONUS_BOT_WIN_CHAMP

        if not (won_a_game and not lost_a_game):
            break

    if valid_champion:
        return [float(total_score), bot]
    else:
        return [float(total_score), None]


def eval_function(genome, config, champions_arr, generation_number: int):
    games_results = [0, 0]
    score = 0
    puzzle_base_score = 0.1
    puzzle_attempts = math.log2(max(generation_number, 1))
    num_puzzles_sucess = eval_func_puzzles(genome, config, int(puzzle_attempts), generation_number)

    score += (num_puzzles_sucess * puzzle_base_score)
    games_results = eval_function_simple(genome, config, champions_arr, generation_number)

    if games_results[0] > 1:
        score += float(games_results[0]*0.5)
    else:
        score += float(games_results[0]*0.5)

    return [float(score), games_results[1]]


if __name__ == "__main__":
    import custom_neat_lib
    from aux_funcs_random import create_continue_file
    from ______FULL_RESET______ import full_reset
    from aux_backup_managemment import BACKUP_FOLDER, get_last_backup_path, restore_checkpoint

    path_champions = "champions"
    partial_puzzles_files = os.path.join("aux_files", "__puzzles_results")
    backups_folder = "backups"
    CONTINUE_FROM_CHECKPOINT = True
    MAX_NUM_GENERATIONS = -1

    # Ensure all runtime directories exist on clean checkout
    os.makedirs(path_champions, exist_ok=True)
    os.makedirs(partial_puzzles_files, exist_ok=True)
    os.makedirs(backups_folder, exist_ok=True)
    os.makedirs("_pgns_to_merge", exist_ok=True)
    os.makedirs("_pgns_to_merge_2", exist_ok=True)

    config_path = '_chess_config.txt'
    if not os.path.isfile(config_path):
        script_cfg = os.path.join(os.path.dirname(__file__), '_chess_config.txt')
        if os.path.isfile(script_cfg):
            config_path = os.path.relpath(script_cfg)

    config = custom_neat_lib.Config(custom_neat_lib.DefaultGenome, custom_neat_lib.DefaultReproduction, custom_neat_lib.DefaultSpeciesSet,
                                    custom_neat_lib.DefaultStagnation, config_path)

    create_continue_file()

    f_names = os.listdir(partial_puzzles_files)
    for fn in f_names:
        path = os.path.join(partial_puzzles_files, fn)
        os.remove(path)

    if CONTINUE_FROM_CHECKPOINT:
        try:
            lastBackupPath = get_last_backup_path()
            if lastBackupPath is not None:
                pop = restore_checkpoint(lastBackupPath, champions_arr_path=path_champions)
                print("continuing from backup:", lastBackupPath)
            else:
                print("No backups found, starting new population")
                pop = custom_neat_lib.Population(config, path_champions=path_champions)

        except Exception as e:
            print("Error loading checkpoint:", e)
            print("Starting new population")
            pop = custom_neat_lib.Population(config, path_champions=path_champions)
    else:
        print("Starting new population")
        pop = custom_neat_lib.Population(config, path_champions=path_champions)

    filenamePrefix = os.path.join('backups', 'backup_')

    stats = custom_neat_lib.StatisticsReporter()
    pop.add_reporter(stats)
    pop.add_reporter(custom_neat_lib.StdOutReporter(True))
    pop.add_reporter(custom_neat_lib.Checkpointer(filename_prefix=filenamePrefix, generation_interval=1))

    lock = multiprocessing.Lock()
    pe = custom_neat_lib.ParallelEvaluator(os.cpu_count(), eval_function)

    if MAX_NUM_GENERATIONS > 0:
        winner = pop.run(pe.evaluate, n=MAX_NUM_GENERATIONS)
    else:
        winner = pop.run(pe.evaluate)

    winner_save_path = 'chess_winner'
    with open(winner_save_path, 'wb') as f:
        pickle.dump(winner, f)
    print(winner)