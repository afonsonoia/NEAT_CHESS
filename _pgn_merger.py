
def merge_pgns(name):
    import os
    import time
    from aux_PGN_reader import get_full_paths_in_folder, count_games, get_pgn_at_index, get_pgn_header_at_index, get_games_headers_arr
    import re

    filename_output = name + ".pgn"

    output_file_path = os.path.join("aux_files", filename_output)
    folder_pgns_to_merge = "_pgns_to_merge"

    all_pgns_paths = get_full_paths_in_folder(folder_pgns_to_merge)

    # iterate files
    output_content = []
    count_elems = [0, 0]    # new / repeated
    display_counts = 10     # frequency


    def delete_files_in_folder(folder_path, display:bool):
        # Get the list of files in the folder
        file_list = os.listdir(folder_path)

        # Iterate through the files and delete each one
        for file_name in file_list:
            file_path = os.path.join(folder_path, file_name)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    if display:
                        print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")


    for pgnPath in all_pgns_paths:
        print(f"\n\nStarting file: {pgnPath}\n\n")
        current_file = open(pgnPath, 'r')
        content_file = current_file.read()
        current_file.close()

        arr_games_headers = get_games_headers_arr(pgnPath)
        num_games = count_games(pgnPath)

        for i in range(num_games):
            # display
            if count_elems[0] % display_counts == 0:
                print(f"unique pgns: {count_elems[0]} - repeated pgns: {count_elems[1]}")

            pgn_header = arr_games_headers[i*2]
            pgn_raw = arr_games_headers[i*2+1]

            if ((len(pgn_raw) < 250) and ('{' in pgn_raw)) or (len(pgn_raw) < 50):
                continue

            pgn_clean = pgn_raw.replace("...", ".")
            pgn_clean = pgn_clean.replace("\n", "")

            # Remove anything within curly braces and the braces themselves
            pgn_clean = re.sub(r'\{[^}]*\}', '', pgn_clean)

            for _ in range(3):
                pgn_clean = pgn_clean.replace("  ", " ")

            if pgn_clean not in output_content:
                count_elems[0] += 1
                output_content.append(pgn_header)
                output_content.append(pgn_clean)
            else:
                print(pgn_clean)
                print("---\n")
                #print(pgn_header)
                print(pgn_raw)
                print("\n---")
                count_elems[1] += 1

    print(f"unique pgns: {count_elems[0]} - repeated pgns: {count_elems[1]}\n")
    print(f"Saving new pgn to: {output_file_path}")

    output_file = open(output_file_path, "w")
    for line in output_content:
        output_file.write(str(line) + '\n\n')
    output_file.close()

    print("Deleting original pgns!")
    time.sleep(5)
    delete_files_in_folder(folder_pgns_to_merge, display=False)

    print("Finished!")

if __name__ == '__main__':
    name = input("Insert pgns name: ")
    merge_pgns(name)

