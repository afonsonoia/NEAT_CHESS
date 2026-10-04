import chess
import customtkinter
import pickle
import os
import pyperclip

contador = 0
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
puzzles_file_path = os.path.join(BASE_DIR, 'aux_files', 'puzzles_generated.puzzle')

if not os.path.isfile(puzzles_file_path):
    print("No Puzzles file Found!")
    exit()

puzzles_file = open(puzzles_file_path, 'rb')
puzzles_arr = pickle.load(puzzles_file)
puzzles_file.close()


def back():
    global contador, puzzles_arr
    if contador > 0:
        contador -= 1
        board = chess.Board(puzzles_arr[0][contador].get_puzzle_fen())
        correct_move = puzzles_arr[0][contador].get_puzzle_correct_move_str()
        print(board.__str__() + "\n")
        print(correct_move, "\n" + "fen: " + board.fen() + "\n\n")
        pyperclip.copy(board.fen())


def next():
    global contador, puzzles_arr
    if contador < len(puzzles_arr[0])-1:
        contador += 1
        board = chess.Board(puzzles_arr[0][contador].get_puzzle_fen())
        correct_move = puzzles_arr[0][contador].get_puzzle_correct_move_str()
        print(board.__str__() + "\n")
        print(correct_move, "\n" + "fen: " + board.fen() + "\n\n")
        pyperclip.copy(board.fen())


customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("dark-blue")

root = customtkinter.CTk()
root.geometry("500x150")
root.title("Blue Pawn - Puzzle Viewer")

frame_1 = customtkinter.CTkFrame(master=root)
frame_1.pack(pady=20, padx=30, fill="both", expand=True)

title_font = customtkinter.CTkFont(size=20, weight="bold")
board_font = customtkinter.CTkFont(size=17)

l_title = customtkinter.CTkLabel(master=frame_1, justify=customtkinter.CENTER)
l_title.configure(text="Blue Pawn - Puzzle Viewer", text_color="#2266FF", font=title_font)
l_title.pack(pady=10, padx=0)

board = chess.Board()

frame_buttons = customtkinter.CTkFrame(master=frame_1, fg_color="transparent")
frame_buttons.pack()

button_left = customtkinter.CTkButton(master=frame_buttons, text="BACK", command=back)
button_left.grid(column=0, row=1, sticky="W")

l_aux_spacing = customtkinter.CTkLabel(master=frame_buttons, width=120, text="")
l_aux_spacing.grid(column=1, row=1, sticky="W")

button_right = customtkinter.CTkButton(master=frame_buttons, text="NEXT", command=next)
button_right.grid(column=2, row=1, sticky="W")

board = chess.Board(puzzles_arr[0][contador].get_puzzle_fen())
correct_move = puzzles_arr[0][contador].get_puzzle_correct_move_str()
print(board.__str__() + "\n")
print(correct_move, "\n" + "fen: " + board.fen() + "\n\n")
pyperclip.copy(board.fen())

root.mainloop()

