import os
BACKUP_FOLDER = 'backups'


def get_last_backup_path(folder_path=BACKUP_FOLDER):
    import os
    import re

    if not os.path.exists(folder_path):
        script_folder = os.path.join(os.path.dirname(__file__), folder_path)
        if os.path.exists(script_folder):
            folder_path = os.path.relpath(script_folder)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
        return None

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


def restore_checkpoint(filename, champions_arr_path, config=None):
    import gzip
    import pickle
    import random
    from custom_neat_lib import Population
    """Resumes the simulation from a previous saved point."""
    with gzip.open(filename) as f:
        generation, saved_config, population, species_set, rndstate = pickle.load(f)
        generation += 1  # making new generation
        random.setstate(rndstate)
        active_config = config if config is not None else saved_config
        if config is not None and hasattr(saved_config, 'pop_size'):
            active_config.pop_size = config.pop_size
        return Population(active_config, (population, species_set, generation), champions_arr_path)


