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

def load_images():
    pieces = ["bB", "bK", "bN", "bP", "bQ", "bR",
              "wB", "wK", "wN", "wP", "wQ", "wR"]
    new_name = ["b", "k", "n", "p", "q", "r",
                "B", "K", "N", "P", "Q", "R"]
    for i in range(len(pieces)):
        IMAGES[new_name[i]] = pygame.transform.scale(pygame.image.load(r"images\\" + pieces[i] + ".png"),
                                                     (SQ_SIZE, SQ_SIZE))


class boardGUI:

    def __init__(self):
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        icon = pygame.image.load('icon.png')




