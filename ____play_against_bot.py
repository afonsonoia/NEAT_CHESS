import time
import pygame
import chess
import os
import pickle
import chess.pgn
import pyperclip
import random
import shutil
from __main import aux_single_game
from classes import Bot

# Constants
SQUARE_SIZE = 60
BOARD_SIZE = SQUARE_SIZE * 8
WHITE_COLOR = (240, 217, 181)
BLACK_COLOR = (181, 136, 99)
BOT_CONTROLS_WHITE = True
AUTO_PROMOTE_QUEEN = True

BOT_NUMBER = 82
DEPTH = 1

flip_board = not BOT_CONTROLS_WHITE

# --- WARNING: Hardcoded paths, update if necessary ---
# Using relative paths for portability, assuming images/ and champions/ are in the same dir
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALT_PGN_PATH = os.path.join(BASE_DIR, "_pgns_to_merge_2")
OUTPUT_PATH = os.path.join(BASE_DIR, "aux_files", "_pgns_database")
IMAGES_PATH = os.path.join(BASE_DIR, "images")
CHAMPIONS_PATH = os.path.join(BASE_DIR, "champions")

# Ensure directories exist
os.makedirs(ALT_PGN_PATH, exist_ok=True)
os.makedirs(OUTPUT_PATH, exist_ok=True)
os.makedirs(IMAGES_PATH, exist_ok=True)
os.makedirs(CHAMPIONS_PATH, exist_ok=True)

pygame.init()

bot_path = os.path.join(CHAMPIONS_PATH, f"champ_{BOT_NUMBER}.pickle")
print("Bot path:", bot_path)

try:
    with open(bot_path, 'rb') as f:
        bot = pickle.load(f)
except FileNotFoundError:
    print(f"Warning: Bot file not found at {bot_path}. Using Mock Bot.")
    bot = Bot() # Use the mock bot if the real one isn't found
except (ImportError, ModuleNotFoundError):
    print(f"Warning: Could not load bot due to missing classes. Using Mock Bot.")
    bot = Bot() # Use mock bot if 'classes' module is missing


# Load piece images
def load_images():
    pieces = {}
    for piece in ['P', 'N', 'B', 'R', 'Q', 'K']:
        try:
            pieces[f'b{piece}'] = pygame.image.load(os.path.join(IMAGES_PATH, f"b{piece}.png"))
            pieces[f'w{piece}'] = pygame.image.load(os.path.join(IMAGES_PATH, f"w{piece}.png"))
        except pygame.error as e:
            print(f"Error loading image for {piece}: {e}")
            print(f"Please make sure images are in: {IMAGES_PATH}")
            # Create a placeholder surface
            placeholder = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            placeholder.fill((255, 0, 255)) # Fill with magenta to show error
            pieces[f'b{piece}'] = placeholder
            pieces[f'w{piece}'] = placeholder
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
        row = chess.square_rank(square) # <-- EDITED: Reverted to original coordinate system
        if flip_board:
            col = 7 - col
            row = 7 - row
        
        # Scale images if they don't fit the square size
        img = piece_images[f'{"w" if piece.color else "b"}{piece.symbol().upper()}']
        img = pygame.transform.scale(img, (SQUARE_SIZE, SQUARE_SIZE))
        
        screen.blit(img, (col * SQUARE_SIZE, row * SQUARE_SIZE))

# Get square from click
def get_square_from_mouse(x, y):
    col = x // SQUARE_SIZE
    row = y // SQUARE_SIZE
    if flip_board:
        col = 7 - col
        row = 7 - row
    return chess.square(col, row) # <-- EDITED: Reverted to original coordinate system

# Handle pawn promotion
def promote_pawn(board, move):
    if chess.square_rank(move.to_square) in [0, 7] and board.piece_at(move.from_square).piece_type == chess.PAWN:
        if AUTO_PROMOTE_QUEEN:
            move.promotion = chess.QUEEN
        else:
            # This console input will block pygame, recommend building a simple UI for this
            print("Pawn promotion needed!")
            while True:
                choice = input("Promote to (q/r/b/n): ").strip().lower()
                if choice in ['q', 'r', 'b', 'n']:
                    move.promotion = {'q': chess.QUEEN, 'r': chess.ROOK, 'b': chess.BISHOP, 'n': chess.KNIGHT}[choice]
                    break

