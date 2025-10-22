import chess
from chess import pgn
import pickle
import os
import neat
import random
from aux_chess_funcs import get_all_legal_moves_raw
from classes import Bot

# load the winner
with open('chess_winner', 'rb') as f:
    genome = pickle.load(f)


# Load the config file, which is assumed to live in
# the same directory as this script.
local_dir = os.path.dirname(__file__)
config_path = os.path.join(local_dir, '_chess_config.txt')
config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                     neat.DefaultSpeciesSet, neat.DefaultStagnation,
                     config_path)

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



