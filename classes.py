import time
import math
import chess
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
        self.optimized_net = None   # None for normal training bots; populated only for champions
        self.genome = genome
        self.config = config
        self.elo = 10.0             # Initial Elo of 10
        self.num_games_played = 0
        self.is_champion = False
        self.champ_num = None
        self.record_champs = [0, 0, 0]

    def generate_optimized_net(self):
        """
        Generates an optimized, mathematically equivalent network for champions.
        Leaves self.net intact and sets self.optimized_net.
        """
        try:
            from fast_evaluator import OptimizedNetwork
            self.optimized_net = OptimizedNetwork(self.net)
            return self.optimized_net
        except Exception as e:
            print(f"Warning: Failed to generate optimized network: {e}")
            self.optimized_net = None
            return None

    def _get_board_input(self, board):
        active_net = getattr(self, 'optimized_net', None) or self.net
        input_size = len(active_net.input_nodes) if hasattr(active_net, 'input_nodes') else 768
        if input_size == 64:
            return get_numeric_board_ai_64(board=board)
        return get_numeric_board_ai(board=board)

    def make_decision(self, board, my_color: int):  # my color: 1 -> white / -1 -> black
        if my_color == 0:
            from time import sleep
            print("WARNING: player color can't be ZERO!!!")
            sleep(5)
            exit()

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        best_move = legal_moves[0]
        best_points = -999999.0

        active_net = getattr(self, 'optimized_net', None) or self.net
        occ_total = board.occupied.bit_count()
        input_size = len(active_net.input_nodes) if hasattr(active_net, 'input_nodes') else 768
        is_64 = (input_size == 64)

        use_delta = (not is_64) and getattr(active_net, '_is_single_direct', False)

        if use_delta:
            dense_w = active_net._dense_weights
            dense_bias = active_net._single_bias
            dense_act = active_net._single_act
            buf = get_numeric_board_ai(board=board)
            base_s = float(np.dot(dense_w, buf))
        elif is_64:
            buf = get_numeric_board_ai_64(board=board).copy()
        else:
            buf = get_numeric_board_ai(board=board).copy()

        # Precompute check and terminal filters for the current board
        turn = board.turn
        enemy_color = not turn
        enemy_king = board.king(enemy_color)
        our_co = board.occupied_co[turn]
        our_rooks_queens = (board.rooks | board.queens) & our_co
        our_bishops_queens = (board.bishops | board.queens) & our_co

        rook_rays = chess.BB_RANK_ATTACKS[enemy_king][0] | chess.BB_FILE_ATTACKS[enemy_king][0]
        bishop_rays = chess.BB_DIAG_ATTACKS[enemy_king][0]

        slider_discovered_rays = 0
        if our_rooks_queens & rook_rays:
            slider_discovered_rays |= rook_rays
        if our_bishops_queens & bishop_rays:
            slider_discovered_rays |= bishop_rays

        knight_attacks = chess.BB_KNIGHT_ATTACKS[enemy_king]
        pawn_attacks = chess.BB_PAWN_ATTACKS[enemy_color][enemy_king]
        has_castling = board.has_castling_rights(turn)
        ep_sq = board.ep_square
        opp_pieces_count = board.occupied_co[enemy_color].bit_count()
        draw_risk = (occ_total <= 4) or (opp_pieces_count <= 3)

        for m in legal_moves:
            pt = board.piece_type_at(m.from_square)
            color = turn
            dest_pt = m.promotion if m.promotion else pt
            is_ep = (ep_sq == m.to_square and pt == chess.PAWN)
            is_castling = (pt == chess.KING and has_castling and board.is_castling(m))

            can_check = True
            if not m.promotion and not is_castling and not is_ep:
                from_bb = 1 << m.from_square
                if not (from_bb & slider_discovered_rays):
                    to_bb = 1 << m.to_square
                    if pt == chess.KNIGHT:
                        can_check = bool(to_bb & knight_attacks)
                    elif pt == chess.PAWN:
                        can_check = bool(to_bb & pawn_attacks)
                    elif pt == chess.KING:
                        can_check = False
                    elif pt == chess.BISHOP:
                        can_check = bool(to_bb & bishop_rays)
                    elif pt == chess.ROOK:
                        can_check = bool(to_bb & rook_rays)
                    else:
                        can_check = bool(to_bb & (bishop_rays | rook_rays))

            if use_delta:
                off_from = ((pt - 1) if color else (pt + 5)) * 64
                off_to = ((dest_pt - 1) if color else (dest_pt + 5)) * 64
                delta = dense_w[off_to + (m.to_square ^ 56)] - dense_w[off_from + (m.from_square ^ 56)]

                if is_ep:
                    ep_sq_val = m.to_square + (-8 if color else 8)
                    delta -= dense_w[(6 if color else 0) * 64 + (ep_sq_val ^ 56)]
                elif board.occupied & (1 << m.to_square):
                    cap_pt = board.piece_type_at(m.to_square)
                    cap_off = ((cap_pt - 1) if enemy_color else (cap_pt + 5)) * 64
                    delta -= dense_w[cap_off + (m.to_square ^ 56)]
                elif is_castling:
                    if m.to_square == chess.G1:
                        delta += dense_w[3 * 64 + (chess.F1 ^ 56)] - dense_w[3 * 64 + (chess.H1 ^ 56)]
                    elif m.to_square == chess.C1:
                        delta += dense_w[3 * 64 + (chess.D1 ^ 56)] - dense_w[3 * 64 + (chess.A1 ^ 56)]
                    elif m.to_square == chess.G8:
                        delta += dense_w[9 * 64 + (chess.F8 ^ 56)] - dense_w[9 * 64 + (chess.H8 ^ 56)]
                    elif m.to_square == chess.C8:
                        delta += dense_w[9 * 64 + (chess.D8 ^ 56)] - dense_w[9 * 64 + (chess.A8 ^ 56)]

                if can_check or draw_risk:
                    board.push(m)
                    if board.is_check():
                        if board.is_checkmate():
                            board.pop()
                            return m
                        points = float(dense_act(dense_bias + (base_s + delta))) * my_color
                    elif (occ_total <= 4 and board.is_insufficient_material()) or (board.occupied_co[board.turn].bit_count() <= 3 and board.is_stalemate()):
                        points = 0.0
                    else:
                        points = float(dense_act(dense_bias + (base_s + delta))) * my_color
                    board.pop()
                else:
                    points = float(dense_act(dense_bias + (base_s + delta))) * my_color

            else:
                # General buffer-based path for non-direct networks or 64-input models
                if is_64:
                    idx_from = m.from_square ^ 56
                    idx_to = m.to_square ^ 56
                    old_to = buf[idx_to]
                    val = PIECE_VALUES_64[dest_pt] if color else -PIECE_VALUES_64[dest_pt]
                    buf[idx_from] = 0.0
                    buf[idx_to] = val
                    if is_ep:
                        ep_sq_idx = (m.to_square + (-8 if color else 8)) ^ 56
                        old_ep = buf[ep_sq_idx]
                        buf[ep_sq_idx] = 0.0
                    elif is_castling:
                        if m.to_square == chess.G1:
                            rf, rt, rv = chess.H1 ^ 56, chess.F1 ^ 56, PIECE_VALUES_64[chess.ROOK]
                        elif m.to_square == chess.C1:
                            rf, rt, rv = chess.A1 ^ 56, chess.D1 ^ 56, PIECE_VALUES_64[chess.ROOK]
                        elif m.to_square == chess.G8:
                            rf, rt, rv = chess.H8 ^ 56, chess.F8 ^ 56, -PIECE_VALUES_64[chess.ROOK]
                        elif m.to_square == chess.C8:
                            rf, rt, rv = chess.A8 ^ 56, chess.D8 ^ 56, -PIECE_VALUES_64[chess.ROOK]
                        buf[rf] = 0.0
                        buf[rt] = rv
                else:
                    off_from = ((pt - 1) if color else (pt + 5)) * 64
                    off_to = ((dest_pt - 1) if color else (dest_pt + 5)) * 64
                    idx_from = off_from + (m.from_square ^ 56)
                    idx_to = off_to + (m.to_square ^ 56)
                    buf[idx_from] = 0.0

                    cap_idx = None
                    ep_idx = None
                    if is_ep:
                        ep_sq_val = m.to_square + (-8 if color else 8)
                        ep_off = (6 if color else 0) * 64
                        ep_idx = ep_off + (ep_sq_val ^ 56)
                        buf[ep_idx] = 0.0
                    elif board.occupied & (1 << m.to_square):
                        cap_pt = board.piece_type_at(m.to_square)
                        cap_off = ((cap_pt - 1) if enemy_color else (cap_pt + 5)) * 64
                        cap_idx = cap_off + (m.to_square ^ 56)
                        buf[cap_idx] = 0.0
                    elif is_castling:
                        if m.to_square == chess.G1:
                            rf_idx, rt_idx = 3 * 64 + (chess.H1 ^ 56), 3 * 64 + (chess.F1 ^ 56)
                        elif m.to_square == chess.C1:
                            rf_idx, rt_idx = 3 * 64 + (chess.A1 ^ 56), 3 * 64 + (chess.D1 ^ 56)
                        elif m.to_square == chess.G8:
                            rf_idx, rt_idx = 9 * 64 + (chess.H8 ^ 56), 9 * 64 + (chess.F8 ^ 56)
                        elif m.to_square == chess.C8:
                            rf_idx, rt_idx = 9 * 64 + (chess.A8 ^ 56), 9 * 64 + (chess.D8 ^ 56)
                        buf[rf_idx] = 0.0
                        buf[rt_idx] = 1.0

                    buf[idx_to] = 1.0

                if can_check or draw_risk:
                    board.push(m)
                    if board.is_check():
                        if board.is_checkmate():
                            board.pop()
                            return m
                        points = float(active_net.activate(buf)[0]) * my_color
                    elif (occ_total <= 4 and board.is_insufficient_material()) or (board.occupied_co[board.turn].bit_count() <= 3 and board.is_stalemate()):
                        points = 0.0
                    else:
                        points = float(active_net.activate(buf)[0]) * my_color
                    board.pop()
                else:
                    points = float(active_net.activate(buf)[0]) * my_color

                # Revert delta on buffer
                if is_64:
                    buf[idx_from] = val if not m.promotion else (PIECE_VALUES_64[chess.PAWN] if color else -PIECE_VALUES_64[chess.PAWN])
                    buf[idx_to] = old_to
                    if is_ep:
                        buf[ep_sq_idx] = old_ep
                    elif is_castling:
                        buf[rf] = rv
                        buf[rt] = 0.0
                else:
                    buf[idx_from] = 1.0
                    buf[idx_to] = 0.0
                    if ep_idx is not None:
                        buf[ep_idx] = 1.0
                    elif cap_idx is not None:
                        buf[cap_idx] = 1.0
                    elif is_castling:
                        buf[rf_idx] = 1.0
                        buf[rt_idx] = 0.0

            if points > best_points:
                best_points = points
                best_move = m

        return best_move


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
        active_net = getattr(self, 'optimized_net', None) or self.net
        response_bot = float(active_net.activate(bot_input)[0])  # NN gives score from White's POV

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