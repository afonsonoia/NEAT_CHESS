import multiprocessing
import random


def sleeping_secure():
    from aux_funcs_random import check_continue_file
    import time
    # stop while continue file doesn't exist
    while not check_continue_file():
        print("Stoped")
        time.sleep(600)


def eval_func_puzzles(genome, config, NUM_ATTEMPTS:int, generation_number:int):
    from classes import generateSortValuePuzzlesV2
    from math import log2
    from aux_funcs_random import wait_for_green_light, check_locked_files_file, delete_locked_files_file, create_locked_files_file
    import chess
    import random
    import pickle
    from classes import Bot
    import time
    import os

    records = {}

    puzzles_file_path = r'aux_files/puzzles_generated.puzzle'
    partial_puzzles_folder_path = r'./aux_files/__puzzles_results'
    percentage_update_puzzles_diff = 3 #min(int(4*NUM_ATTEMPTS), 50)

    skip_prob_perc = 0     #%

    sleeping_secure()

    i_attempts = NUM_ATTEMPTS

    ACCUMULATIVE_POINTS = True
    DEBUG_PRINTS = False

    BEST_POINTS = 0
    POINTS = 0
    bot = Bot(genome, config)

    if skip_prob_perc > 0:
        skip_prob = skip_prob_perc/100
    else:
        skip_prob = 0

    if skip_prob > 1:
        print("WARNING: skip_prob_perc is too high - __main.py - eval_func_white_puzzles()")
        skip_prob = 0.9

    sucess_read = False

    while not sucess_read:
        try:
            puzzles_file = open(puzzles_file_path, 'rb')
            puzzles_arr = pickle.load(puzzles_file)
            puzzles_file.close()
            sucess_read = True
        except FileNotFoundError:
            return 0
        except:
            time.sleep(random.random()*0.1)

    updatePuzzles = False
    if (random.random()*100) < percentage_update_puzzles_diff:
        updatePuzzles = True

    best_puzzle_index = -1
    quick_start = 5
    correct_puzzles_in_a_row = quick_start

    for i in range(len(puzzles_arr)):
        best_puzzle_index = i
        if NUM_ATTEMPTS <= 0:
            break

        # skip super simple puzzles
        if i < generation_number/250:
            POINTS += 1
            continue

        if correct_puzzles_in_a_row > 0:
            step = max(2, int(log2(correct_puzzles_in_a_row)))
        else:
            step = 1

        if i % step != 0:
            POINTS += 1
            continue

        puzzle = puzzles_arr[i]

        board = chess.Board(fen=puzzle.get_fen())

        if puzzle.white:
            color_int = 1
        else:
            color_int = -1

        decision = bot.make_decision(board, color_int).__str__()

        # check if decision is correct
        if decision in puzzle.get_best_moves_list_strs():
            if updatePuzzles:
                records[puzzle.get_fen()] = 1

            correct_puzzles_in_a_row += 1
            # add points to puzzleV2
            puzzles_arr[i].count(True)

            if ACCUMULATIVE_POINTS:
                BEST_POINTS = max(BEST_POINTS, POINTS) + 1
                POINTS = BEST_POINTS
            else:
                POINTS += 1
        else:
            if updatePuzzles:
                records[puzzle.get_fen()] = -1

            correct_puzzles_in_a_row = 0
            # add points to puzzleV2
            puzzles_arr[i].count(False)

            NUM_ATTEMPTS -= 1
            if not ACCUMULATIVE_POINTS:
                BEST_POINTS = max(POINTS, BEST_POINTS)
                POINTS = 0

    # update difficulty if randomly selected:
    if updatePuzzles:

        # ------- extra puzzle evaluations - doesn't change points --------
        puzzles_size = len(puzzles_arr)
        percentage_test_puzzles = 5
        if best_puzzle_index+2 < puzzles_size:
            num_tests = max(1, int((puzzles_size-best_puzzle_index)*(percentage_test_puzzles/100)))

            indexes_tested = []
            indexes_tested_2 = []

            i = -1
            for k in range(num_tests):
                if k > min(100, int(puzzles_size*0.1)):
                    security_counter = 0
                    while (i in indexes_tested) or (i == -1):
                        i = random.randint(best_puzzle_index+1, puzzles_size-1)
                        security_counter += 1
                        if security_counter > 10*puzzles_size:
                            print("WARNING: STUCK IN RANDOM TEST LOOP")
                            security_counter = int(security_counter*0.9)
                    indexes_tested.append(i)

                elif k > 0: # always test some of the next 100 puzzles (probably have less attempts)
                    n_puzzles_to_test = 200
                    if puzzles_size < 10 * n_puzzles_to_test:
                        continue
                    if indexes_tested_2:
                        i = -1
                    security_counter = 0
                    while i in indexes_tested_2 or i == -1:
                        i = random.randint(best_puzzle_index+1 , min(best_puzzle_index+1+n_puzzles_to_test, puzzles_size))
                        if security_counter > 10 * n_puzzles_to_test:
                            print("WARNING: STUCK IN RANDOM TEST LOOP (2)")
                            security_counter = int(security_counter * 0.8)
                    indexes_tested_2.append(i)

                else:   # always test last puzzle (hardest)
                    i = len(puzzles_arr)-1

                puzzle = puzzles_arr[i]
                board = chess.Board(fen=puzzle.get_fen())
                if puzzle.white:
                    color_int = 1
                else:
                    color_int = -1

                decision = bot.make_decision(board, color_int).__str__()

                # check if decision is correct
                if decision == puzzle.get_best_moves_list_strs():
                    # add points to puzzleV2
                    puzzles_arr[i].count(True)
                    records[puzzle.get_fen()] = 1
                else:
                    # add points to puzzleV2
                    puzzles_arr[i].count(False)
                    records[puzzle.get_fen()] = -1

        # -----------------------------------------------------------------

        if BEST_POINTS > 0:
            puzzles_per_attempt = round((BEST_POINTS/i_attempts), 2)
        else:
            puzzles_per_attempt = 0

        if random.random() < 0.1:
            print(f"NN updated puzzles - num attempts: {i_attempts} - puzzles: {BEST_POINTS} - p/a: {round(puzzles_per_attempt, 2)}")
        sleeping_secure()

        # sort first
        puzzles_arr.sort(key=generateSortValuePuzzlesV2)

        sucess_write = False
        while not sucess_write:
            try:
                str_num = ""
                for _ in range(5):
                    num = random.randint(1, 1000000)
                    str_num += str(num)
                name = str(str_num) + ".pickle"
                full_path = os.path.join(partial_puzzles_folder_path, name)
                puzzles_file = open(full_path, "wb")
                pickle.dump(records, puzzles_file)
                puzzles_file.close()
                if DEBUG_PRINTS:
                    print("Diff updated sucessfuly")
                sucess_write = True
            except Exception as e:
                time.sleep(random.random() * 0.1)
                print(e)

        sleeping_secure()
    return BEST_POINTS


