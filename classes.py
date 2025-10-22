import time
from aux_neat_funcs import *

LICHESS_TOKEN = 'lip_R8Smg69o2Uproe0Wm21F'

def generateSortValuePuzzlesV2(puzzleV2):
    numericValue = puzzleV2.dificulty + min(min(puzzleV2.counterTotal, 1000000)/1000, 30)
    return numericValue


def get_fen_from_move(main_fen, move):
    import chess
    aux_board = chess.Board(main_fen)
    aux_board.push(move)
    new_fen = aux_board.fen()
    aux_board.pop()
    return new_fen


class Puzzle:
    def __init__(self, fen, best_move_str, white_to_move:bool):
        self.fen = fen
        self.best_move_str = best_move_str
        self.white_to_move = white_to_move

    def get_puzzle_fen(self):
        return self.fen

    def get_puzzle_correct_move_str(self):
        return self.best_move_str

    def is_white_to_move(self):
        return self.white_to_move


class PuzzleV2:

    def __init__(self, fen, best_moves_list_strs:list, white:bool, depth_checked:int):
        self.fen = fen
        self.best_moves_list_strs = best_moves_list_strs
        self.counterTotal = 0
        self.counterPassed = 0
        self.dificulty = 200  # %
        self.white = white
        self.depth_checked = depth_checked

    def get_fen(self):
        return self.fen

    def get_best_moves_list_strs(self):
        return self.best_moves_list_strs

    def update_depth_checked(self, new_depth, sudo=False):
        if sudo:
            self.depth_checked = new_depth
        else:
            self.depth_checked = max(self.depth_checked, new_depth)

    def count(self, correct=False):
        self.counterTotal += 1
        if correct:
            self.counterPassed += 1
        if self.counterTotal >= 1:    # min games to get diff
            self.dificulty = round(100 * (1-(self.counterPassed / self.counterTotal)), 2)
        else:
            self.dificulty = 200


class PuzzlesV3Arr:

    def __init__(self):
        self.arrPuzzles = [[], []]
        self.aux_int = 1

    def updateFullArrPuzzles(self, newArrPuzzles):
        self.arrPuzzles = newArrPuzzles
        # force sorting data
        self.sortPuzzlesV2(True)
        self.sortPuzzlesV2(False)

    def getFullArr(self):
        return self.arrPuzzles

    def insertPuzzleV2(self, puzzleV2:PuzzleV2, iswhite:bool):
        if iswhite:
            self.arrPuzzles[0].append(puzzleV2)
        else:
            self.arrPuzzles[1].append(puzzleV2)

    def sortPuzzlesV2(self, iswhite):
        if iswhite:
            self.arrPuzzles[0].sort(key=generateSortValuePuzzlesV2)
        else:
            self.arrPuzzles[1].sort(key=generateSortValuePuzzlesV2)

    def getTotalAmount(self, iswhite):
        if iswhite:
            return len(self.arrPuzzles[0])
        else:
            return len(self.arrPuzzles[1])


class theoryPoint:
    def __init__(self, fen, bestMove, depth):
        self.fen = fen
        self.bestMove = bestMove
        self.depth = depth

    def getFen(self):
        return self.fen

    def getBestMove(self):
        return self.bestMove

    def getDepth(self):
        return self.depth


class theoryData:
    def __init__(self, includeAllDepth=6):
        self.completeDatabaseDepth = -1
        self.numPositionsInDB = 0
        self.numAnalisedPositions = 0
        self.includeAllDepth = includeAllDepth
        self.theoryDict = {}


    def getDictResponse(self, fen):
        if fen in self.theoryDict:
            return self.theoryDict[fen]
        else:
            return None

    def setIncludeAllDepth(self, depth):
        self.includeAllDepth = depth
        return

    def getDataBaseDepth(self):
        return self.completeDatabaseDepth

    def getNumPosDB(self):
        return self.numPositionsInDB

    def getNumPosAnalisadas(self):
        return self.numAnalisedPositions

    def setCompleteDatabaseDepth(self, newDepth, newAmountAnalisadas):
        if newDepth > self.completeDatabaseDepth:
            self.completeDatabaseDepth = newDepth
        else:
            print("Erro: depth inserida < ao valor anterior")

        if newAmountAnalisadas > self.numAnalisedPositions:
            self.numAnalisedPositions = newAmountAnalisadas
        else:
            print("Erro: num de posicoes inseridas < valor anterior")
        return

    def insertNew(self, fen, bestMove, depth):
        if not self.getDictResponse(fen):
            newEntry = theoryPoint(fen=fen, bestMove=bestMove, depth=depth)
            self.theoryDict[fen] = newEntry
            self.numPositionsInDB += 1
        else:
            print("Erro: valor já existe na DB da teoria")
        return

    def getBestMove(self, fen):
        return self.theoryDict[fen].getBestMove()

    def getLastFronteira(self):
        import chess

        display_loading = 10000

        fronteira = []
        actual_move = self.completeDatabaseDepth
        print("\nLoading Last Fronteira...\n")
        if actual_move <= self.includeAllDepth:
            for fen in self.theoryDict:
                board = chess.Board(fen=fen)
                if self.theoryDict[fen].getDepth() == self.completeDatabaseDepth:
                    for m in board.legal_moves:
                        new_fen = get_fen_from_move(fen, m)
                        fronteira.append(new_fen)
                        if len(fronteira) % display_loading == 0:
                            print(f"imported {len(fronteira)}")
            print("\nFinished loading Last Fronteira\n\n")
            return fronteira

        else:
            print("incomplete - todo")
            exit()


