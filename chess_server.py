from flask import Flask, request, jsonify, send_from_directory
import chess
from chess_engine import ChessEngine

app = Flask(__name__)
engine = ChessEngine(depth=3)

@app.route('/')
def index():
    return send_from_directory('.', 'chess_simplest.html')

@app.route('/make_move', methods=['POST'])
def make_move():
    data = request.json
    fen = data.get('fen')
    
    # Create a board from the FEN
    board = chess.Board(fen)
    
    # Find the best move
    best_move, best_score, principal_variation = engine.iterative_deepening(board)
    
    # Return the move in UCI format
    return jsonify({'move': str(best_move)})

if __name__ == '__main__':
    app.run(debug=True, port=5001) 