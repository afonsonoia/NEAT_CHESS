
def full_reset():
    import time
    import os

    DELETE_CHAMPIONS = True

    base_dir = os.path.dirname(os.path.abspath(__file__))
    path_champions = os.path.join(base_dir, "champions")
    partial_puzzles_files = os.path.join(base_dir, "aux_files", "__puzzles_results")
    backups_paths = os.path.join(base_dir, "backups")
    os.makedirs(path_champions, exist_ok=True)
    os.makedirs(partial_puzzles_files, exist_ok=True)
    os.makedirs(backups_paths, exist_ok=True)
    main_arr = []

    print("\n!!  -----  FULL RESET  -----  !!\n\n")
    for i in range(5):
        print(5-i)
        time.sleep(1)


    # ----- DELETE ALL -----

    # BACKUPS
    f_names = os.listdir(backups_paths)
    for fn in f_names:
        path = os.path.join(backups_paths, fn)
        os.remove(path)

    # CHAMPIONS
    if DELETE_CHAMPIONS:
        f_names = os.listdir(path_champions)
        for fn in f_names:
            path = os.path.join(path_champions, fn)
            os.remove(path)

    # PUZZLES PARTIAL FILES
    f_names = os.listdir(partial_puzzles_files)
    for fn in f_names:
        path = os.path.join(partial_puzzles_files, fn)
        os.remove(path)

    print("\nAll deleted!")


if __name__ == "__main__":
    full_reset()
