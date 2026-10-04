import time
import math
from aux_neat_funcs import *


def generateSortValuePuzzlesV2(puzzleV2):
    diff = getattr(puzzleV2, 'difficulty', getattr(puzzleV2, 'dificulty', 200))
    numericValue = diff + min(min(puzzleV2.counterTotal, 1000000)/1000, 30)
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
        self.difficulty = 200  # %
        self.dificulty = 200   # backwards compatibility alias
        self.white = white
        self.depth_checked = depth_checked

    def get_fen(self):
        return self.fen

    def get_best_moves_list_strs(self):
        if hasattr(self, 'best_moves_list_strs'):
            return self.best_moves_list_strs
        if hasattr(self, 'best_move_str'):
            return [self.best_move_str]
        return []

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
            calc_diff = round(100 * (1-(self.counterPassed / self.counterTotal)), 2)
            self.difficulty = calc_diff
            self.dificulty = calc_diff
        else:
            self.difficulty = 200
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
        self.numAnalyzedPositions = 0
        self.numAnalisedPositions = 0  # backwards compatibility alias
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

    def getNumPosAnalyzed(self):
        return getattr(self, 'numAnalyzedPositions', getattr(self, 'numAnalisedPositions', 0))

    def getNumPosAnalisadas(self):
        """Backwards-compatibility alias for getNumPosAnalyzed."""
        return self.getNumPosAnalyzed()

    def setCompleteDatabaseDepth(self, newDepth, newAmountAnalyzed):
        if newDepth > self.completeDatabaseDepth:
            self.completeDatabaseDepth = newDepth
        else:
            print("Error: inserted depth < previous value")

        curr_analyzed = getattr(self, 'numAnalyzedPositions', getattr(self, 'numAnalisedPositions', 0))
        if newAmountAnalyzed > curr_analyzed:
            self.numAnalyzedPositions = newAmountAnalyzed
            self.numAnalisedPositions = newAmountAnalyzed
        else:
            print("Error: number of inserted positions < previous value")
        return

    def insertNew(self, fen, bestMove, depth):
        if not self.getDictResponse(fen):
            newEntry = theoryPoint(fen=fen, bestMove=bestMove, depth=depth)
            self.theoryDict[fen] = newEntry
            self.numPositionsInDB += 1
        else:
            print("Error: value already exists in theory DB")
        return

    def getBestMove(self, fen):
        return self.theoryDict[fen].getBestMove()

    def getLastFrontier(self):
        import chess

        display_loading = 10000

        frontier = []
        actual_move = self.completeDatabaseDepth
        print("\nLoading Last Frontier...\n")
        if actual_move <= self.includeAllDepth:
            for fen in self.theoryDict:
                board = chess.Board(fen=fen)
                if self.theoryDict[fen].getDepth() == self.completeDatabaseDepth:
                    for m in board.legal_moves:
                        new_fen = get_fen_from_move(fen, m)
                        frontier.append(new_fen)
                        if len(frontier) % display_loading == 0:
                            print(f"imported {len(frontier)}")
            print("\nFinished loading Last Frontier\n\n")
            return frontier

        else:
            print("incomplete - todo")
            exit()

    def getLastFronteira(self):
        """Backwards-compatibility alias for getLastFrontier."""
        return self.getLastFrontier()


