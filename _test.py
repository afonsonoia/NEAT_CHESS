import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
folder_path = os.path.join(BASE_DIR, 'aux_files', '__puzzles_results')

# Get a list of all file names in the folder (exclude directories)
file_names = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

print("Files in folder:")
for file in file_names:
    print(file)