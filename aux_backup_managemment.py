BACKUP_FOLDER = r'./backups'


def get_last_backup_path(folder_path=BACKUP_FOLDER):
    import os
    import re

    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"The folder_path '{folder_path}' does not exist.")

    # List all files in the folder_path
    dir_list = os.listdir(folder_path)
    if not dir_list:  # Check if the folder_path is empty
        return None

    backups = []

    # Extract backup files with the format 'backup_[N]'
    for filename in dir_list:
        match = re.match(r'backup_(\d+)', filename)  # Match 'backup_[N]'
        if match:
            n = int(match.group(1))  # Extract the number N
            backups.append((n, os.path.join(folder_path, filename)))  # Store as (N, filepath)

    if not backups:  # No valid backup files found
        return None

    # Find the backup with the largest N
    backups.sort(key=lambda x: x[0])  # Sort by the number N
    return backups[-1][1]  # Return the path of the backup with the largest N


def restore_checkpoint(filename, champions_arr_path):
    import gzip
    import pickle
    import random
    from custom_neat_lib import Population
    """Resumes the simulation from a previous saved point."""
    with gzip.open(filename) as f:
        generation, config, population, species_set, rndstate = pickle.load(f)
        generation += 1  # making new generation
        random.setstate(rndstate)
        return Population(config, (population, species_set, generation), champions_arr_path)


