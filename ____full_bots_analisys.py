from __main import aux_single_game
import os
import pickle
import matplotlib.pyplot as plt
from tqdm import tqdm
from datetime import datetime

# ================= CONFIG =================
BOT_NUMBER = 25

CHAMPIONS_DIR = r"C:\Users\Afonso Noia\PycharmProjects\NEAT_CHESS\champions"
ELO_PATH = r"C:\Users\Afonso Noia\PycharmProjects\NEAT_CHESS\leaderboard_elo.txt"

PLOTS_ROOT_DIR = r"C:\Users\Afonso Noia\PycharmProjects\NEAT_CHESS\bot_analisys_plots"
# =========================================

# ================= DATE FOLDER =================
today_str = datetime.now().strftime("%d_%m_%Y")
PLOTS_DATE_DIR = os.path.join(PLOTS_ROOT_DIR, today_str)

PLOTS_BY_BOT = os.path.join(PLOTS_DATE_DIR, "by_bot_number")
PLOTS_BY_ELO = os.path.join(PLOTS_DATE_DIR, "by_elo")

os.makedirs(PLOTS_BY_BOT, exist_ok=True)
os.makedirs(PLOTS_BY_ELO, exist_ok=True)

# ================= LOAD BOTS =================
BOT_NUMBER += 1

bots = []
for i in range(BOT_NUMBER):
    with open(os.path.join(CHAMPIONS_DIR, f"champ_{i}.pickle"), "rb") as f:
        bots.append(pickle.load(f))

# ================= STATS STRUCT =================
stats = {
    i: {
        "win": 0,
        "loss": 0,
        "draw": 0,
        "superior_to": 0,
        "inferior_to": 0,
        "equivalent_to": 0
    }
    for i in range(BOT_NUMBER)
}

# ================= ROUND ROBIN =================
print("Starting exhaustive round-robin evaluation...\n")

for i in tqdm(range(BOT_NUMBER)):
    for j in range(i + 1, BOT_NUMBER):

        # ---- Game 1: i vs j ----
        r1 = aux_single_game(bots[i], bots[j], record_game=False)[0]

        if r1 == 1:
            stats[i]["win"] += 1
            stats[j]["loss"] += 1
        elif r1 == 0:
            stats[i]["draw"] += 1
            stats[j]["draw"] += 1
        else:
            stats[i]["loss"] += 1
            stats[j]["win"] += 1

        # ---- Game 2: j vs i ----
        r2 = aux_single_game(bots[j], bots[i], record_game=False)[0]
        r2_i = -r2

        if r2_i == 1:
            stats[i]["win"] += 1
            stats[j]["loss"] += 1
        elif r2_i == 0:
            stats[i]["draw"] += 1
            stats[j]["draw"] += 1
        else:
            stats[i]["loss"] += 1
            stats[j]["win"] += 1

        # ---- SUPERIORITY ----
        results_i = [r1, r2_i]
        wins_i = results_i.count(1)
        losses_i = results_i.count(-1)

        if losses_i == 0 and wins_i >= 1:
            stats[i]["superior_to"] += 1
            stats[j]["inferior_to"] += 1
        elif wins_i == 0 and losses_i >= 1:
            stats[j]["superior_to"] += 1
            stats[i]["inferior_to"] += 1
        else:
            stats[i]["equivalent_to"] += 1
            stats[j]["equivalent_to"] += 1

# ================= LOAD ELO =================
elo_by_bot = {}

with open(ELO_PATH, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if "champ" in line and "Elo:" in line:
            champ_id = int(line.split("champ")[1].split("|")[0].strip())
            elo = float(line.split("Elo:")[1].split("(")[0].strip())
            elo_by_bot[champ_id] = elo

# ================= DATA PREP =================
bots_idx = list(range(BOT_NUMBER))

wins       = [stats[i]["win"] for i in bots_idx]
losses     = [stats[i]["loss"] for i in bots_idx]
draws      = [stats[i]["draw"] for i in bots_idx]
superior   = [stats[i]["superior_to"] for i in bots_idx]
inferior   = [stats[i]["inferior_to"] for i in bots_idx]
equivalent = [stats[i]["equivalent_to"] for i in bots_idx]

elo_sorted_bots = sorted(
    [i for i in bots_idx if i in elo_by_bot],
    key=lambda x: elo_by_bot[x]
)

elo_x = [elo_by_bot[i] for i in elo_sorted_bots]

wins_elo       = [stats[i]["win"] for i in elo_sorted_bots]
losses_elo     = [stats[i]["loss"] for i in elo_sorted_bots]
draws_elo      = [stats[i]["draw"] for i in elo_sorted_bots]
superior_elo   = [stats[i]["superior_to"] for i in elo_sorted_bots]
inferior_elo   = [stats[i]["inferior_to"] for i in elo_sorted_bots]
equivalent_elo = [stats[i]["equivalent_to"] for i in elo_sorted_bots]

# ================= PLOT FUNCTIONS =================
def plot_bar(x, y, title, ylabel, path):
    plt.figure(figsize=(14, 5))
    plt.bar(x, y)
    plt.xlabel("Bot number")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True)
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()

def plot_elo(x, y, title, ylabel, path):
    plt.figure(figsize=(14, 5))
    plt.plot(x, y, marker="o")
    plt.xlabel("Elo")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True)
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()

# ================= SAVE BOT-NUMBER PLOTS =================
plot_bar(bots_idx, wins, "Wins per bot", "Wins",
         os.path.join(PLOTS_BY_BOT, "wins_per_bot.png"))
plot_bar(bots_idx, losses, "Losses per bot", "Losses",
         os.path.join(PLOTS_BY_BOT, "losses_per_bot.png"))
plot_bar(bots_idx, draws, "Draws per bot", "Draws",
         os.path.join(PLOTS_BY_BOT, "draws_per_bot.png"))

plot_bar(bots_idx, superior, "Bots each bot is superior to", "Superior to",
         os.path.join(PLOTS_BY_BOT, "superiority.png"))
plot_bar(bots_idx, inferior, "Bots superior to each bot", "Inferior to",
         os.path.join(PLOTS_BY_BOT, "inferiority.png"))
plot_bar(bots_idx, equivalent, "Equivalent bots", "Equivalent to",
         os.path.join(PLOTS_BY_BOT, "equivalent.png"))

# ================= SAVE ELO PLOTS =================
plot_elo(elo_x, wins_elo, "Wins vs Elo", "Wins",
         os.path.join(PLOTS_BY_ELO, "wins_vs_elo.png"))
plot_elo(elo_x, losses_elo, "Losses vs Elo", "Losses",
         os.path.join(PLOTS_BY_ELO, "losses_vs_elo.png"))
plot_elo(elo_x, draws_elo, "Draws vs Elo", "Draws",
         os.path.join(PLOTS_BY_ELO, "draws_vs_elo.png"))

plot_elo(elo_x, superior_elo, "Superior to vs Elo", "Superior to",
         os.path.join(PLOTS_BY_ELO, "superiority_vs_elo.png"))
plot_elo(elo_x, inferior_elo, "Inferior to vs Elo", "Inferior to",
         os.path.join(PLOTS_BY_ELO, "inferiority_vs_elo.png"))
plot_elo(elo_x, equivalent_elo, "Equivalent to vs Elo", "Equivalent to",
         os.path.join(PLOTS_BY_ELO, "equivalent_vs_elo.png"))

print("\nAnalysis complete.")
print("Plots saved in:", PLOTS_DATE_DIR)
