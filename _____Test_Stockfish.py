from stockfish import Stockfish


DEPTH_stockfish = 38
THREADS = 8

engine_path = r'./stockfish_16/stockfish-windows-x86-64-avx2.exe'
puzzles_file_path = r'aux_files/puzzles_generated.puzzle'

# stockfish setup
stockfish_stronger = Stockfish(path=engine_path, depth=DEPTH_stockfish, parameters={"Threads": THREADS})

new_fen = input("fen: ")


stockfish_stronger.set_fen_position(new_fen)
moves = stockfish_stronger.get_top_moves()

for move in moves:
    print(move)







