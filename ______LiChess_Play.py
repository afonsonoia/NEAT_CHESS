import os
import time
import random
import berserk
import chess
import pickle
import pygame
from classes import Bot, LICHESS_TOKEN

# === CONFIGURATION ===
token = os.getenv('LICHESS_BOT_TOKEN', LICHESS_TOKEN)
bot_path = "./champions/champ_18.pickle"
depth = 1
target_time = 60
target_increment = 1
auto_rated = True

# GUI setup
TILE_SIZE = 80
BOARD_SIZE = TILE_SIZE * 8
WHITE = (240, 217, 181)
BLACK = (181, 136, 99)

# Load your bot
with open(bot_path, 'rb') as f:
    bot = pickle.load(f)

# Initialize display
pygame.init()
screen = pygame.display.set_mode((BOARD_SIZE, BOARD_SIZE))
pygame.display.set_caption("Lichess Bot Live Game")

# Preload piece images
images = {}
for piece in 'PNBRQK':
    for color in 'wb':
        img = pygame.image.load(f"images/{color}{piece}.png")
        images[f"{color}{piece}"] = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))

def draw_board(board):
    for r in range(8):
        for c in range(8):
            col = WHITE if (r + c) % 2 == 0 else BLACK
            pygame.draw.rect(screen, col, (c*TILE_SIZE, (7-r)*TILE_SIZE, TILE_SIZE, TILE_SIZE))
    for sq, pc in board.piece_map().items():
        code = ('w' if pc.color else 'b') + pc.symbol().upper()
        x = chess.square_file(sq) * TILE_SIZE
        y = (7 - chess.square_rank(sq)) * TILE_SIZE
        screen.blit(images[code], (x, y))
    pygame.display.flip()

# Set up Lichess client
session = berserk.TokenSession(token)
client = berserk.Client(session=session)

def compute_move(san_moves):
    board = chess.Board()
    for san in san_moves:
        board.push_san(san)
    color_val = 1 if board.turn else -1
    return bot.make_decision_depth(board, my_color=color_val, depth=depth)

def auto_matchmake():
    try:
        bots = list(client.bots.get_online(nb=20))
        opponents = [u['id'] for u in bots]
        if not opponents:
            print("No bots currently online among the first 20.")
            return
        opp = random.choice(opponents)
        client.challenges.create(
            username=opp,
            rated=auto_rated,
            color='random',
            clock={'limit': target_time, 'increment': target_increment}
        )
        print(f"Challenged {opp} ({'rated' if auto_rated else 'unrated'})")
    except Exception as e:
        print(f"Matchmaking error: {e}")

# MAIN
if __name__ == "__main__":
    print("Bot online. Launching matchmaking...")
    auto_matchmake()

    for ev in client.bots.stream_incoming_events():
        et = ev.get('type')

        if et == 'challenge':
            cid = ev['challenge']['id']
            client.bots.accept_challenge(cid)
            print(f"Accepted challenge {cid}")

        elif et == 'gameStart':
            game_id = ev['game']['id']
            print(f"Game started: {game_id}")
            board = chess.Board()

            for st in client.bots.stream_game_state(game_id):
                for pe in pygame.event.get():
                    if pe.type == pygame.QUIT:
                        pygame.quit()
                        exit()

                moves = st['moves'].split() if st['moves'] else []
                board.reset()
                for san in moves:
                    board.push_san(san)
                draw_board(board)

                if st['isMyTurn']:
                    mv = compute_move(moves)
                    try:
                        client.bots.make_move(game_id, mv.uci())
                        print(f"Played {mv.uci()}")
                    except berserk.exceptions.ResponseError as e:
                        print(f"Move error: {e}")

                if st.get('status') not in ['started', 'created']:
                    print(f"Game ended: {st.get('status')} (winner: {st.get('winner')})")
                    break

            print(f"Finished game: {game_id}")
            time.sleep(2)
            auto_matchmake()
