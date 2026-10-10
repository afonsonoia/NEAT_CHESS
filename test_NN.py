import chess
from chess import pgn
import pickle
import os
import custom_neat_lib as neat
import random
from aux_chess_funcs import get_all_legal_moves_raw
from classes import Bot

local_dir = os.path.dirname(os.path.abspath(__file__))
winner_path = os.path.join(local_dir, 'chess_winner')

# Load the config file
config_path = os.path.join(local_dir, '_chess_config.txt')
config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                     neat.DefaultSpeciesSet, neat.DefaultStagnation,
                     config_path)

if os.path.exists(winner_path):
    with open(winner_path, 'rb') as f:
        genome = pickle.load(f)
    bot = Bot(genome, config)
else:
    champ_dir = os.path.join(local_dir, 'champions')
    os.makedirs(champ_dir, exist_ok=True)
    champs = [f for f in os.listdir(champ_dir) if f.startswith('champ_') and f.endswith('.pickle')]
    champs.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
    if champs:
        with open(os.path.join(champ_dir, champs[-1]), 'rb') as f:
            bot = pickle.load(f)
    else:
        print("[test_NN] No saved champions found. Creating a baseline genome from config for testing.")
        genome = config.genome_type(0)
        genome.configure_new(config.genome_config)
        bot = Bot(genome, config)


board = chess.Board()
game_record = chess.pgn.Game()

last_move = None

# board.turn = True -> white to move
while not board.outcome():

    if board.turn:
        decision = bot.make_decision(board, my_color=1)
        board.push(decision)
        if not last_move:
            last_move = game_record.add_main_variation(decision)
        else:
            last_move = last_move.add_main_variation(decision)

    else:
        # random decision
        valid_moves = get_all_legal_moves_raw(board)
        d = random.randint(0, len(valid_moves)-1)
        decision = valid_moves[d]
        board.push(decision)
        last_move = last_move.add_main_variation(decision)


if board.outcome().winner is None:
    # draw
    print("draw")

elif board.outcome().winner:
    # white wins
    print("win")

else:
    # black wins
    print("defeat")

print(game_record.mainline())



