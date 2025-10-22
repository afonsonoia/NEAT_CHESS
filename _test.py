import os

# Specify the folder path (change this to your directory)
folder_path = r'C:\Users\Afonso Noia\PycharmProjects\NEAT_CHESS\aux_files\__puzzles_results'

# Get a list of all file names in the folder (exclude directories)
file_names = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

print("Files in folder:")
for file in file_names:
    print(file)