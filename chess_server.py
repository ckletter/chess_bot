from flask import Flask, request, jsonify, send_from_directory
import chess
import chess.polyglot
from chess_engine import ChessEngine

app = Flask(__name__)
engine = ChessEngine()
reader = chess.polyglot.open_reader("Perfect2023.bin")  # Load the opening book

@app.route('/')
def index():
    return send_from_directory('.', 'chess_simplest.html')

@app.route('/make_move', methods=['POST'])
def make_move():
    data = request.json
    fen = data.get('fen')

    # Create a board from the FEN
    board = chess.Board(fen)

    # Check for a book move
    book_move = None
    for entry in reader.find_all(board):
        # Take the first available book move
        book_move = entry.move
        break

    if book_move:
        move = book_move
    else:
        # If no book move, use the engine's best move
        best_move, best_score, principal_variation = engine.iterative_deepening(board)
        move = best_move

    # Return the move in UCI format
    return jsonify({'move': str(move)})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
