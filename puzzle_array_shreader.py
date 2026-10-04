import pickle
from tqdm import tqdm

print("1. Loading large file into RAM (this may take a while)...")
with open(r'human_puzzles/human_moves.puzzle', 'rb') as f:
    large_puzzle_list = pickle.load(f)

total_puzzles = len(large_puzzle_list)
print(f"-> File loaded successfully! Found {total_puzzles:,} puzzles.")
print("2. Starting write to new sequential stream format...\n")

# Save deconstructed file (puzzle by puzzle) with progress bar
with open(r'human_puzzles/human_moves_stream.puzzle', 'wb') as f:
    # tqdm wraps the list and automatically displays the progress bar
    for puzzle in tqdm(large_puzzle_list, desc="Saving puzzles", unit="puz"):
        pickle.dump(puzzle, f)

print("\nDone! Conversion finished perfectly.")
print("You can delete the old 'human_moves.puzzle' file to free up disk space and use the new stream file!")