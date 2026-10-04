import requests
import json
import time

small_delay = 5

username = input("Enter Chess.com username: ")
headers = {
    'User-Agent': username
}

# Retrieve a list of archives
all_data = []
game_counter = 0
for url in requests.get(f"https://api.chess.com/pub/player/{username}/games/archives", headers=headers).json()[
    "archives"]:
    all_data.append(requests.get(url, headers=headers).json())
    time.sleep(small_delay)
    for game in all_data[-1]["games"]:
        game_counter += 1
    print(f"Games: {game_counter}")


# Retrieve games from archives
games = []
for row in all_data:
    for game in row["games"]:
        games.append(game)


print("\nSaving games to file")

# Save PGN data
with open(str(username) + "_raw" + ".pgn", "w") as file:
    for game in games:
        try:
            file.write(game["pgn"] + "\n")
        except:
            continue

# chesswarrior7197
# VincentKeymer