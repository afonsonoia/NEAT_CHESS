import os
import sys
import numpy as np
import chess

# Ensure local relative imports work on any PC regardless of execution directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import custom_neat_lib
from classes import Bot
from aux_neat_funcs import get_numeric_board_ai


def test_tactical_positions_and_delta_equivalence():
    """
    Verifies that the incremental O(1) delta evaluation produces 100% mathematically
    identical output values to the ground-truth full buffer evaluation across all move
    types (promotions, en-passant, castling for both sides, checks, stalemates).
    """
    config_path = '_chess_config.txt'
    if not os.path.isfile(config_path):
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '_chess_config.txt')

    config = custom_neat_lib.Config(
        custom_neat_lib.DefaultGenome,
        custom_neat_lib.DefaultReproduction,
        custom_neat_lib.DefaultSpeciesSet,
        custom_neat_lib.DefaultStagnation,
        config_path
    )

    genome = config.genome_type(0)
    genome.configure_new(config.genome_config)
    bot = Bot(genome, config)

    test_fens = [
        chess.STARTING_FEN,
        "r1bqk2r/pp2pP1p/2n3p1/2p5/2B5/5N2/PPPP1PPP/R1BQK2R w KQkq - 1 9",
        "4k3/1P6/8/8/8/8/6p1/4K3 w - - 0 1",
        "4k3/1P6/8/8/8/8/6p1/4K3 b - - 0 1",
        "rnbqkbnr/pppp1ppp/8/4pP2/8/8/PPPPP1PP/RNBQKBNR w KQkq e6 0 3",
        "rnbqkbnr/ppppp1pp/8/8/4Pp2/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 3",
        "r3k2r/pppq1ppp/2np1n2/2b1p1B1/2B1P1b1/2NP1N2/PPPQ1PPP/R3K2R w KQkq - 6 8",
        "r3k2r/pppq1ppp/2np1n2/2b1p1B1/2B1P1b1/2NP1N2/PPPQ1PPP/R3K2R b KQkq - 6 8",
        "r1bqkb1r/pppp1ppp/2n5/4p3/2B1n3/5Q2/PPPP1PPP/RNB1K1NR w KQkq - 0 4",
        "k7/8/1Q6/8/8/8/8/7K b - - 0 1",
        "8/5pk1/4p1p1/R3P2p/5P1P/6P1/4r3/6K1 w - - 0 41",
    ]

    active_net = bot.net
    dense_w = active_net._dense_weights
    dense_bias = active_net._single_bias
    dense_act = active_net._single_act

    for fen in test_fens:
        board = chess.Board(fen)
        buf = get_numeric_board_ai(board=board).copy()
        base_s = float(np.dot(dense_w, buf))

        turn = board.turn
        enemy_color = not turn
        has_castling = board.has_castling_rights(turn)
        ep_sq = board.ep_square

        for m in board.legal_moves:
            pt = board.piece_type_at(m.from_square)
            dest_pt = m.promotion if m.promotion else pt
            is_ep = (ep_sq == m.to_square and pt == chess.PAWN)
            is_castling = (pt == chess.KING and has_castling and board.is_castling(m))

            off_from = ((pt - 1) if turn else (pt + 5)) * 64
            off_to = ((dest_pt - 1) if turn else (dest_pt + 5)) * 64
            idx_from = off_from + (m.from_square ^ 56)
            idx_to = off_to + (m.to_square ^ 56)

            buf[idx_from] = 0.0
            cap_idx = None
            ep_idx = None
            if is_ep:
                ep_sq_val = m.to_square + (-8 if turn else 8)
                ep_off = (6 if turn else 0) * 64
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
            expected_eval = float(active_net.activate(buf)[0])

            buf[idx_from] = 1.0
            buf[idx_to] = 0.0
            if ep_idx is not None:
                buf[ep_idx] = 1.0
            elif cap_idx is not None:
                buf[cap_idx] = 1.0
            elif is_castling:
                buf[rf_idx] = 1.0
                buf[rt_idx] = 0.0

            delta = dense_w[off_to + (m.to_square ^ 56)] - dense_w[off_from + (m.from_square ^ 56)]
            if is_ep:
                ep_sq_val = m.to_square + (-8 if turn else 8)
                delta -= dense_w[(6 if turn else 0) * 64 + (ep_sq_val ^ 56)]
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

            actual_eval = float(dense_act(dense_bias + (base_s + delta)))
            diff = abs(expected_eval - actual_eval)
            assert diff <= 1e-12, f"Mismatch in FEN {fen} on move {m}: diff={diff}"


if __name__ == "__main__":
    test_tactical_positions_and_delta_equivalence()
    print("All mathematical correctness assertions PASSED successfully!")
