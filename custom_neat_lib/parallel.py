import os
import pickle
import re
import math
from multiprocessing import Pool
# Make sure this import works from your main script
# It's used by the multiprocessing Pool
from __main import aux_single_game


class ParallelEvaluator(object):
    def __init__(self, num_workers, eval_function, timeout=None):
        """
        eval_function should take one argument, a tuple of
        (genome object, config object, champions_list, generation_number),
        and return a tuple of (fitness, new_champion_or_None).
        """
        self.num_workers = num_workers
        self.eval_function = eval_function
        self.timeout = timeout
        self.pool = Pool(num_workers)

        # --- Elo Configuration ---
        # As requested:
        self.initial_elo = 5.0
        self.min_elo = 1.0
        self.k_base = 30
        self.k_min = 5

        self.all_bots = []  # Cache for loaded bots

    def __del__(self):
        self.pool.close()
        self.pool.join()

    def evaluate(self, genomes, config, champions_path, generation_number):
        jobs = []
        new_champion = None

        # --- Load all existing champions ---
        arr_champions = []
        aux_files_arr = []

        for filename in os.listdir(champions_path):
            match = re.match(r'champ_(\d+)\.pickle', filename)
            if match:
                n = int(match.group(1))
                aux_files_arr.append((n, os.path.join(champions_path, filename)))

        sorted_filenames = sorted(aux_files_arr, key=lambda x: x[0])
        for _, file_path in sorted_filenames:
            with open(file_path, 'rb') as f:
                arr_champions.append(pickle.load(f))

        # --- Evaluate genomes in parallel ---
        for ignored_genome_id, genome in genomes:
            jobs.append(self.pool.apply_async(self.eval_function, (genome, config, arr_champions, generation_number)))

        new_champion = None
        for job, (ignored_genome_id, genome) in zip(jobs, genomes):
            arr_outputs = job.get(timeout=self.timeout)
            if arr_outputs is None:
                genome.fitness = -1
            else:
                genome.fitness = arr_outputs[0]
                if arr_outputs[1]:
                    new_champion = arr_outputs[1]

        # --- Save new champion and reorder leaderboard ---
        if new_champion:
            new_champion.champ_num = len(arr_champions)
            new_champion.is_champion = True
            print("\nNEW CHAMPION\n")
            name_file = f"champ_{len(arr_champions)}.pickle"
            full_path = os.path.join(champions_path, name_file)
            with open(full_path, 'wb') as f:
                pickle.dump(new_champion, f)

            # Run incremental ELO evaluation and reorder champions
            # This function was changed to run games in PARALLEL.
            self.evaluate_and_rank_incremental(champions_path)

    # --------------------------------------------------------------------------
    # --- ELO HELPER METHODS ---
    # --------------------------------------------------------------------------

    def _get_k_factor(self, bot):
        """Calculates the dynamic K-Factor for a bot."""
        # We use +1 to avoid log2(0) on the first game
        k = self.k_base - math.log2(bot.num_games_played + 1)
        return max(self.k_min, k)  # Ensures the minimum K of 5

    def _update_elo(self, bot1, bot2, score_bot1):
        """
        Updates the Elo of two bots based on a game result.
        score_bot1: 1.0 for win, 0.5 for draw, 0.0 for loss.
        """
        # 1. Get K-Factors for both bots
        k1 = self._get_k_factor(bot1)
        k2 = self._get_k_factor(bot2)

        # 2. Calculate expected score
        r1 = bot1.elo
        r2 = bot2.elo
        e1 = 1 / (1 + 10 ** ((r2 - r1) / 400))
        e2 = 1 - e1

        # 3. Calculate new Elo score
        s1 = score_bot1
        s2 = 1 - s1
        new_r1 = bot1.elo + k1 * (s1 - e1)
        new_r2 = bot2.elo + k2 * (s2 - e2)

        # 4. Apply Elo floor and update
        bot1.elo = max(self.min_elo, new_r1)
        bot2.elo = max(self.min_elo, new_r2)

        # 5. Increment game count
        bot1.num_games_played += 1
        bot2.num_games_played += 1

    def _process_game_result(self, bot1, bot2, result_code):
        """
        Processes a game result and updates Elo/stats.
        This is the SEQUENTIAL part.
        """
        if result_code == 1:  # bot1 (White) wins
            score_bot1 = 1.0
            bot1.record_champs[0] += 1
            bot2.record_champs[2] += 1
        elif result_code == 0:  # Draw
            score_bot1 = 0.5
            bot1.record_champs[1] += 1
            bot2.record_champs[1] += 1
        else:  # bot1 (White) loses
            score_bot1 = 0.0
            bot1.record_champs[2] += 1
            bot2.record_champs[0] += 1

        # Update Elo based on the result
        self._update_elo(bot1, bot2, score_bot1)

    def _play_game_and_update_elo(self, bot1, bot2):
        """
        Helper function for SEQUENTIAL mode (like the full round-robin).
        Plays a game AND updates Elo.
        """
        result_code = aux_single_game(bot1, bot2, record_game=False)[0]
        self._process_game_result(bot1, bot2, result_code)

    def _load_bots(self, reset_tournament_records=False):
        """Loads all bots and initializes Elo attributes if they don't exist."""
        self.all_bots = []
        files = [f for f in os.listdir(self.champions_path) if f.startswith("champ_") and f.endswith(".pickle")]
        files = sorted(files, key=lambda x: int(x.split("_")[1].split(".")[0]))

        for fname in files:
            path = os.path.join(self.champions_path, fname)
            with open(path, "rb") as f:
                bot = pickle.load(f)

            # --- Initialize Elo attributes if it's an old bot ---
            if not hasattr(bot, "elo"):
                bot.elo = self.initial_elo
            if not hasattr(bot, "num_games_played"):
                bot.num_games_played = 0

            # Zero the (W/D/L) record *just for this tournament*
            # This is still needed for internal tracking, but won't be written to the file
            if not hasattr(bot, "record_champs") or reset_tournament_records:
                bot.record_champs = [0, 0, 0]

            self.all_bots.append((bot.champ_num, bot, path))

        self.all_bots.sort(key=lambda x: x[0])  # Sort by ID

    def _save_bots_and_leaderboard(self, leaderboard_title):
        """Saves bots, creates leaderboard, and renames files."""

        # 1. Build Leaderboard (now with Elo)
        # We no longer need to append w, d, l
        leaderboard = []
        for idx, bot, _ in self.all_bots:
            leaderboard.append((idx, bot.elo, bot.num_games_played))

        # Sort by Elo (highest first)
        leaderboard.sort(key=lambda x: x[1], reverse=True)

        # 2. Save Leaderboard file
        parent_folder = os.path.dirname(self.champions_path)
        output_file = os.path.join(parent_folder, "leaderboard_elo.txt")
        with open(output_file, "w") as f:
            f.write(f"{leaderboard_title} (sorted by Elo)\n")
            f.write("=" * 60 + "\n\n")
            # Updated loop to unpack only 3 items and write the cleaned-up string
            for rank, (bot_id, elo, games) in enumerate(leaderboard, start=1):
                f.write(f"{rank}. champ{bot_id} | Elo: {elo:.2f} (Games: {games})\n")

        print(f"\n✅ Elo Leaderboard saved to {output_file}")

        # 3. Rename files (from weakest to strongest, by Elo)
        temp_dir = os.path.join(self.champions_path, "temp")
        os.makedirs(temp_dir, exist_ok=True)

        # Sort by Elo (lowest first) to get new IDs
        leaderboard.sort(key=lambda x: x[1])

        id_map = {}  # Maps old ID -> new ID
        # Updated loop to unpack only 3 items
        for new_idx, (old_bot_id, _, _) in enumerate(leaderboard):
            id_map[old_bot_id] = new_idx

        # Update the bot's internal ID and save it *before* moving
        for old_bot_id, bot, old_path in self.all_bots:
            # If the bot isn't in the id_map (rare case), do nothing
            if old_bot_id not in id_map:
                print(f"WARNING: Bot with ID {old_bot_id} not found in leaderboard. Skipping rename.")
                continue

            new_idx = id_map[old_bot_id]
            bot.champ_num = new_idx
            with open(old_path, "wb") as f:
                pickle.dump(bot, f)

            # Move to the temp directory with the *new* name
            new_path_temp = os.path.join(temp_dir, f"champ_{new_idx}.pickle")
            # Handle case where file already exists (rare, but can happen if OS is slow)
            if os.path.exists(new_path_temp):
                os.remove(new_path_temp)
            os.rename(old_path, new_path_temp)

        # 4. Move files back
        for fname in os.listdir(temp_dir):
            os.rename(os.path.join(temp_dir, fname), os.path.join(self.champions_path, fname))
        os.rmdir(temp_dir)

        print("✅ Champions renamed (weakest -> strongest) by Elo.")

    # --------------------------------------------------------------------------
    # --- PUBLIC EVALUATION METHODS (ELO-BASED) ---
    # --------------------------------------------------------------------------

    def evaluate_and_rank(self, champions_path):
        """
        Full round-robin evaluation (All-vs-All) using Elo.
        This function runs 100% SEQUENTIALLY.
        """
        self.champions_path = champions_path  # Ensure the path is set
        self._load_bots(reset_tournament_records=True)

        print(f"▶ Starting full (Sequential) round-robin Elo evaluation for {len(self.all_bots)} bots...")

        total_bots = len(self.all_bots)
        total_games = (total_bots * (total_bots - 1))
        game_count = 0

        if total_games == 0:
            print("Not enough bots for a round-robin.")
            return

        for i in range(total_bots):
            id1, bot1, path1 = self.all_bots[i]
            for j in range(i + 1, total_bots):
                id2, bot2, path2 = self.all_bots[j]

                # Game 1: bot1 (White) vs bot2 (Black)
                self._play_game_and_update_elo(bot1, bot2)

                # Game 2: bot2 (White) vs bot1 (Black)
                self._play_game_and_update_elo(bot2, bot1)

                game_count += 2
                print(f"  Games {game_count}/{total_games} completed... (Bot {id1} vs {id2})", end="\r")

        print(f"\n▶ Full round-robin complete. Saving results...")
        self._save_bots_and_leaderboard("Full Round-Robin Elo Leaderboard")

    def evaluate_and_rank_incremental(self, champions_path):
        """
        Incremental evaluation: tests only the newest bot against all previous ones.
        Games run in PARALLEL, but Elo is calculated SEQUENTIALLY.
        """
        self.champions_path = champions_path  # Ensure the path is set
        self._load_bots(reset_tournament_records=True)  # Zero W/D/L for this run

        if len(self.all_bots) < 2:
            print("Not enough bots for incremental evaluation.")
            return

        # Find the newest bot (highest ID)
        self.all_bots.sort(key=lambda x: x[0], reverse=True)
        last_id, last_bot, last_path = self.all_bots[0]
        previous_bots = self.all_bots[1:]

        print(f"▶ Evaluating champ_{last_id} (Elo: {last_bot.elo:.2f}) against {len(previous_bots)} bots...")

        total_games = len(previous_bots) * 2

        if total_games == 0:
            print(f"▶ champ_{last_id} is the first bot. No incremental evaluation.")
            return

        # --- PHASE 1: Submit all games to the Parallel Pool ---
        parallel_jobs = []
        print(f"Submitting {total_games} games to the pool of {self.num_workers} workers...")

        for prev_id, prev_bot, prev_path in previous_bots:
            # Game 1: last_bot (White) vs prev_bot (Black)
            # We pass (bot1, bot2, record_game=False)
            job1 = self.pool.apply_async(aux_single_game, (last_bot, prev_bot, False))
            parallel_jobs.append((job1, last_bot, prev_bot))

            # Game 2: prev_bot (White) vs last_bot (Black)
            job2 = self.pool.apply_async(aux_single_game, (prev_bot, last_bot, False))
            parallel_jobs.append((job2, prev_bot, last_bot))

        # --- PHASE 2: Collect results (blocks until all are done) ---
        print("Waiting for all games to complete...")
        game_results_for_sequencing = []
        game_count = 0
        for job, bot1, bot2 in parallel_jobs:
            try:
                # Get the result (may time out)
                result_data = job.get(timeout=self.timeout)
                result_code = result_data[0]
                # Store for Phase 3
                game_results_for_sequencing.append((bot1, bot2, result_code))
            except Exception as e:
                print(f"\nERROR in parallel game between {bot1.champ_num} and {bot2.champ_num}: {e}")
                # Decide how to handle: here, we just ignore the result

            game_count += 1
            print(f"  Game {game_count}/{total_games} completed...", end="\r")

        print("\nAll games finished.")

        # --- PHASE 3: Process Elo Sequentially ---
        print("Processing Elo updates sequentially...")
        for bot1, bot2, result_code in game_results_for_sequencing:
            # This function applies the Elo and W/D/L update
            self._process_game_result(bot1, bot2, result_code)

        print(f"\n▶ Incremental evaluation complete. Saving results...")
        self._save_bots_and_leaderboard("Incremental Elo Leaderboard")