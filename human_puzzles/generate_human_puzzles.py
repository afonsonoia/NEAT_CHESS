import os
import chess.pgn
import multiprocessing
import logging
import time
import threading
import pickle
import tkinter as tk
import heapq
import random  # For 90% filtering
import glob  # For cleanup of temporary files
from concurrent.futures import ProcessPoolExecutor, as_completed
from io import StringIO
from tqdm import tqdm

from aux_PGN_reader import get_pgn_at_index, count_games, get_full_paths_in_folder
from aux_funcs_random import get_current_time_str_print
from classes import PuzzleV2

logging.getLogger("chess.pgn").setLevel(logging.CRITICAL)

# ===================================================================
# 0. GENERAL CONFIGURATION
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
PGN_FOLDER_PATH = os.path.join(PROJECT_ROOT, 'aux_files', 'BIG_BUCKET')
OUTPUT_DIR = os.path.join(BASE_DIR, 'all_files')
FINAL_PUZZLE_NAME = 'twic_and_gms.puzzle'

MAX_ITEMS_PER_CHUNK = 500_000
MAX_PLY_PER_GAME = 200
# ===================================================================

worker_shared_delay = None


def init_worker(shared_val):
    global worker_shared_delay
    worker_shared_delay = shared_val


def process_single_pgn_file(filepath):
    base_name = os.path.basename(filepath)
    temp_filename = os.path.join(OUTPUT_DIR, f"temp_{base_name}.pkl")

    # -----------------------------------------------------------------
    # REQUIREMENT 1: RESUME PROGRESS (Resumable Execution)
    # If final file already exists, skip heavy processing!
    # -----------------------------------------------------------------
    if os.path.exists(temp_filename):
        return filepath, temp_filename, 0

    local_positions = {}
    num_games_in_file = count_games(filepath)
    games_processed = 0

    for i in range(num_games_in_file):
        current_delay = worker_shared_delay.value
        if current_delay > 0:
            time.sleep(current_delay)

        pgn_raw = get_pgn_at_index(filepath, i)
        if not pgn_raw or len(pgn_raw) < 50 or '@' in pgn_raw:
            continue

        pgn = chess.pgn.read_game(StringIO(pgn_raw))
        if pgn is None or pgn.errors:
            continue

        board = chess.Board()
        ply_count = 0

        for move in pgn.mainline_moves():
            if ply_count >= MAX_PLY_PER_GAME:
                break

            fen = board.fen()
            moving_color = board.turn
            move_str = move.uci()

            if fen not in local_positions:
                local_positions[fen] = {"moves": set(), "color": moving_color}
            local_positions[fen]["moves"].add(move_str)
            board.push(move)
            ply_count += 1

        games_processed += 1

    sorted_items = sorted(local_positions.items(), key=lambda x: x[0])

    # Save to temporary ".tmp" file (Atomic Write)
    temp_filename_tmp = temp_filename + ".tmp"
    with open(temp_filename_tmp, "wb") as f:
        for fen, data in sorted_items:
            pickle.dump((fen, list(data["moves"]), data["color"]), f)

    # Rename to final name only when 100% written
    os.rename(temp_filename_tmp, temp_filename)

    return filepath, temp_filename, games_processed


def stream_pickle_file(filepath):
    with open(filepath, 'rb') as f:
        while True:
            try:
                yield pickle.load(f)
            except EOFError:
                break