class Bot:
    def __init__(self, genome, config):
        from custom_neat_lib.nn import FeedForwardNetwork
        net = FeedForwardNetwork.create(genome, config)
        self.net = net
        self.genome = genome
        self.config = config
        self.elo = 10.0             # Elo inicial de 10
        self.num_games_played = 0
        self.is_champion = False
        self.champ_num = None

        # self.mem_hit_miss = [0, 0]
        # self.max_memory_storage = 50000
        # self.memory_amount = 0
        # self.memory = {}
        # self.mem_frequency = {}

    def make_decision(self, board, my_color: int):  # my color: 1 -> white / -1 -> black
        if my_color == 0:
            from time import sleep
            print("WARNING: player color can't be ZERO!!!")
            sleep(5)
            exit()

        DEBUG_MODE = False

        best_move = [None, -999999]  # [move, points]
        outputs_debug = []

        legal_moves = []
        for lm in board.legal_moves:
            legal_moves.append(lm)

        # random.shuffle(legal_moves)
        for m in legal_moves:
            board.push(m)

            # if outcome for this move:
            if board.outcome() is not None:
                board.pop()
                return m

            # NOTA: Assume que get_numeric_board_ai está definida/importada
            # Esta função precisa de estar disponível.
            # ex: from teu_ficheiro_utils import get_numeric_board_ai
            bot_input = get_numeric_board_ai(board_str=board.__str__())
            response_bot = self.net.activate(bot_input)[0]  # running NN

            # A NN dá uma pontuação da perspetiva das Brancas.
            # Multiplicamos por my_color (1 para Brancas, -1 para Pretas)
            # para obter a pontuação da perspetiva do bot.
            response_bot *= my_color

            if DEBUG_MODE:
                print(bot_input)
                print(response_bot)

            if not (isinstance(response_bot, float) or isinstance(response_bot, int)):
                print("Weird Error")
                print(response_bot)
                exit()

            points = response_bot
            outputs_debug.append(points)
            if points > best_move[1]:
                best_move[0] = m
                best_move[1] = points
            board.pop()

        return best_move[0]


    # Esta função é necessária para a pesquisa alpha-beta.
    # Retorna a avaliação estática de um tabuleiro *sem* pesquisar.
    def _get_static_eval(self, board, my_color):
        """
        Obtém a avaliação estática da NN para o estado *atual* do tabuleiro,
        da perspetiva da cor do bot.
        """
        outcome = board.outcome()
        if outcome:
            # Jogo terminado, retorna pontuação de vitória/derrota/empate
            if outcome.winner is True:  # Brancas ganham
                return float('inf') if my_color == 1 else float('-inf')
            elif outcome.winner is False:  # Pretas ganham
                return float('-inf') if my_color == 1 else float('inf')
            else:  # Empate
                return 0

        # NOTA: Assume que get_numeric_board_ai está definida/importada
        bot_input = get_numeric_board_ai(board_str=board.__str__())
        response_bot = self.net.activate(bot_input)[0]  # NN dá pontuação da POV das Brancas

        # Converte pontuação para a perspetiva do bot
        response_bot *= my_color

        return response_bot


    def make_decision_depth(self, board, my_color, depth):
        """
        Usa poda alpha-beta para procurar a melhor jogada até à profundidade especificada.

        Parâmetros:
            board: a instância atual de chess.Board.
            my_color: a cor do bot (1 para brancas, -1 para pretas).
            depth: profundidade da pesquisa.

        Retorna:
            A chess.Move selecionada.
        """

        # Profundidade 1 é uma pesquisa de 1-ply, que make_decision já faz.
        if depth <= 1:
            return self.make_decision(board, my_color)

        def alpha_beta(b, d, alpha, beta):
            # Condição terminal: profundidade atingida ou fim de jogo.
            if d == 0 or b.is_game_over():
                # --- ESTA É A CORREÇÃO ---
                # Em vez de chamar make_decision (que retorna uma jogada),
                # chamamos a nossa nova função helper que retorna uma pontuação.
                return self._get_static_eval(b, my_color)

            # Determina se é a vez do bot.
            is_bot_turn = (b.turn and my_color == 1) or (not b.turn and my_color == -1)

            if is_bot_turn:
                # Vez do Bot: Maximiza a sua própria pontuação
                value = -float('inf')
                for move in b.legal_moves:
                    b.push(move)
                    value = max(value, alpha_beta(b, d - 1, alpha, beta))
                    b.pop()
                    alpha = max(alpha, value)
                    if beta <= alpha:
                        break  # Corte Beta
                return value
            else:
                # Vez do Oponente: Minimiza a pontuação do bot
                value = float('inf')
                for move in b.legal_moves:
                    b.push(move)
                    value = min(value, alpha_beta(b, d - 1, alpha, beta))
                    b.pop()
                    beta = min(beta, value)
                    if beta <= alpha:
                        break  # Corte Alpha
                return value

        best_move = None
        best_value = -float('inf')  # Bot quer sempre maximizar
        alpha = -float('inf')
        beta = float('inf')

        # NOTA: Idealmente, deves ordenar as jogadas (ex: capturas primeiro)
        # para que a poda alpha-beta seja mais eficiente.

        for move in board.legal_moves:
            board.push(move)
            value = alpha_beta(board, depth - 1, alpha, beta)
            board.pop()

            if value > best_value:
                best_value = value
                best_move = move
            alpha = max(alpha, best_value)

        return best_move