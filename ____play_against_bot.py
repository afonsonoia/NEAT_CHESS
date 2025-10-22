import time
import pygame
import chess
import os
import pickle
import chess.pgn
import pyperclip
import random
import shutil  # <--- added for moving files
from __main import aux_single_game
from classes import Bot

# Constants
SQUARE_SIZE = 60
BOARD_SIZE = SQUARE_SIZE * 8
WHITE_COLOR = (240, 217, 181)
BLACK_COLOR = (181, 136, 99)
BOT_CONTROLS_WHITE = True
AUTO_PROMOTE_QUEEN = True

BOT_NUMBER = 1
DEPTH = 1

flip_board = not BOT_CONTROLS_WHITE

ALT_PGN_PATH = r"C:\Users\Afonso Noia\PycharmProjects\NEAT_CHESS\_pgns_to_merge_2"
OUTPUT_PATH = r"C:\Users\Afonso Noia\PycharmProjects\NEAT_CHESS\aux_files\_pgns_database"

pygame.init()

bot_path = f"./champions/champ_{BOT_NUMBER}.pickle"
print("Bot path:", bot_path)

with open(bot_path, 'rb') as f:
    bot = pickle.load(f)

# Load piece images
def load_images():
    pieces = {}
    for piece in ['P', 'N', 'B', 'R', 'Q', 'K']:
        pieces[f'b{piece}'] = pygame.image.load(os.path.join("./images", f"b{piece}.png"))
        pieces[f'w{piece}'] = pygame.image.load(os.path.join("./images", f"w{piece}.png"))
    return pieces

piece_images = load_images()

# Draw board and pieces
def draw_board(screen, board):
    for row in range(8):
        for col in range(8):
            color = WHITE_COLOR if (row + col) % 2 == 0 else BLACK_COLOR
            pygame.draw.rect(screen, color, pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    for square, piece in board.piece_map().items():
        col = chess.square_file(square)
        row = chess.square_rank(square)
        if flip_board:
            col = 7 - col
            row = 7 - row
        screen.blit(piece_images[f'{"w" if piece.color else "b"}{piece.symbol().upper()}'],
                    (col * SQUARE_SIZE, row * SQUARE_SIZE))

# Get square from click
def get_square_from_mouse(x, y):
    col = x // SQUARE_SIZE
    row = y // SQUARE_SIZE
    if flip_board:
        col = 7 - col
        row = 7 - row
    return chess.square(col, row)

# Handle pawn promotion
def promote_pawn(board, move):
    if chess.square_rank(move.to_square) in [0, 7] and board.piece_at(move.from_square).piece_type == chess.PAWN:
        if AUTO_PROMOTE_QUEEN:
            move.promotion = chess.QUEEN
        else:
            while True:
                choice = input("Promote to (q/r/b/n): ").strip().lower()
                if choice in ['q', 'r', 'b', 'n']:
                    move.promotion = {'q': chess.QUEEN, 'r': chess.ROOK, 'b': chess.BISHOP, 'n': chess.KNIGHT}[choice]
                    break

# Save PGN to disk
def save_pgn(game, bot_white, bot_black):
    pgn = chess.pgn.Game()
    pgn.headers["Event"] = "Neural Networks Training Vs Human"
    pgn.headers["White"] = f"Champion {bot_white.champ_num}" if bot_white and bot_white.champ_num else "Not fully working label"
    pgn.headers["Black"] = f"Champion {bot_black.champ_num}" if bot_black and bot_black.champ_num else "Not fully working label"
    node = pgn
    for move in game.move_stack:
        node = node.add_variation(move)

    random_name = "".join(str(random.randint(1, 9)) for _ in range(50))
    file_name = f"human_game_{random_name}.pgn"
    file_path = os.path.join(ALT_PGN_PATH, file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(str(pgn))

    print("PGN saved to:", file_path)

# Move local_games.pgn if it exists
def move_local_pgn():
    src = os.path.join(OUTPUT_PATH, "local_games.pgn")
    dst = os.path.join(ALT_PGN_PATH, "local_games.pgn")
    if os.path.exists(src):
        print(f"Moving local_games.pgn from {OUTPUT_PATH} to {ALT_PGN_PATH}")
        shutil.move(src, dst)
    else:
        print("No local_games.pgn found to move.")

# Main game loop
def play_game(bot):
    global flip_board
    screen = pygame.display.set_mode((BOARD_SIZE, BOARD_SIZE))
    pygame.display.set_caption('Play Against Bot')
    board = chess.Board()
    game = board
    selected_square = None
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                flip_board = not flip_board

            if event.type == pygame.MOUSEBUTTONDOWN and not board.is_game_over():
                if not (BOT_CONTROLS_WHITE and board.turn) and not (not BOT_CONTROLS_WHITE and not board.turn):
                    x, y = pygame.mouse.get_pos()
                    square = get_square_from_mouse(x, y)

                    if selected_square is None:
                        if board.piece_at(square) and board.piece_at(square).color == board.turn:
                            selected_square = square
                    else:
                        move = chess.Move(selected_square, square)
                        if move in board.legal_moves:
                            promote_pawn(board, move)
                            board.push(move)
                        else:
                            try:
                                promo_move = chess.Move.from_uci(str(move) + "q")
                                if promo_move in board.legal_moves:
                                    move.promotion = chess.QUEEN
                                    board.push(move)
                            except:
                                pass
                        selected_square = None

        # Check for game end before bot moves
        if board.outcome():
            print("Game over:", board.outcome())
            draw_board(screen, board)  # ✅ Final board
            pygame.display.flip()
            if BOT_CONTROLS_WHITE:
                save_pgn(board, bot, None)
            else:
                save_pgn(board, None, bot)
            pyperclip.copy(str(board))
            move_local_pgn()           # ✅ Move local PGN
            time.sleep(5)
            break

        # Bot's move
        if (board.turn and BOT_CONTROLS_WHITE) or (not board.turn and not BOT_CONTROLS_WHITE):
            my_color = 1 if board.turn else -1
            move = bot.make_decision_depth(board, my_color=my_color, depth=DEPTH)
            if move is None or move not in board.legal_moves:
                print("Bot move is invalid or None. Ending game.")
                draw_board(screen, board)
                pygame.display.flip()
                move_local_pgn()       # ✅ Move local PGN even on failure
                time.sleep(5)
                break
            board.push(move)

        draw_board(screen, board)
        pygame.display.flip()

    pygame.quit()

# Run
if __name__ == "__main__":
    play_game(bot)
