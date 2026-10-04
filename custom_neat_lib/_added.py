

def generateSortValuePuzzlesV2(puzzleV2):
    diff = getattr(puzzleV2, 'difficulty', getattr(puzzleV2, 'dificulty', 200))
    numericValue = diff + min(min(puzzleV2.counterTotal, 1000000)/1000, 30)
    return numericValue


def copy_file(path_original, path_output):
    import shutil
    shutil.copy2(path_original, path_output)

def checkFileExistance(path):
    import os
    if os.path.isfile(path):
        return True
    else:
        return False

def getPickleData(path):

    if not checkFileExistance(path):
        return None
    else:
        import pickle
        with open(path, 'rb') as file:
            received_data = pickle.load(file)

        return received_data


def savePickleData(path, data_to_save):
    import os
    import pickle
    dirname = os.path.dirname(path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with open(path, 'wb') as file:
        pickle.dump(data_to_save, file)
    return


def save_files_secure_backups():
    import os
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    original_path = os.path.join(project_root, 'aux_files')
    secure_backups_path = os.path.join(project_root, '_secure_backups', 'auto puzzles')
    os.makedirs(original_path, exist_ok=True)
    os.makedirs(secure_backups_path, exist_ok=True)

    files_to_copy = [r'processed_moves.fens', r'puzzles_generated.puzzle']

    for file_name in files_to_copy:
        path_i = os.path.join(original_path, file_name)
        path_f = os.path.join(secure_backups_path, file_name)
        if os.path.isfile(path_i):
            copy_file(path_i, path_f)
    return


def update_puzzles_diff():
    import os
    import pickle
    from classes import generateSortValuePuzzlesV2

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    original_path = os.path.join(project_root, 'human_puzzles', 'all_files', 'twic_and_gms.puzzle')
    if not os.path.isfile(original_path):
        original_path = os.path.join(project_root, 'human_puzzles', 'human_moves_stream.puzzle')

    partials_path = os.path.join(project_root, 'aux_files', '__puzzles_results')
    os.makedirs(partials_path, exist_ok=True)

    # Get a list of all file names in the folder (exclude directories)
    file_names = [f for f in os.listdir(partials_path) if os.path.isfile(os.path.join(partials_path, f))]

    if len(file_names) == 0:
        print("No puzzle files to update")
        return
    else:
        print("Updating puzzles diff")

    if not os.path.isfile(original_path):
        print(f"Warning: Puzzle file not found at {original_path}. Skipping puzzle diff update.")
        return

    # --- Read stream format (puzzle by puzzle) into a list ---
    all_puzzles = []
    with open(original_path, 'rb') as f:
        while True:
            try:
                all_puzzles.append(pickle.load(f))
            except EOFError:
                break

    # fen -> [correct, wrong]
    all_results = {}

    # extract results content from files
    for filename in file_names:
        path_file = os.path.join(partials_path, filename)
        results = getPickleData(path_file)  # Kept because results were saved normally
        for fen in results:
            if results[fen] == 1:
                if fen in all_results:
                    all_results[fen][0] += 1
                else:
                    all_results[fen] = [1, 0]
            else:
                if fen in all_results:
                    all_results[fen][1] += 1
                else:
                    all_results[fen] = [0, 1]

    # delete files
    for filename in file_names:
        path_file = os.path.join(partials_path, filename)
        os.remove(path_file)

    # update main file contents
    for i in range(len(all_puzzles)):
        if all_puzzles[i].get_fen() in all_results:
            # total tries
            all_puzzles[i].counterTotal += all_results[all_puzzles[i].get_fen()][0] + all_results[all_puzzles[i].get_fen()][1]

            # total wins
            all_puzzles[i].counterPassed += all_results[all_puzzles[i].get_fen()][0]

            # trick to update difficulty
            all_puzzles[i].counterTotal -= 1
            all_puzzles[i].count(False)

    # sort puzzles
    all_puzzles.sort(key=generateSortValuePuzzlesV2)

    # --- Write back in stream format to prevent excessive RAM usage ---
    with open(original_path, 'wb') as f:
        for p in all_puzzles:
            pickle.dump(p, f)

    print("Finished updating puzzles diff")

