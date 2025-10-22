def merge_pgns(name):
    import os
    import time
    from aux_PGN_reader import get_full_paths_in_folder, count_games, get_pgn_header_at_index, get_games_headers_arr
    import re

    filename_output = name + ".pgn"
    output_file_path = os.path.join("aux_files\\_pgns_database", filename_output)
    folder_pgns_to_merge = "_pgns_to_merge_2"

    all_pgns_paths = get_full_paths_in_folder(folder_pgns_to_merge)

    # Exit early if no input PGN files found
    if not all_pgns_paths:
        print("No PGN files to merge. Exiting without creating output file.")
        return

    # Output collection
    output_content = []
    count_elems = [0, 0]  # [unique, repeated]
    display_counts = 10

    def delete_files_in_folder(folder_path, display: bool):
        file_list = os.listdir(folder_path)
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
        with open(pgnPath, 'r') as current_file:
            content_file = current_file.read()

        arr_games_headers = get_games_headers_arr(pgnPath)
        num_games = count_games(pgnPath)

        for i in range(num_games):
            if count_elems[0] % display_counts == 0:
                print(f"unique pgns: {count_elems[0]} - repeated pgns: {count_elems[1]}")

            pgn_header = arr_games_headers[i * 2]
            pgn_raw = arr_games_headers[i * 2 + 1]

            if ((len(pgn_raw) < 250 and '{' in pgn_raw) or len(pgn_raw) < 50):
                continue

            pgn_clean = pgn_raw.replace("...", ".").replace("\n", "")
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
                print(pgn_raw)
                print("\n---")
                count_elems[1] += 1

    print(f"unique pgns: {count_elems[0]} - repeated pgns: {count_elems[1]}\n")

    # Save output only if there are valid unique PGNs
    if output_content:
        print(f"Saving new pgn to: {output_file_path}")
        with open(output_file_path, "w") as output_file:
            for line in output_content:
                output_file.write(str(line) + '\n\n')
    else:
        print("No valid PGNs to write. Output file not created.")

    print("Deleting original pgns!")
    time.sleep(5)
    delete_files_in_folder(folder_pgns_to_merge, display=False)

    print("Finished!")

if __name__ == '__main__':
    name = "local_games"
    merge_pgns(name)
