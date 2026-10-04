import pygame
import os
import time
import chess

chess.Board

# consts
WIDTH = HEIGHT = 512  # multiple of 8
DIMENSION = 8  # chess board is 8*8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15  # animations fps
IMAGES = {}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_images():
    pieces = ["bB", "bK", "bN", "bP", "bQ", "bR",
              "wB", "wK", "wN", "wP", "wQ", "wR"]
    new_name = ["b", "k", "n", "p", "q", "r",
                "B", "K", "N", "P", "Q", "R"]
    for i in range(len(pieces)):
        img_path = os.path.join(BASE_DIR, "images", f"{pieces[i]}.png")
        IMAGES[new_name[i]] = pygame.transform.scale(pygame.image.load(img_path),
                                                     (SQ_SIZE, SQ_SIZE))


class boardGUI:

    def __init__(self):
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        icon_path = os.path.join(BASE_DIR, 'icon.png')
        if os.path.exists(icon_path):
            icon = pygame.image.load(icon_path)




