
def full_reset():
    import time
    import os

    DELETE_CHAMPIONS = True

    path_champions = r"C:\Users\Afonso Noia\PycharmProjects\NEAT_CHESS\champions"
    partial_puzzles_files = r"C:\Users\Afonso Noia\PycharmProjects\NEAT_CHESS\aux_files\__puzzles_results"
    backups_paths = r'backups'
    main_arr = []

    print("\n!!  -----  FULL RESET  -----  !!\n\n")
    for i in range(5):
        print(5-i)
        time.sleep(1)


    # ----- APAGAR TUDO -----

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
