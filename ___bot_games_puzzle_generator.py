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

# --- Importação direta da classe Bot ---
# AVISO: O arquivo 'classes.py' DEVE estar no mesmo diretório.
try:
    from classes import Bot
except ImportError:
    print("ERRO CRÍTICO: Não foi possível encontrar 'classes.py'.")
    print("Este script não pode funcionar sem esse arquivo.")
    sys.exit(1)

# --- Configurações do Torneio ---
MIN_BOT_NUMBER = 0
MAX_BOT_NUMBER = 37
DEFAULT_DEPTH = 1
# MOVE_DELAY_SECONDS foi removido, agora é dinâmico

# --- Constantes do Pygame (do script original) ---
SQUARE_SIZE = 60
BOARD_SIZE = SQUARE_SIZE * 8
WHITE_COLOR = (240, 217, 181)
BLACK_COLOR = (181, 136, 99)
flip_board = False  # Você pode mudar isso se quiser

# --- Caminhos (Paths) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALT_PGN_PATH = os.path.join(BASE_DIR, "_pgns_to_merge_2")
CHAMPIONS_PATH = os.path.join(BASE_DIR, "champions")
IMAGES_PATH = os.path.join(BASE_DIR, "images")  # <-- ADICIONADO

# Garantir que os diretórios existam
os.makedirs(ALT_PGN_PATH, exist_ok=True)
os.makedirs(CHAMPIONS_PATH, exist_ok=True)
os.makedirs(IMAGES_PATH, exist_ok=True)  # <-- ADICIONADO


# --- Funções do Pygame (do script original) ---

def load_images():
    """Carrega as imagens das peças de xadrez da pasta 'images'."""
    pieces = {}
    for piece in ['P', 'N', 'B', 'R', 'Q', 'K']:
        try:
            # Tenta carregar a imagem
            img_b = pygame.image.load(os.path.join(IMAGES_PATH, f"b{piece}.png"))
            img_w = pygame.image.load(os.path.join(IMAGES_PATH, f"w{piece}.png"))

            # Escala a imagem para o tamanho do quadrado
            pieces[f'b{piece}'] = pygame.transform.scale(img_b, (SQUARE_SIZE, SQUARE_SIZE))
            pieces[f'w{piece}'] = pygame.transform.scale(img_w, (SQUARE_SIZE, SQUARE_SIZE))

        except pygame.error as e:
            print(f"Erro ao carregar imagem para {piece}: {e}")
            print(f"Por favor, verifique se as imagens existem em: {IMAGES_PATH}")
            # Cria uma imagem de placeholder (magenta) se falhar
            placeholder = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
            placeholder.fill((255, 0, 255))  # Cor magenta para erro visível
            pieces[f'b{piece}'] = placeholder
            pieces[f'w{piece}'] = placeholder
    return pieces


