from classes import PuzzleV2
import time
import pickle
import os
import random


display_timedout = False
display_diff_full = False

display_diff_partial = True
divisior = 5

processed_file_path = r'./aux_files/processed_moves.fens'
puzzles_file_path = r'aux_files/puzzles_generated.puzzle'

amount_by_depth = {}

if not os.path.isfile(puzzles_file_path):
    print("no file found")
    exit()

sucess_read = False
while not sucess_read:
    try:
        puzzles_file = open(puzzles_file_path, 'rb')
        puzzles_arrV2 = pickle.load(puzzles_file)
        puzzles_file.close()
        sucess_read = True
    except:
        time.sleep(random.random()*0.5)

sucess_read = False
while not sucess_read:
    try:
        processed_file = open(processed_file_path, 'rb')
        processed_arr = pickle.load(processed_file)
        processed_file.close()
        sucess_read = True
    except:
        time.sleep(random.random()*0.5)


for puzzle in puzzles_arrV2:
    #print(f"{puzzle.get_fen().ljust(80)} - {puzzle.get_best_move_str()} - depth: {puzzle.depth_checked} - counter total: {puzzle.counterTotal} - passed: {puzzle.counterPassed} - diff: {puzzle.dificulty}")
    if str(puzzle.depth_checked) not in amount_by_depth:
        amount_by_depth[str(puzzle.depth_checked)] = 1
    else:
        amount_by_depth[str(puzzle.depth_checked)] += 1

# display stats
print(f"\namount of puzzles: {len(puzzles_arrV2)}")
print()
sorted_amount_by_depth = {int(k): v for k, v in sorted(amount_by_depth.items())}

for key, value in sorted_amount_by_depth.items():
    print(f"Depth {key}: {value}")

print()
print(f"\nPositions processed: {len(processed_arr[0]) + len(processed_arr[1])}")
print(f"full check: {len(processed_arr[0])} - timed out: {len(processed_arr[1])}\n")

if display_timedout:
    print("Timed out fens:")
    for f in processed_arr[1]:
        print(f)

count_total_tests = 0


for puzzle in puzzles_arrV2:
    if display_diff_full:
        print(f"{puzzle.get_fen().ljust(100)} - diff: {puzzle.counterPassed} / {puzzle.counterTotal} ({puzzle.dificulty}) ")
    count_total_tests += puzzle.counterTotal
print("\nTotal atempts:", count_total_tests, "\n\n")
if display_diff_partial:
    counter = 0
    for puzzle in puzzles_arrV2:
        counter += 1
        count_total_tests += puzzle.counterTotal
        if counter%divisior == 0:
            print(f"{counter}: {puzzle.get_fen().ljust(100)} - diff: {puzzle.counterPassed} / {puzzle.counterTotal} ({puzzle.dificulty})")

time.sleep(90)
