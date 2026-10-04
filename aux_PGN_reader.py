import chess
import chess.pgn
from io import StringIO
import re


def get_pgn_at_index(filename, index, content=None):
    if content is None:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()

    # Split the content into individual games using double newline characters
    games = content.split('\n\n')

    if index < 0 or index * 2 + 1 >= len(games):
        return "Invalid index. Please provide a valid index."

    # Extract the game at the specified index
    selected_game = games[index * 2 + 1]

    return selected_game.strip()


def get_pgn_header_at_index(filename, index, content=None):
    if content is None:
        with open(filename, 'r') as file:
            content = file.read()

    # Split the content into individual games using double newline characters
    games = content.split('\n\n')

    if index < 0 or index * 2 + 1 >= len(games):
        return "Invalid index. Please provide a valid index."

    # Extract the game at the specified index
    selected_game = games[index * 2]

    return selected_game.strip()


def get_games_headers_arr(filename):
    with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.read()

    # Split the content into individual games using double newline characters
    content = content.split('\n\n')

    return content


def count_games(filename):
    with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.read()

    # Split the content into individual games using double newline characters
    games = content.split('\n\n')

    # Count the number of games (divide by 2 to exclude event headers)
    num_games = len(games) // 2

    return num_games


def display_board_after_moves(pgn_string):
    # Create a PGN game from the input string
    pgn = chess.pgn.read_game(StringIO(pgn_string))

    # Create a chess board from the starting position
    board = chess.Board()

    # Iterate through the moves in the PGN and display the board after each move
    for move in pgn.mainline_moves():
        board.push(move)
        print(board)
        print('\n' + str(board.fen()) + '\n\n')


def get_full_paths_in_folder(folder_path):
    import os
    file_paths = []

    # Iterate through all files in the specified folder
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_paths.append(file_path)

    return file_paths


if __name__ == "__main__":
    local_dir = os.path.dirname(os.path.abspath(__file__))
    pgn_path = os.path.join(local_dir, 'sample_game.pgn')
    if os.path.isfile(pgn_path):
        with open(pgn_path, 'r') as file:
            pgn = file.read()
        display_board_after_moves(pgn)
    else:
        print(f"Sample PGN not found at: {pgn_path}")

