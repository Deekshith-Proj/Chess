import chess
import pygame
import sys
import random
import tkinter as tk
from tkinter import simpledialog

# Game Constants
WIDTH, HEIGHT = 512, 512
DIMENSION = 8  # 8x8 board
SQ_SIZE = WIDTH // DIMENSION
MAX_FPS = 15
IMAGES = {}

# Load images once
def load_images():
    pieces = ['P', 'R', 'N', 'B', 'Q', 'K']
    colors = ['w', 'b']
    for color in colors:
        for piece in pieces:
            name = f"{color}{piece}"
            IMAGES[name] = pygame.transform.scale(
                pygame.image.load(f"images/{name}.png"), (SQ_SIZE, SQ_SIZE))

# Evaluation Function
def evaluate_board(board):
    if board.is_checkmate():
        return -9999 if board.turn else 9999
    if board.is_stalemate() or board.is_insufficient_material():
        return 0

    piece_values = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000
    }

    eval = 0
    for piece_type in piece_values:
        eval += len(board.pieces(piece_type, chess.WHITE)) * piece_values[piece_type]
        eval -= len(board.pieces(piece_type, chess.BLACK)) * piece_values[piece_type]

    # Bonus for mobility
    eval += 10 * len(list(board.legal_moves)) if board.turn else -10 * len(list(board.legal_moves))

    # Bonus for checks
    if board.is_check():
        eval += 50 if board.turn else -50

    return eval if board.turn else -eval

# Order moves based on aggression
def order_moves(board):
    def move_score(move):
        score = 0
        if board.is_capture(move):
            score += 1000
        if board.gives_check(move):
            score += 500
        if move.promotion:
            score += 800
        return score
    return sorted(board.legal_moves, key=move_score, reverse=True)

# Minimax with Alpha-Beta
def minimax_alpha_beta(board, depth, alpha, beta, is_maximizing):
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)

    moves = order_moves(board)

    if is_maximizing:
        max_eval = float('-inf')
        for move in moves:
            board.push(move)
            eval = minimax_alpha_beta(board, depth - 1, alpha, beta, False)
            board.pop()
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in moves:
            board.push(move)
            eval = minimax_alpha_beta(board, depth - 1, alpha, beta, True)
            board.pop()
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

# Find Best Move
def find_best_move(board, depth=4):
    best_move = None
    best_eval = float('-inf')
    alpha = float('-inf')
    beta = float('inf')

    for move in order_moves(board):
        board.push(move)
        eval = minimax_alpha_beta(board, depth - 1, alpha, beta, False)
        board.pop()
        if eval > best_eval:
            best_eval = eval
            best_move = move
        alpha = max(alpha, eval)
    return best_move

# Promotion selector
def choose_promotion():
    root = tk.Tk()
    root.withdraw()
    piece = simpledialog.askstring("Promotion", "Promote to (Q, R, B, N):", parent=root)
    root.destroy()
    if piece:
        piece = piece.upper()
        return {
            'Q': chess.QUEEN,
            'R': chess.ROOK,
            'B': chess.BISHOP,
            'N': chess.KNIGHT
        }.get(piece, chess.QUEEN)
    return chess.QUEEN

# Drawing Functions
def draw_board(win, board):
    colors = [pygame.Color("white"), pygame.Color("gray")]
    check_square = None
    if board.is_check():
        check_square = board.king(board.turn)

    for r in range(DIMENSION):
        for c in range(DIMENSION):
            square = chess.square(c, 7 - r)
            color = colors[(r + c) % 2]
            pygame.draw.rect(win, color, pygame.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
            if square == check_square:
                pygame.draw.rect(win, pygame.Color("red"), pygame.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE), 4)

def draw_pieces(win, board):
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            col = chess.square_file(square)
            row = chess.square_rank(square)
            color = 'w' if piece.color == chess.WHITE else 'b'
            name = f"{color}{piece.symbol().upper()}"
            win.blit(IMAGES[name], pygame.Rect(col*SQ_SIZE, (7-row)*SQ_SIZE, SQ_SIZE, SQ_SIZE))

# Main Game Loop
def main():
    pygame.init()
    win = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Chess with AI")
    clock = pygame.time.Clock()
    board = chess.Board()
    load_images()

    selected_square = None
    player_clicks = []

    while not board.is_game_over():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if board.turn == chess.WHITE:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    location = pygame.mouse.get_pos()
                    col = location[0] // SQ_SIZE
                    row = 7 - (location[1] // SQ_SIZE)
                    square = chess.square(col, row)
                    if selected_square is None:
                        if board.piece_at(square) and board.piece_at(square).color == chess.WHITE:
                            selected_square = square
                            player_clicks = [square]
                    else:
                        player_clicks.append(square)
                        move = chess.Move(player_clicks[0], player_clicks[1])
                        # Handle promotions
                        if chess.square_rank(player_clicks[1]) in [0, 7] and board.piece_at(player_clicks[0]).piece_type == chess.PAWN:
                            move.promotion = choose_promotion()
                        if move in board.legal_moves:
                            board.push(move)
                        selected_square = None
                        player_clicks = []

        if not board.turn:
            ai_move = find_best_move(board, depth=4)
            if ai_move:
                board.push(ai_move)

        draw_board(win, board)
        draw_pieces(win, board)
        pygame.display.flip()
        clock.tick(MAX_FPS)

    print("Game Over. Result:", board.result())
    pygame.time.wait(5000)
    pygame.quit()

if __name__ == "__main__":
    main()