# Save PGN to disk
def save_pgn(game, bot_white, bot_black):
    pgn = chess.pgn.Game()
    pgn.headers["Event"] = "Neural Networks Training Vs Human"
    
    # Check if bot is the mock bot or a real one
    bot_white_name = f"Champion {bot_white.champ_num}" if hasattr(bot_white, 'champ_num') else "Bot (White)"
    bot_black_name = f"Champion {bot_black.champ_num}" if hasattr(bot_black, 'champ_num') else "Bot (Black)"
    
    pgn.headers["White"] = bot_white_name if bot_white else "Human"
    pgn.headers["Black"] = bot_black_name if bot_black else "Human"

    node = pgn
    # Use game.move_stack if it's a chess.Board object
    move_stack = game.move_stack if hasattr(game, 'move_stack') else []
    for move in move_stack:
        node = node.add_variation(move)

    random_name = "".join(str(random.randint(1, 9)) for _ in range(50))
    file_name = f"human_game_{random_name}.pgn"
    file_path = os.path.join(ALT_PGN_PATH, file_name)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(str(pgn))
        print("PGN saved to:", file_path)
    except Exception as e:
        print(f"Error saving PGN: {e}")


# Move local_games.pgn if it exists
def move_local_pgn():
    src = os.path.join(OUTPUT_PATH, "local_games.pgn")
    dst = os.path.join(ALT_PGN_PATH, "local_games.pgn")
    if os.path.exists(src):
        try:
            print(f"Moving local_games.pgn from {OUTPUT_PATH} to {ALT_PGN_PATH}")
            shutil.move(src, dst)
        except Exception as e:
            print(f"Error moving local PGN: {e}")
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

    # Initial draw of the board
    draw_board(screen, board)
    pygame.display.flip()

    while running:
        # Check if it's the bot's turn *before* processing events
        # This allows the bot to play without waiting for a mouse click
        is_bot_turn = (board.turn and BOT_CONTROLS_WHITE) or (not board.turn and not BOT_CONTROLS_WHITE)
        
        if is_bot_turn and not board.is_game_over():
            my_color = 1 if board.turn else -1
            move = bot.make_decision_depth(board, my_color=my_color, depth=DEPTH)
            
            if move is None or move not in board.legal_moves:
                print("Bot move is invalid or None. Ending game.")
                draw_board(screen, board)
                pygame.display.flip()
                move_local_pgn()  # Move local PGN even on failure
                time.sleep(5)
                break
            
            board.push(move)
            draw_board(screen, board) # Draw after bot move
            pygame.display.flip()
            selected_square = None # Clear selection after bot moves

        # Process all events in the queue
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                flip_board = not flip_board
                draw_board(screen, board) # Redraw immediately on flip
                pygame.display.flip()

            # Human's turn logic
            if event.type == pygame.MOUSEBUTTONDOWN and not is_bot_turn and not board.is_game_over():
                x, y = pygame.mouse.get_pos()
                square = get_square_from_mouse(x, y)

                if selected_square is None:
                    if board.piece_at(square) and board.piece_at(square).color == board.turn:
                        selected_square = square
                else:
                    move = chess.Move(selected_square, square)
                    promote_pawn(board, move) # Check for promotion *before* move legality

                    if move in board.legal_moves:
                        board.push(move)
                        # --- 💡 EDITED: Added update here ---
                        draw_board(screen, board)
                        pygame.display.flip()
                        # --- End of Edit ---
                    else:
                        # Try to handle auto-queen promotion on click
                        try:
                            promo_move = chess.Move.from_uci(str(move) + "q")
                            if promo_move in board.legal_moves:
                                board.push(promo_move)
                                # --- 💡 EDITED: Added update here ---
                                draw_board(screen, board)
                                pygame.display.flip()
                                # --- End of Edit ---
                        except:
                            pass  # Not a valid promotion or move
                    selected_square = None

        # Check for game end *after* moves have been processed
        if board.outcome():
            print("Game over:", board.outcome())
            draw_board(screen, board)  # Show final board
            pygame.display.flip()
            if BOT_CONTROLS_WHITE:
                save_pgn(board, bot, None)
            else:
                save_pgn(board, None, bot)
            
            try:
                pyperclip.copy(str(board))
            except Exception as e:
                print(f"Could not copy to clipboard: {e}")

            move_local_pgn()  # Move local PGN
            time.sleep(5)
            running = False # End the loop
            break

        # The main draw loop was moved. 
        # We only draw/flip *after* a move (human or bot) or a board flip.
        # This check might be redundant now, but we keep the main flip
        # to catch any other visual updates (like board flipping)
        
        # We can remove the final draw/flip as it's handled inside the move logic
        # draw_board(screen, board)
        # pygame.display.flip()

        # Add a small delay to prevent the loop from spinning too fast
        pygame.time.wait(10) 

    pygame.quit()

# Run
if __name__ == "__main__":
    play_game(bot)

