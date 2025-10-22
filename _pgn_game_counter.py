from aux_PGN_reader import count_games
import time

file_pgn_path = r"C:\Users\Afonso Noia\PycharmProjects\NEAT_CHESS\___chess.com - downloader\games.pgn"

n_games = count_games(file_pgn_path)

print(f"{n_games} games  -  {file_pgn_path}")
time.sleep(12)








