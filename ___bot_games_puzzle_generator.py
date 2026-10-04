import time
import chess
import os
import pickle
import chess.pgn
import random
import shutil
from itertools import combinations
import pygame
import multiprocessing
import sys
import subprocess

# --- Direct import of Bot class ---
# WARNING: 'classes.py' MUST be in the same directory.
try:
    from classes import Bot
except ImportError:
    print("CRITICAL ERROR: Could not find 'classes.py'.")
    print("This script cannot run without this file.")
    sys.exit(1)

# --- Tournament Configuration ---
MIN_BOT_NUMBER = 0
MAX_BOT_NUMBER = 37
DEFAULT_DEPTH = 1
# MOVE_DELAY_SECONDS was removed, now dynamic

# --- Pygame Constants (from original script) ---
SQUARE_SIZE = 60
BOARD_SIZE = SQUARE_SIZE * 8
WHITE_COLOR = (240, 217, 181)
BLACK_COLOR = (181, 136, 99)
flip_board = False  # Change to True to flip board

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALT_PGN_PATH = os.path.join(BASE_DIR, "_pgns_to_merge_2")
CHAMPIONS_PATH = os.path.join(BASE_DIR, "champions")
IMAGES_PATH = os.path.join(BASE_DIR, "images")

# Ensure directories exist
os.makedirs(ALT_PGN_PATH, exist_ok=True)
os.makedirs(CHAMPIONS_PATH, exist_ok=True)
os.makedirs(IMAGES_PATH, exist_ok=True)


# --- Pygame Functions ---

def load_images():
    """Loads chess piece images from the 'images' folder."""
    pieces = {}
    for piece in ['P', 'N', 'B', 'R', 'Q', 'K']:
        try:
            # Try to load image
            img_b = pygame.image.load(os.path.join(IMAGES_PATH, f"b{piece}.png"))
            img_w = pygame.image.load(os.path.join(IMAGES_PATH, f"w{piece}.png"))

            # Scale image to square size
            pieces[f'b{piece}'] = pygame.transform.scale(img_b, (SQUARE_SIZE, SQUARE_SIZE))
            pieces[f'w{piece}'] = pygame.transform.scale(img_w, (SQUARE_SIZE, SQUARE_SIZE))

        except pygame.error as e:
            print(f"Error loading image for {piece}: {e}")
            print(f"Please check if images exist at: {IMAGES_PATH}")
            # Create magenta placeholder surface on error
            placeholder = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            placeholder.fill((255, 0, 255))
            pieces[f'b{piece}'] = placeholder
            pieces[f'w{piece}'] = placeholder
    return pieces