# return result + n_moves
def aux_single_game(bot1, bot2, record_game:bool, alt_record_path=False):
    import chess
    import chess.pgn
    from os.path import join
    from classes import get_numeric_board_pawns_calculation
    import random
    n_moves = 0
    board = chess.Board()

    if alt_record_path:
        path_records = r"C:\Users\Afonso Noia\PycharmProjects\NEAT_CHESS\_pgns_to_merge_2"
    else:
        path_records = r"C:\Users\Afonso Noia\PycharmProjects\NEAT_CHESS\_pgns_to_merge"

    # board.turn = True -> white to move
    while not board.outcome():
        if board.turn:
            n_moves += 1
            board.push(bot1.make_decision(board, my_color=1))  # white
        else:
            board.push(bot2.make_decision(board, my_color=-1))  # black

    result = None   # 0 = draw; 1 = white_win; -1 = black_win
    draw_diff_pieces_in_pawns = 0

    if board.outcome().winner is None:
        # draw
        result = 0
        numeric_board = get_numeric_board_pawns_calculation(board.__str__())
        for val in numeric_board:
            draw_diff_pieces_in_pawns += val  # val is negative if oposite color

    elif board.outcome().winner:
        # white wins
        result = 1
    else:
        # black wins
        result = -1

    # recording game pgn
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
        # Add moves to the game
        for move in board.move_stack:
            node = node.add_variation(move)

        # generate random name file
        num_game = ""
        for _ in range(50):
            num_game = num_game + str(random.randint(1, 9))

        if alt_record_path:
            name_file = "human_game_" + num_game + ".pgn"
        else:
            name_file = "nn_" + num_game + ".pgn"
        path_file = join(path_records, name_file)

        with open(path_file, "w", encoding="utf-8") as f:
            f.write(str(game_record))

        print(f"PGN gravado em: {path_file}")

    return [result, n_moves, draw_diff_pieces_in_pawns]

