import os
import pickle
from tqdm import tqdm

base_dir = os.path.dirname(os.path.abspath(__file__))
input_puzzle_path = os.path.join(base_dir, 'human_puzzles', 'human_moves.puzzle')
output_puzzle_path = os.path.join(base_dir, 'human_puzzles', 'human_moves_stream.puzzle')

if not os.path.isfile(input_puzzle_path):
    print(f"Input puzzle file not found at: {input_puzzle_path}")
    exit()

os.makedirs(os.path.dirname(output_puzzle_path), exist_ok=True)

print("1. Loading large file into RAM (this may take a while)...")
with open(input_puzzle_path, 'rb') as f:
    large_puzzle_list = pickle.load(f)

total_puzzles = len(large_puzzle_list)
print(f"-> File loaded successfully! Found {total_puzzles:,} puzzles.")
print("2. Starting write to new sequential stream format...\n")

# Save deconstructed file (puzzle by puzzle) with progress bar
with open(output_puzzle_path, 'wb') as f:
    # tqdm wraps the list and automatically displays the progress bar
    for puzzle in tqdm(large_puzzle_list, desc="Saving puzzles", unit="puz"):
        pickle.dump(puzzle, f)

print("\nDone! Conversion finished perfectly.")
print("You can delete the old 'human_moves.puzzle' file to free up disk space and use the new stream file!")