def draw_board(screen, board, piece_images):
    """Desenha o tabuleiro e as peças na tela do Pygame."""
    for row in range(8):
        for col in range(8):
            color = WHITE_COLOR if (row + col) % 2 == 0 else BLACK_COLOR
            pygame.draw.rect(screen, color, pygame.Rect(col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

    for square, piece in board.piece_map().items():
        col = chess.square_file(square)
        row = 7 - chess.square_rank(square)  # O Pygame desenha de cima para baixo

        if flip_board:
            col = 7 - col
            row = 7 - row

        # Constrói a chave para o dicionário de imagens
        piece_color = "w" if piece.color == chess.WHITE else "b"
        piece_type = piece.symbol().upper()
        img_key = f"{piece_color}{piece_type}"

        if img_key in piece_images:
            img = piece_images[img_key]
            screen.blit(img, (col * SQUARE_SIZE, row * SQUARE_SIZE))
        else:
            print(f"Aviso: Chave de imagem não encontrada: {img_key}")


# --- Funções do Torneio ---

def load_bot(bot_number):
    """Carrega um bot a partir de um arquivo pickle."""
    bot_path = os.path.join(CHAMPIONS_PATH, f"champ_{bot_number}.pickle")
    try:
        with open(bot_path, 'rb') as f:
            bot = pickle.load(f)
        print(f"Bot champ_{bot_number}.pickle carregado.")
        # Garante que o bot sabe o seu número
        bot.champ_num = bot_number
        return bot
    except FileNotFoundError:
        print(f"ERRO: Bot não encontrado em {bot_path}.")
    except Exception as e:
        print(f"ERRO ao carregar {bot_path}: {e}")
    return None


def save_game_pgn(board, bot_white, bot_black):
    """Salva o estado final do tabuleiro como um arquivo PGN."""
    pgn = chess.pgn.Game()
    pgn.headers["Event"] = "Torneio de Bots (NEAT)"

    # Nomes dos bots
    bot_white_name = f"Champ {bot_white.champ_num}" if hasattr(bot_white, 'champ_num') else "Bot (Brancas)"
    bot_black_name = f"Champ {bot_black.champ_num}" if hasattr(bot_black, 'champ_num') else "Bot (Pretas)"

    pgn.headers["White"] = bot_white_name
    pgn.headers["Black"] = bot_black_name
    pgn.headers["Result"] = board.result()

    # Adiciona os lances
    node = pgn
    for move in board.move_stack:
        node = node.add_variation(move)

    # Nome de arquivo único
    timestamp = int(time.time())
    random_id = random.randint(1000, 9999)
    file_name = f"champ_{bot_white.champ_num}_vs_champ_{bot_black.champ_num}_{timestamp}_{random_id}.pgn"
    file_path = os.path.join(ALT_PGN_PATH, file_name)

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(str(pgn))
        print(f"PGN salvo em: {file_path}")
    except Exception as e:
        print(f"Erro ao salvar PGN: {e}")


# --- ADICIONADO: Função para executar em background ---
def run_background_scripts():
    """Executa os scripts de merge e geração de puzzles num processo separado."""
    pid = os.getpid()
    print(f"[Processo Background (PID: {pid})] Iniciando...")
    try:
        # Encontra o executável do Python (ex: python.exe ou /usr/bin/python)
        python_exe = sys.executable

        # Caminho para os scripts
        script1_path = os.path.join(BASE_DIR, "_pgn_merger_2.py")
        script2_path = os.path.join(BASE_DIR, "__puzzle_generator_V2_PGN.py")

        if os.path.exists(script1_path):
            print(f"[Processo Background] Executando: {script1_path}")
            # Usa subprocess.run para tratar caminhos com espaços corretamente
            subprocess.run([python_exe, script1_path])
        else:
            print(f"[Processo Background] AVISO: Script não encontrado: {script1_path}")

        print("[Processo Background] Aguardando 1 segundo...")
        time.sleep(1)

        if os.path.exists(script2_path):
            print(f"[Processo Background] Executando: {script2_path}")
            # Usa subprocess.run
            subprocess.run([python_exe, script2_path])
        else:
            print(f"[Processo Background] AVISO: Script não encontrado: {script2_path}")

        print(f"[Processo Background (PID: {pid})] Concluído.")

    except Exception as e:
        print(f"[Processo Background (PID: {pid})] Erro: {e}")


# --- FIM ---

def play_single_game(bot_white, bot_black, depth_white, depth_black, screen, piece_images, background_process):
    """
    Simula um único jogo entre dois bots, mostrando-o na GUI.
    Usa um *único* 'background_process' para calcular o delay dinamicamente.
    Retorna (board, should_stop_tournament)
    """
    board = chess.Board()
    base_caption = f"Jogo: {bot_white.champ_num} (W) vs {bot_black.champ_num} (B)"

    # --- Mostrar estado inicial ---
    pygame.display.set_caption(base_caption)
    draw_board(screen, board, piece_images)
    pygame.display.flip()
    time.sleep(1)  # Uma pausa um pouco maior para o início
    # --- FIM ---

    while not board.is_game_over():
        # --- ADICIONADO: Verificar se o usuário fechou a janela ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print("Janela fechada pelo usuário. Encerrando o torneio...")
                return board, True  # (board, should_stop = True)
        # --- FIM ---

        try:
            # Determina de quem é a vez
            if board.turn == chess.WHITE:
                my_color = 1
                move = bot_white.make_decision_depth(board, my_color=my_color, depth=depth_white)
            else:
                my_color = -1
                move = bot_black.make_decision_depth(board, my_color=my_color, depth=depth_black)

            if move is None or move not in board.legal_moves:
                print(f"Bot {bot_white.champ_num if board.turn == chess.WHITE else bot_black.champ_num} fez um lance inválido (None ou ilegal).")
                break  # Encerra o jogo

            board.push(move)

            # --- LÓGICA DE DELAY DINÂMICO (ALTERADA) ---
            # 'n' é 1 se o processo de background estiver vivo, 0 caso contrário.
            n = 1 if background_process is not None and background_process.is_alive() else 0

            # --- FÓRMULA ALTERADA ---
            current_delay = 0.5 + (2.0 * n)

            # Atualiza o caption da janela para mostrar o status
            caption = f"{base_caption} | Processando: {n} | Delay: {current_delay:.1f}s"
            pygame.display.set_caption(caption)

            draw_board(screen, board, piece_images)
            pygame.display.flip()  # Atualiza a tela
            time.sleep(current_delay)  # Usa o novo delay
            # --- FIM DA LÓGICA DE DELAY ---

        except Exception as e:
            print(f"Erro durante a execução do bot: {e}")
            break  # Encerra o jogo se o bot falhar

    # --- Mostrar resultado final ---
    print(f"Jogo terminado. Resultado: {board.result()}")
    draw_board(screen, board, piece_images)
    pygame.display.flip()
    time.sleep(2)  # Pausa maior para ver o final
    # --- FIM ---

    return board, False  # (board, should_stop = False)


def run_tournament(min_bot_num, max_bot_num, depth):
    """Função principal que organiza e executa todos os jogos."""

    # --- Inicializar Pygame ---
    pygame.init()
    pygame.display.set_caption('Torneio de Bots')
    screen = pygame.display.set_mode((BOARD_SIZE, BOARD_SIZE))

    # --- Carregar Assets ---
    try:
        piece_images = load_images()
    except Exception as e:
        print(f"Erro fatal ao carregar imagens: {e}. Encerrando.")
        pygame.quit()
        return

    # Carregar todos os bots necessários
    bots = {}
    bot_ids = list(range(min_bot_num, max_bot_num + 1))
    print(f"Carregando bots de {min_bot_num} a {max_bot_num}...")

    for i in bot_ids:
        bot = load_bot(i)
        if bot:
            bots[i] = bot
        else:
            print(f"Aviso: Não foi possível carregar o Bot {i}. Ele será ignorado.")

    if len(bots) < 2:
        print("Erro: São necessários pelo menos 2 bots para iniciar um torneio.")
        pygame.quit()
        return

    # Criar todos os pares de jogos (combinações de 2)
    game_pairs = list(combinations(bots.keys(), 2))

    # --- LÓGICA DE ORDEM ALEATÓRIA (ALTERADA) ---
    print("Criando e baralhando a lista de jogos...")
    all_games_to_play = []
    for (id_a, id_b) in game_pairs:
        all_games_to_play.append((id_a, id_b))  # Jogo 1: A (W) vs B (B)
        all_games_to_play.append((id_b, id_a))  # Jogo 2: B (W) vs A (B)

    # Baralha a lista de todos os jogos
    random.shuffle(all_games_to_play)

    total_games = len(all_games_to_play)  # Total de jogos é o tamanho da nova lista
    # --- FIM DA ALTERAÇÃO ---

    print(f"Bots carregados: {list(bots.keys())}")
    print(f"Total de jogos (ordem aleatória): {total_games}")
    print(f"Usando profundidade (depth): {depth}")

    game_count = 0
    start_time = time.time()
    should_stop_tournament = False

    # --- ALTERADO: Variável única para o processo de background ---
    background_process = None

    # --- LOOP PRINCIPAL ALTERADO ---
    # Itera sobre a lista baralhada, um jogo de cada vez
    for (white_id, black_id) in all_games_to_play:
        bot_white = bots[white_id]
        bot_black = bots[black_id]

        game_count += 1
        print(f"Preparando Jogo {game_count}/{total_games}: Champ {white_id} (W) vs Champ {black_id} (B)")
        board, should_stop_tournament = play_single_game(bot_white, bot_black, depth, depth, screen, piece_images, background_process)
        save_game_pgn(board, bot_white, bot_black)

        # LÓGICA DE BACKGROUND (executada após cada jogo)
        if background_process is None or not background_process.is_alive():
            print("Disparando scripts de background (merger/puzzle)...")
            background_process = multiprocessing.Process(target=run_background_scripts)
            background_process.start()
        else:
            print("Scripts de background ainda em execução. Jogo adicionado à fila.")
        # --- FIM DA LÓGICA DE BACKGROUND ---

        if should_stop_tournament: break

    # --- FIM DO LOOP ALTERADO ---

    # --- ALTERADO: Esperar pelo processo final ---
    print("\nTorneio visual concluído. Aguardando processo de background final...")
    if background_process is not None and background_process.is_alive():
        print("Aguardando a última execução dos scripts...")
        background_process.join()  # Espera que termine
    print("Todos os processos de background terminaram.")
    # --- FIM DA ALTERAÇÃO ---

    # --- ADICIONADO: Encerrar Pygame ---
    pygame.quit()
    print(f"Torneio concluído. Tempo total: {(time.time() - start_time):.2f} segundos.")


# --- Executar ---
if __name__ == "__main__":
    # Garante que o multiprocessing funciona corretamente (especialmente no Windows)
    multiprocessing.freeze_support()

    run_tournament(MIN_BOT_NUMBER, MAX_BOT_NUMBER, DEFAULT_DEPTH)