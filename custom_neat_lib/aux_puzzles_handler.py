def get_full_paths_in_folder(folder_path):
    import os
    file_paths = []

    # Iterate through all files in the specified folder
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            file_paths.append(file_path)

    return file_paths

def count_games(filename):
    with open(filename, 'r') as file:
        content = file.read()

    # Split the content into individual games using double newline characters
    games = content.split('\n\n')

    # Count the number of games (divide by 2 to exclude event headers)
    num_games = len(games) // 2

    return num_games

def get_games_headers_arr(filename):
    with open(filename, 'r') as file:
        content = file.read()

    # Split the content into individual games using double newline characters
    content = content.split('\n\n')

    return content