class BucketManager:
    def __init__(self, base_dir, max_items_per_chunk):
        self.base_dir = base_dir
        self.max_items = max_items_per_chunk
        self.active_files = {}
        self.chunk_indices = {}
        self.item_counts = {}

    def add_puzzle(self, move_count, puzzle):
        if move_count not in self.active_files:
            self.chunk_indices[move_count] = 1
            self.item_counts[move_count] = 0
            path = os.path.join(self.base_dir, f"balde_{move_count}_1.pkl")
            self.active_files[move_count] = open(path, "wb")

        if self.item_counts[move_count] >= self.max_items:
            self.active_files[move_count].close()
            self.chunk_indices[move_count] += 1
            self.item_counts[move_count] = 0
            path = os.path.join(self.base_dir, f"balde_{move_count}_{self.chunk_indices[move_count]}.pkl")
            self.active_files[move_count] = open(path, "wb")

        pickle.dump(puzzle, self.active_files[move_count])
        self.item_counts[move_count] += 1

    def close_all(self):
        for f in self.active_files.values():
            f.close()

    def get_ordered_chunks(self):
        sorted_counts = sorted(self.chunk_indices.keys(), reverse=True)
        ordered_paths = []
        for count in sorted_counts:
            max_chunk = self.chunk_indices[count]
            for i in range(1, max_chunk + 1):
                ordered_paths.append(os.path.join(self.base_dir, f"balde_{count}_{i}.pkl"))
        return ordered_paths


