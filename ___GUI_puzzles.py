import pygame
import os
import chess  # Ensure you have the chess library installed


class ChessGame:
    def __init__(self, flip_board:bool):
        # Initialize Pygame
        pygame.init()

        # Constants for the chess board
        self.BOARD_SIZE = 8
        self.SQUARE_SIZE = 60
        self.WINDOW_SIZE = self.BOARD_SIZE * self.SQUARE_SIZE

        # Colors
        self.WHITE = (255, 255, 255)
        self.ALT_COLOR = (0, 170, 0)
        self.RED = (255, 0, 0, 128)
        self.BLUE = (0, 0, 255, 128)

        # Load piece images
        self.piece_images = {}
        pieces = [
            'bB', 'bK', 'bN', 'bP', 'bQ', 'bR',
            'wB', 'wK', 'wN', 'wP', 'wQ', 'wR'
        ]

        base_dir = os.path.dirname(os.path.abspath(__file__))
        for piece in pieces:
            image_path = os.path.join(base_dir, 'images', f'{piece}.png')
            self.piece_images[piece] = pygame.image.load(image_path)

        # Create the window
        self.screen = pygame.display.set_mode((self.WINDOW_SIZE, self.WINDOW_SIZE))
        pygame.display.set_caption("Chess Board")

        # Variables to track clicks
        self.first_click = None
        self.second_click = None

        # Initialize the chess board and flip board setting
        self.board = chess.Board()
        self.flip_board = not flip_board

    def draw_board(self):
        for row in range(self.BOARD_SIZE):
            for col in range(self.BOARD_SIZE):
                color = self.WHITE if (row + col) % 2 == 0 else self.ALT_COLOR
                pygame.draw.rect(self.screen, color, (col * self.SQUARE_SIZE, row * self.SQUARE_SIZE, self.SQUARE_SIZE, self.SQUARE_SIZE))

                if self.first_click == (row, col):
                    self.highlight_square(row, col, self.RED)
                elif self.second_click == (row, col):
                    self.highlight_square(row, col, self.BLUE)

    def highlight_square(self, row, col, color):
        if not self.flip_board:
            row, col = 7 - row, col
        overlay = pygame.Surface((self.SQUARE_SIZE, self.SQUARE_SIZE), pygame.SRCALPHA)
        overlay.fill(color)
        self.screen.blit(overlay, (col * self.SQUARE_SIZE, row * self.SQUARE_SIZE))

    def draw_pieces(self):
        for i in range(64):
            piece = self.board.piece_at(i)
            if piece is not None:
                # Calculate the row and column
                row, col = divmod(i, 8)

                # Flip rows if self.flip_board is True
                draw_row = 7 - row if self.flip_board else row
                draw_col = 7 - col if self.flip_board else col

                piece_name = piece.symbol()  # Piece name like 'K', 'Q', etc.
                piece_color = 'w' if piece.color == chess.WHITE else 'b'
                piece_image_key = f"{piece_color}{piece_name.upper()}"

                # Draw the piece in the appropriate position
                self.screen.blit(self.piece_images[piece_image_key],
                                 (draw_col * self.SQUARE_SIZE, draw_row * self.SQUARE_SIZE))

    def to_chess_notation(self, row, col):
        # Adjust row and column based on board flip
        actual_row = 7 - row if self.flip_board else row
        actual_col = 7 - col if self.flip_board else col

        file = chr(actual_col + ord('a'))
        rank = str(8 - actual_row)
        return file + rank

    def promote_pawn(self):
        # Prompt user for choice of promotion
        while True:
            choice = input("Promote pawn to (q)ueen, (r)ook, (b)ishop, or (n)ight? ").lower()
            if choice in ['q', 'r', 'b', 'n']:
                return choice  # Return the character directly for the UCI notation
            else:
                print("Invalid choice. Please select again.")

    def update_board(self, from_square, to_square):
        try:
            # Construct the move
            move = chess.Move.from_uci(f"{from_square}{to_square}")

            # Check if the move is a pawn promotion
            if self.board.piece_at(chess.parse_square(from_square)).piece_type == chess.PAWN:
                target_rank = chess.square_rank(chess.parse_square(to_square))
                if target_rank == 0 or target_rank == 7:  # Last rank for white or black
                    promotion_piece = self.promote_pawn()
                    move = chess.Move.from_uci(f"{from_square}{to_square}{promotion_piece}")

            # Check if the move is legal
            if move in self.board.legal_moves:
                self.board.push(move)
            else:
                print("Invalid move")
        except:
            print("Invalid move")

    def run(self):
        running = True
        while running:
            self.screen.fill(self.WHITE)

            self.draw_board()
            self.draw_pieces()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    col = pos[0] // self.SQUARE_SIZE
                    row = pos[1] // self.SQUARE_SIZE

                    # Adjust for board flip in click interpretation
                    if not self.flip_board:
                        row, col = 7 - row, col

                    if not self.first_click:
                        self.first_click = (row, col)
                    elif not self.second_click:
                        self.second_click = (row, col)

                        from_square = self.to_chess_notation(*self.first_click)
                        to_square = self.to_chess_notation(*self.second_click)

                        print(f"{from_square}{to_square}")
                        self.update_board(from_square, to_square)

                        self.first_click = None
                        self.second_click = None

                pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    game = ChessGame(flip_board=True)
    game.run()