def eval_function_simple(genome, config, champions_arr:list, generation_number:int):
    from classes import Bot
    from math import log2, ceil

    # ser melhor que x% dos champions para ser novo champion
    #PERCENTAGE_BETTER = 95
    MAX_VALUE_SPEED = 0.5
    MAX_N_GAMES = 1
    PERCENTAGE_RECORD_GAME = -1
    BONUS_DOUBLE_WIN = 0.1
    BONUS_BOT_WIN_CHAMP = 1.0

    if len(champions_arr) > 0:
        MAX_N_GAMES = max(int(log2(len(champions_arr))), 1)

    bot = Bot(genome, config)
    total_score = 0
    global_results = [0, 0]  # global wins / losses
    count_champions = 0

    valid_champion = True

    for champion in champions_arr:
        count_champions += 1
        RECORD_GAMES = False

        if random.random()*100 < PERCENTAGE_RECORD_GAME:
            RECORD_GAMES = True

        local_score = 0

        sleeping_secure()
        won_a_game = False
        lost_a_game = False

        base_score = 1

        # skip some games!
        if len(champions_arr) > 2:
            if count_champions <= len(champions_arr)-MAX_N_GAMES:
                total_score += 1.5
                global_results[0] += 1
                continue

        # ----- first game with white -----

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
            local_score += min(0.8, results[2]/20)

        # ----- second game with black -----
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
            local_score += min(0.8, (-1*results[2])/20)

        # ----- check if won against champion -----
        if won_both_games: #won_a_game and not lost_a_game:
            global_results[0] += 1

        if lost_a_game and champion == champions_arr[-1]:
            global_results[0] -= 1

        total_score += float(local_score)

        if won_both_games:
            total_score += BONUS_DOUBLE_WIN

        if lost_a_game or not won_a_game:
            valid_champion = False

        else:
            total_score += BONUS_BOT_WIN_CHAMP

        #if not(won_a_game and not lost_a_game):
        #    break


        # FUTURE: add extra bonus for defeating stronger champions - like local_score * 1.01 ** champion_number

    # calculating if it is a new champion
    #diz_wins = round(PERCENTAGE_BETTER/100, 5)
    """if len(champions_arr) > 0:
        tolerance_champions = min(int(0.49 * len(champions_arr)), int(ceil(MAX_N_GAMES/2))-1)
    else:
        tolerance_champions = 0"""

    # if len(champions_arr) == 0 or global_results[0] >= len(champions_arr):
    # if len(champions_arr) == 0 or total_score > len(champions_arr):
    if len(champions_arr) == 0 or valid_champion:
        return [float(total_score), bot]
    else:
        return [float(total_score), None]


# retornar [score, None] OU [score, bot_object]
def eval_function(genome, config, champions_arr, generation_number:int):
    from math import log2

    games_results = [None, None]

    score = 0
    puzzle_attempts = 3
    num_puzzles_sucess = eval_func_puzzles(genome, config, int(puzzle_attempts), generation_number)
    """
    if generation_number < 100: # incentivise puzzles on the beguinning
        if num_puzzles_sucess > 0:
            score += num_puzzles_sucess/10
    elif num_puzzles_sucess >= generation_number:
        games_results = eval_function_simple(genome, config, champions_arr)
        try:
            score += log2(num_puzzles_sucess) * max(float(games_results[0]), 1)
        except:
            score += 0
    """
    score += (num_puzzles_sucess/20)
    games_results = eval_function_simple(genome, config, champions_arr, generation_number)

    if games_results[0] > 1:
        score += float(games_results[0])# **2
    else:
        score += float(games_results[0])

    return [float(score), games_results[1]]


if __name__ == "__main__":

    import os
    import custom_neat_lib
    import pickle
    import time
    from aux_funcs_random import create_continue_file
    from classes import Bot
    from ______FULL_RESET______ import full_reset
    from aux_backup_managemment import BACKUP_FOLDER, get_last_backup_path, restore_checkpoint

    path_champions = r"C:\Users\Afonso Noia\PycharmProjects\NEAT_CHESS\champions"
    partial_puzzles_files = r"C:\Users\Afonso Noia\PycharmProjects\NEAT_CHESS\aux_files\__puzzles_results"
    CONTINUE_FROM_CHECKPOINT = True
    MAX_NUM_GENERATIONS = -1

    # Load the config file, which is assumed to live in
    # the same directory as this script.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, '_chess_config.txt')
    config = custom_neat_lib.Config(custom_neat_lib.DefaultGenome, custom_neat_lib.DefaultReproduction, custom_neat_lib.DefaultSpeciesSet,
                                    custom_neat_lib.DefaultStagnation, config_path)

    create_continue_file()

    # delete partial puzzle files
    f_names = os.listdir(partial_puzzles_files)
    for fn in f_names:
        path = os.path.join(partial_puzzles_files, fn)
        os.remove(path)

    if CONTINUE_FROM_CHECKPOINT:
        try:
            lastBackupPath = get_last_backup_path()
            pop = restore_checkpoint(lastBackupPath, champions_arr_path=path_champions)
            print("continuing from backup")

        except Exception as e:
            print(e)
            print("new population")
            full_reset()
            pop = custom_neat_lib.Population(config, path_champions=path_champions)
    else:
        print("new population")
        full_reset()
        pop = custom_neat_lib.Population(config, path_champions=path_champions)

    filenamePrefix = r'C:\Users\Afonso Noia\PycharmProjects\NEAT_CHESS\backups\backup_'

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

    # Save the winner.
    with open('chess_winner', 'wb') as f:
        pickle.dump(winner, f)
    print(winner)



