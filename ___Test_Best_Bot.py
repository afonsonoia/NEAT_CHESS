from __main import aux_single_game
import os
import pickle

BOT_NUMBER = 15

path_champions = r"C:\Users\Afonso Noia\PycharmProjects\NEAT_CHESS\champions"
main_bot_path = os.path.join(path_champions, "champ_"+str(BOT_NUMBER)+".pickle")
all_bots_list = []

with open(main_bot_path, 'rb') as f:
    main_bot = pickle.load(f)

for i in range(BOT_NUMBER):
    bot_path = os.path.join(path_champions, "champ_"+str(i)+".pickle")
    with open(bot_path, 'rb') as f:
        bot = pickle.load(f)
        all_bots_list.append(bot)

stats = {"win":0, "draw":0, "loss":0}
for bot in all_bots_list:
    result_game_1 = aux_single_game(main_bot, bot, record_game=False)[0]
    print(result_game_1)
    if result_game_1 == 1:
        stats["win"] += 1
    elif result_game_1 == 0:
        stats["draw"] += 1
    else:
        stats["loss"] += 1

    result_game_2 = aux_single_game(bot, main_bot, record_game=False)[0]*-1
    print(result_game_2)
    if result_game_2 == 1:
        stats["win"] += 1
    elif result_game_2 == 0:
        stats["draw"] += 1
    else:
        stats["loss"] += 1

    print()

print(stats)