class Bot:
    def __init__(self, genome, config):
        from custom_neat_lib.nn import FeedForwardNetwork
        net = FeedForwardNetwork.create(genome, config)
        self.net = net
        self.genome = genome
        self.config = config
        self.elo = 10.0             # Initial Elo of 10
        self.num_games_played = 0
        self.is_champion = False
        self.champ_num = None
        self.record_champs = [0, 0, 0]

        # self.mem_hit_miss = [0, 0]
        # self.max_memory_storage = 50000
        # self.memory_amount = 0
        # self.memory = {}
        # self.mem_frequency = {}

    def _get_board_input(self, board):
        input_size = len(self.net.input_nodes) if hasattr(self, 'net') and hasattr(self.net, 'input_nodes') else 768
        if input_size == 64:
            return get_numeric_board_ai_64(board.__str__())
        return get_numeric_board_ai(board_str=board.__str__(), board=board)

    def make_decision(self, board, my_color: int):  # my color: 1 -> white / -1 -> black
        if my_color == 0:
            from time import sleep
            print("WARNING: player color can't be ZERO!!!")
            sleep(5)
            exit()

        DEBUG_MODE = False

        best_move = [None, -999999]  # [move, points]
        outputs_debug = []

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        best_move = [legal_moves[0], -999999.0]  # [move, points]
        outputs_debug = []

        for m in legal_moves:
            board.push(m)

            outcome = board.outcome()
            if outcome is not None:
                # If it's a win for the bot, play immediately!
                if (outcome.winner is True and my_color == 1) or (outcome.winner is False and my_color == -1):
                    board.pop()
                    return m
                elif (outcome.winner is False and my_color == 1) or (outcome.winner is True and my_color == -1):
                    points = -99999.0
                else:  # Draw (stalemate, repetition, etc.)
                    points = 0.0
            else:
                bot_input = self._get_board_input(board)
                response_bot = float(self.net.activate(bot_input)[0])  # running NN
                response_bot *= my_color
                points = response_bot

            if DEBUG_MODE:
                print(bot_input)
                print(points)

            if not (isinstance(points, (float, int)) or (isinstance(points, np.number) and not np.isnan(points))):
                print("Weird Error")
                print(points)
                exit()

            outputs_debug.append(points)
            if points > best_move[1]:
                best_move[0] = m
                best_move[1] = points
            board.pop()

        return best_move[0]


    # This function is required for alpha-beta search.
    # Returns the static evaluation of a board *without* searching.
    def _get_static_eval(self, board, my_color):
        """
        Gets the static NN evaluation for the *current* board state,
        from the perspective of the bot's color.
        """
        outcome = board.outcome()
        if outcome:
            # Game over: return win/loss/draw score
            if outcome.winner is True:  # White wins
                return float('inf') if my_color == 1 else float('-inf')
            elif outcome.winner is False:  # Black wins
                return float('-inf') if my_color == 1 else float('inf')
            else:  # Draw
                return 0

        bot_input = self._get_board_input(board)
        response_bot = float(self.net.activate(bot_input)[0])  # NN gives score from White's POV

        # Convert score to bot's perspective
        response_bot *= my_color

        return response_bot


    def make_decision_depth(self, board, my_color, depth):
        """
        Uses alpha-beta pruning to search for the best move up to the specified depth.

        Parameters:
            board: current chess.Board instance.
            my_color: bot's color (1 for White, -1 for Black).
            depth: search depth.

        Returns:
            The selected chess.Move.
        """

        # Depth 1 is a 1-ply search, which make_decision already performs.
        if depth <= 1:
            return self.make_decision(board, my_color)

        def alpha_beta(b, d, alpha, beta):
            # Terminal condition: depth reached or game over.
            if d == 0 or b.is_game_over():
                return self._get_static_eval(b, my_color)

            # Determine if it's the bot's turn.
            is_bot_turn = (b.turn and my_color == 1) or (not b.turn and my_color == -1)

            if is_bot_turn:
                # Bot's turn: Maximize its own score
                value = -float('inf')
                for move in b.legal_moves:
                    b.push(move)
                    value = max(value, alpha_beta(b, d - 1, alpha, beta))
                    b.pop()
                    alpha = max(alpha, value)
                    if beta <= alpha:
                        break  # Beta cut-off
                return value
            else:
                # Opponent's turn: Minimize bot's score
                value = float('inf')
                for move in b.legal_moves:
                    b.push(move)
                    value = min(value, alpha_beta(b, d - 1, alpha, beta))
                    b.pop()
                    beta = min(beta, value)
                    if beta <= alpha:
                        break  # Alpha cut-off
                return value

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        best_move = legal_moves[0]
        best_value = -float('inf')  # Bot always wants to maximize
        alpha = -float('inf')
        beta = float('inf')

        # Note: ideally order moves (e.g. captures first) for efficient alpha-beta pruning.

        for move in legal_moves:
            board.push(move)
            value = alpha_beta(board, depth - 1, alpha, beta)
            board.pop()

            if value > best_value:
                best_value = value
                best_move = move
            alpha = max(alpha, best_value)

        return best_move