import os
from aux_PGN_reader import count_games
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_pgn_path = os.path.join(BASE_DIR, "___chess.com - downloader", "games.pgn")

n_games = count_games(file_pgn_path)

print(f"{n_games} games  -  {file_pgn_path}")
time.sleep(12)