def run_heavy_processing(shared_delay):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_pickle_path = os.path.join(OUTPUT_DIR, FINAL_PUZZLE_NAME)

    pgn_files = get_full_paths_in_folder(PGN_FOLDER_PATH)
    pgn_files.sort(key=os.path.getsize, reverse=True)

    print("\n" * 2)
    print(get_current_time_str_print() + f" PHASE 1: Parallel Extraction (Limit: {MAX_PLY_PER_GAME} plies)...")
    print("-" * 60)

    if pgn_files:
        largest_mb = os.path.getsize(pgn_files[0]) / (1024 * 1024)
        smallest_mb = os.path.getsize(pgn_files[-1]) / (1024 * 1024)
        print(f"ℹ️ LPT Order Active: {len(pgn_files)} files queued.")
        print(f"ℹ️ From largest ({largest_mb:.1f} MB) to smallest ({smallest_mb:.1f} MB).\n")

    temp_files_generated = []
    total_processed_games = 0
    num_cores = multiprocessing.cpu_count()

    with ProcessPoolExecutor(max_workers=num_cores, initializer=init_worker, initargs=(shared_delay,)) as executor:
        futures = {executor.submit(process_single_pgn_file, path): path for path in pgn_files}
        with tqdm(total=len(pgn_files), desc="Completed Files", unit="file", colour="blue") as pbar:
            for future in as_completed(futures):
                try:
                    filepath, temp_filepath, games = future.result()
                    total_processed_games += games
                    temp_files_generated.append(temp_filepath)

                    file_name = os.path.basename(filepath)

                    # If games == 0, read from cache/resume!
                    if games == 0:
                        tqdm.write(f"[{get_current_time_str_print().strip()}] [CACHE] Resumed: {file_name}")
                    else:
                        size_mb = os.path.getsize(filepath) / (1024 * 1024)
                        tqdm.write(f"[{get_current_time_str_print().strip()}] [CPU] Completed: {file_name} ({size_mb:.1f} MB)")

                    pbar.set_postfix({"New Games": f"{total_processed_games:,}"})
                    pbar.update(1)

                except Exception as exc:
                    tqdm.write(f"\n[ERROR] {exc}")

    print("\n" + get_current_time_str_print() + " PHASE 2: Smart Merge (Merge Sort)...")
    print("-" * 60)

    streams = [stream_pickle_file(f) for f in temp_files_generated]
    bucket_manager = BucketManager(OUTPUT_DIR, max_items_per_chunk=MAX_ITEMS_PER_CHUNK)

    current_fen = None
    current_moves = set()
    current_color = None
    total_unique_positions = 0

    with tqdm(desc="Merged Unique Positions", unit="pos", colour="yellow") as pbar_merge:
        for fen, moves, color in heapq.merge(*streams, key=lambda x: x[0]):
            if fen != current_fen:
                if current_fen is not None:
                    total_unique_positions += 1
                    puzzle = PuzzleV2(current_fen, list(current_moves), current_color, 99)
                    bucket_manager.add_puzzle(len(current_moves), puzzle)
                    pbar_merge.update(1)

                current_fen = fen
                current_moves = set(moves)
                current_color = color
            else:
                current_moves.update(moves)

        if current_fen is not None:
            total_unique_positions += 1
            puzzle = PuzzleV2(current_fen, list(current_moves), current_color, 99)
            bucket_manager.add_puzzle(len(current_moves), puzzle)
            pbar_merge.update(1)

    bucket_manager.close_all()

    print("\n" + get_current_time_str_print() + " PHASE 3: Random Filtering and Final Assembly...")
    print("-" * 60)

    ordered_chunks = bucket_manager.get_ordered_chunks()
    puzzles_saved = 0
    puzzles_removed = 0

    with open(output_pickle_path, "wb") as final_out:
        with tqdm(total=total_unique_positions, desc="Saving .puzzle File", unit="pos", colour="green") as pbar_final:
            for chunk_path in ordered_chunks:
                with open(chunk_path, "rb") as chunk_in:
                    while True:
                        try:
                            obj = pickle.load(chunk_in)

                            # -----------------------------------------------------------------
                            # REQUIREMENT 3: REMOVE 90% OF PUZZLES WITH ONLY 1 OPTION
                            # -----------------------------------------------------------------
                            try:
                                valid_moves = obj.get_best_moves_list_strs()
                            except AttributeError:
                                valid_moves = obj.moves if hasattr(obj, 'moves') else []

                            if len(valid_moves) == 1:
                                if random.random() < 0.90:  # 90% chance to discard puzzle
                                    puzzles_removed += 1
                                    pbar_final.update(1)
                                    continue  # Skip saving and continue

                            pickle.dump(obj, final_out)
                            puzzles_saved += 1
                            pbar_final.update(1)

                        except EOFError:
                            break
                os.remove(chunk_path)

    # -----------------------------------------------------------------
    # REQUIREMENT 2: DELETE ALL TEMPORARY FILES AT THE END
    # -----------------------------------------------------------------
    print("\n" + get_current_time_str_print() + " Cleaning temporary files from disk...")

    # Clean completed .pkl files
    for f in temp_files_generated:
        if os.path.exists(f):
            try:
                os.remove(f)
            except:
                pass

    # Clean interrupted .tmp traces
    interrupted_tmp = glob.glob(os.path.join(OUTPUT_DIR, "temp_*.pkl.tmp"))
    for f in interrupted_tmp:
        try:
            os.remove(f)
        except:
            pass

    print("\n" + 100 * "=")
    print(get_current_time_str_print() + " COMPLETE SUCCESS!")
    print(f"Total new games processed: {total_processed_games:,}")
    print(f"Puzzles Removed by Filter (1 option): {puzzles_removed:,}")
    print(f"Total Puzzles Saved to Disk: {puzzles_saved:,}")
    print(f"File saved at: {output_pickle_path}")


if __name__ == '__main__':
    shared_delay = multiprocessing.Value('d', 0.0)
    processing_thread = threading.Thread(target=run_heavy_processing, args=(shared_delay,), daemon=True)
    processing_thread.start()

    root = tk.Tk()
    root.title("CPU Throttling - MapReduce Pipeline")
    root.geometry("500x200")
    root.configure(padx=20, pady=20)
    lbl_title = tk.Label(root, text="Adjust processor load:", font=("Arial", 12, "bold"))
    lbl_title.pack(pady=(0, 10))
    lbl_info = tk.Label(root, text="0s = Maximum Usage (Fast)\n1.0s = Very Light Usage (Slow)", font=("Arial", 12))
    lbl_info.pack(pady=(0, 15))


    def update_delay(val):
        shared_delay.value = float(val)


    slider = tk.Scale(root, from_=0.0, to=1.0, resolution=0.001, orient=tk.HORIZONTAL, length=500, command=update_delay)
    slider.pack()
    root.mainloop()