def draw_board(screen, board, piece_images):
    """Draws the chess board and pieces on the Pygame screen."""
    for row in range(8):
        for col in range(8):
            color = WHITE_COLOR if (row + col) % 2 == 0 else BLACK_COLOR
            pygame.draw.rect(screen, color, pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    for square, piece in board.piece_map().items():
        col = chess.square_file(square)
        row = 7 - chess.square_rank(square)  # Pygame coordinates draw top to bottom

        if flip_board:
            col = 7 - col
            row = 7 - row

        # Build image key
        piece_color = "w" if piece.color == chess.WHITE else "b"
        piece_type = piece.symbol().upper()
        img_key = f"{piece_color}{piece_type}"

        if img_key in piece_images:
            img = piece_images[img_key]
            screen.blit(img, (col * SQUARE_SIZE, row * SQUARE_SIZE))
        else:
            print(f"Warning: Image key not found: {img_key}")


# --- Tournament Functions ---

def load_bot(bot_number):
    """Loads a bot from a pickle file."""
    bot_path = os.path.join(CHAMPIONS_PATH, f"champ_{bot_number}.pickle")
    try:
        with open(bot_path, 'rb') as f:
            bot = pickle.load(f)
        print(f"Bot champ_{bot_number}.pickle loaded.")
        # Ensure bot knows its number
        bot.champ_num = bot_number
        return bot
    except FileNotFoundError:
        print(f"ERROR: Bot not found at {bot_path}.")
    except Exception as e:
        print(f"ERROR loading {bot_path}: {e}")
    return None


def save_game_pgn(board, bot_white, bot_black):
    """Saves the final board state as a PGN file."""
    pgn = chess.pgn.Game()
    pgn.headers["Event"] = "Bot Tournament (NEAT)"

    # Bot names
    bot_white_name = f"Champ {bot_white.champ_num}" if hasattr(bot_white, 'champ_num') else "Bot (White)"
    bot_black_name = f"Champ {bot_black.champ_num}" if hasattr(bot_black, 'champ_num') else "Bot (Black)"

    pgn.headers["White"] = bot_white_name
    pgn.headers["Black"] = bot_black_name
    pgn.headers["Result"] = board.result()

    # Add moves
    node = pgn
    for move in board.move_stack:
        node = node.add_variation(move)

    # Unique file name
    timestamp = int(time.time())
    random_id = random.randint(1000, 9999)
    file_name = f"champ_{bot_white.champ_num}_vs_champ_{bot_black.champ_num}_{timestamp}_{random_id}.pgn"
    file_path = os.path.join(ALT_PGN_PATH, file_name)

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(str(pgn))
        print(f"PGN saved to: {file_path}")
    except Exception as e:
        print(f"Error saving PGN: {e}")


# --- Background Script Runner ---
def run_background_scripts():
    """Runs merge and puzzle generation scripts in a separate process."""
    pid = os.getpid()
    print(f"[Background Process (PID: {pid})] Starting...")
    try:
        python_exe = sys.executable

        # Script paths
        script1_path = os.path.join(BASE_DIR, "_pgn_merger_2.py")
        script2_path = os.path.join(BASE_DIR, "__puzzle_generator_V2_PGN.py")

        if os.path.exists(script1_path):
            print(f"[Background Process] Running: {script1_path}")
            subprocess.run([python_exe, script1_path])
        else:
            print(f"[Background Process] WARNING: Script not found: {script1_path}")

        print("[Background Process] Waiting 1 second...")
        time.sleep(1)

        if os.path.exists(script2_path):
            print(f"[Background Process] Running: {script2_path}")
            subprocess.run([python_exe, script2_path])
        else:
            print(f"[Background Process] WARNING: Script not found: {script2_path}")

        print(f"[Background Process (PID: {pid})] Finished.")

    except Exception as e:
        print(f"[Background Process (PID: {pid})] Error: {e}")


# --- END ---

def play_single_game(bot_white, bot_black, depth_white, depth_black, screen, piece_images, background_process):
    """
    Simulates a single game between two bots, displaying it on the GUI.
    Uses a single 'background_process' to calculate delay dynamically.
    Returns (board, should_stop_tournament)
    """
    board = chess.Board()
    base_caption = f"Game: {bot_white.champ_num} (W) vs {bot_black.champ_num} (B)"

    # --- Show initial state ---
    pygame.display.set_caption(base_caption)
    draw_board(screen, board, piece_images)
    pygame.display.flip()
    time.sleep(1)  # Longer pause for the start

    while not board.is_game_over():
        # --- Check if user closed the window ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("Window closed by user. Ending tournament...")
                return board, True

        try:
            # Determine whose turn it is
            if board.turn == chess.WHITE:
                my_color = 1
                move = bot_white.make_decision_depth(board, my_color=my_color, depth=depth_white)
            else:
                my_color = -1
                move = bot_black.make_decision_depth(board, my_color=my_color, depth=depth_black)

            if move is None or move not in board.legal_moves:
                print(f"Bot {bot_white.champ_num if board.turn == chess.WHITE else bot_black.champ_num} made an invalid move (None or illegal).")
                break  # End game

            board.push(move)

            # --- DYNAMIC DELAY LOGIC ---
            # 'n' is 1 if background process is alive, 0 otherwise.
            n = 1 if background_process is not None and background_process.is_alive() else 0
            current_delay = 0.5 + (2.0 * n)

            # Update window caption to show status
            caption = f"{base_caption} | Processing: {n} | Delay: {current_delay:.1f}s"
            pygame.display.set_caption(caption)

            draw_board(screen, board, piece_images)
            pygame.display.flip()
            time.sleep(current_delay)

        except Exception as e:
            print(f"Error during bot execution: {e}")
            break

    # --- Show final result ---
    print(f"Game finished. Result: {board.result()}")
    draw_board(screen, board, piece_images)
    pygame.display.flip()
    time.sleep(2)

    return board, False


def run_tournament(min_bot_num, max_bot_num, depth):
    """Main function that organizes and runs all games."""

    # --- Initialize Pygame ---
    pygame.init()
    pygame.display.set_caption('Bot Tournament')
    screen = pygame.display.set_mode((BOARD_SIZE, BOARD_SIZE))

    # --- Load Assets ---
    try:
        piece_images = load_images()
    except Exception as e:
        print(f"Fatal error loading images: {e}. Exiting.")
        pygame.quit()
        return

    # Load all required bots
    bots = {}
    bot_ids = list(range(min_bot_num, max_bot_num + 1))
    print(f"Loading bots from {min_bot_num} to {max_bot_num}...")

    for i in bot_ids:
        bot = load_bot(i)
        if bot:
            bots[i] = bot
        else:
            print(f"Warning: Could not load Bot {i}. It will be skipped.")

    if len(bots) < 2:
        print("Error: At least 2 bots are required to start a tournament.")
        pygame.quit()
        return

    # Create all game pairs (combinations of 2)
    game_pairs = list(combinations(bots.keys(), 2))

    # --- RANDOM ORDER LOGIC ---
    print("Creating and shuffling game list...")
    all_games_to_play = []
    for (id_a, id_b) in game_pairs:
        all_games_to_play.append((id_a, id_b))  # Game 1: A (W) vs B (B)
        all_games_to_play.append((id_b, id_a))  # Game 2: B (W) vs A (B)

    # Shuffle list of all games
    random.shuffle(all_games_to_play)

    total_games = len(all_games_to_play)

    print(f"Bots loaded: {list(bots.keys())}")
    print(f"Total games (random order): {total_games}")
    print(f"Using search depth: {depth}")

    game_count = 0
    start_time = time.time()
    should_stop_tournament = False

    # Variable for background process
    background_process = None

    # --- MAIN LOOP ---
    # Iterate over shuffled list, one game at a time
    for (white_id, black_id) in all_games_to_play:
        bot_white = bots[white_id]
        bot_black = bots[black_id]

        game_count += 1
        print(f"Preparing Game {game_count}/{total_games}: Champ {white_id} (W) vs Champ {black_id} (B)")
        board, should_stop_tournament = play_single_game(bot_white, bot_black, depth, depth, screen, piece_images, background_process)
        save_game_pgn(board, bot_white, bot_black)

        # Background process check
        if background_process is None or not background_process.is_alive():
            print("Spawning background scripts (merger/puzzle)...")
            background_process = multiprocessing.Process(target=run_background_scripts)
            background_process.start()
        else:
            print("Background scripts still running. Game queued.")

        if should_stop_tournament:
            break

    # Wait for final background process
    print("\nVisual tournament finished. Waiting for final background process...")
    if background_process is not None and background_process.is_alive():
        print("Waiting for last script execution...")
        background_process.join()
    print("All background processes finished.")

    # Quit Pygame
    pygame.quit()
    print(f"Tournament completed. Total time: {(time.time() - start_time):.2f} seconds.")


# --- Run ---
if __name__ == "__main__":
    # Ensure multiprocessing works correctly across platforms
    multiprocessing.freeze_support()

    run_tournament(MIN_BOT_NUMBER, MAX_BOT_NUMBER, DEFAULT_DEPTH)