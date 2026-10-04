from __main import aux_single_game
import os
import pickle

# Total number of bots (0 through 115 inclusive)
BOT_NUMBER = 48
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
path_champions = os.path.join(BASE_DIR, "champions")

# Load all bots
all_bots = []
for i in range(BOT_NUMBER + 1):  # include bot 115
    bot_path = os.path.join(path_champions, f"champ_{i}.pickle")
    with open(bot_path, 'rb') as f:
        bot = pickle.load(f)
        all_bots.append((i, bot))  # store tuple (id, bot)

# Initialize stats for every bot
stats = {
    i: {"win": 0, "draw": 0, "loss": 0, "games": 0}
    for i in range(BOT_NUMBER + 1)
}

# Round-robin tournament: every bot plays against every other
for i in range(len(all_bots)):
    id1, bot1 = all_bots[i]
    for j in range(i + 1, len(all_bots)):
        id2, bot2 = all_bots[j]

        # Game 1: bot1 as white
        result1 = aux_single_game(bot1, bot2, record_game=False)[0]
        if result1 == 1:
            stats[id1]["win"] += 1
            stats[id2]["loss"] += 1
        elif result1 == 0:
            stats[id1]["draw"] += 1
            stats[id2]["draw"] += 1
        else:
            stats[id1]["loss"] += 1
            stats[id2]["win"] += 1
        stats[id1]["games"] += 1
        stats[id2]["games"] += 1

        # Game 2: bot2 as white
        result2 = aux_single_game(bot2, bot1, record_game=False)[0]
        if result2 == 1:
            stats[id2]["win"] += 1
            stats[id1]["loss"] += 1
        elif result2 == 0:
            stats[id1]["draw"] += 1
            stats[id2]["draw"] += 1
        else:
            stats[id2]["loss"] += 1
            stats[id1]["win"] += 1
        stats[id1]["games"] += 1
        stats[id2]["games"] += 1

    # ✅ Progress print
    print(f"Analysed {i+1} out of {BOT_NUMBER+1} bots...")

# Build leaderboard: sort by win ratio
leaderboard = []
for bot_id, record in stats.items():
    games = record["games"]
    winrate = record["win"] / games if games > 0 else 0
    leaderboard.append((bot_id, winrate, record))

leaderboard.sort(key=lambda x: x[1], reverse=True)

# Save leaderboard to file
output_file = os.path.join(path_champions, "leaderboard.txt")
with open(output_file, "w") as f:
    f.write("Leaderboard (sorted by winrate)\n")
    f.write("="*40 + "\n\n")
    for rank, (bot_id, winrate, record) in enumerate(leaderboard, start=1):
        line = (f"{rank}. champ{bot_id} | "
                f"Winrate: {winrate:.2%} | "
                f"W: {record['win']} D: {record['draw']} L: {record['loss']} "
                f"Games: {record['games']}\n")
        f.write(line)

print(f"\n✅ Leaderboard saved to {output_file}")
