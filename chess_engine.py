import chess
import chess.polyglot
import random
import time

class ChessEngine:
    # Piece-square tables for each piece
    PAWN_TABLE = [
        0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5,  5, 10, 25, 25, 10,  5,  5,
        0,  0,  0, 20, 20,  0,  0,  0,
        5, -5,-10,  0,  0,-10, -5,  5,
        5, 10, 10,-20,-20, 10, 10,  5,
        0,  0,  0,  0,  0,  0,  0,  0
    ]

    KNIGHT_TABLE = [
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30
    ,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ]
    
    BISHOP_TABLE = [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20
    ]
    
    ROOK_TABLE = [
        0,  0,  0,  0,  0,  0,  0,  0,
        5, 10, 10, 10, 10, 10, 10,  5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        0,  0,  0,  5,  5,  0,  0,  0
    ]
    
    QUEEN_TABLE = [
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
        -5,  0,  5,  5,  5,  5,  0, -5,
        0,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20
    ]
    
    KING_TABLE = [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
        20, 20,  0,  0,  0,  0, 20, 20,
        20, 30, 10,  0,  0, 10, 30, 20
    ]
    # King tables for endgame
    KING_ENDGAME_TABLE = [
        -50,-40,-30,-20,-20,-30,-40,-50,
        -30,-20,-10,  0,  0,-10,-20,-30,
        -30,-10, 20, 30, 30, 20,-10,-30,
        -30,-10, 30, 40, 40, 30,-10,-30,
        -30,-10, 30, 40, 40, 30,-10,-30,
        -30,-10, 20, 30, 30, 20,-10,-30,
        -30,-30,  0,  0,  0,  0,-30,-30,
        -50,-30,-30,-30,-30,-30,-30,-50
    ]


    # Piece values for material counting
    PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        # Bishops slightly better than knights :)
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000
    }

    # Constructor, resetting global variables like pv table and transposition tables
    def __init__(self):
        self.MAX_DEPTH = 5  # Maximum search depth
        self.pv_table = {}  # Principal Variation table
        self.nodes_searched = 0  # Counter for total nodes searched
        self.number_of_prunes = 0 # Counter for number of prunes
        self.zobrist_hash = self.init_zobrist_hash()
        self.transposition_table = {}
        self.tt_hits = 0
    
    def evaluate_position(self, board):
        # Simple material counting evaluation
        if board.is_checkmate():
            # If checkmate, return a large value
            return -10000 if board.turn else 10000

        # Check for draw
        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        # Check if endgame (two queens off the board OR less than 12 pieces total on board)
        is_endgame = len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK)) == 0 or (len(board.piece_map()) <= 12)
        # Count material and position
        score = 0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                # Material value
                value = self.PIECE_VALUES[piece.piece_type]
                
                # Position value based on piece-square tables
                if piece.color == chess.WHITE:
                    score += value
                    # Add positional bonus
                    if piece.piece_type == chess.PAWN:
                        score += self.PAWN_TABLE[square]
                    elif piece.piece_type == chess.KNIGHT:
                        score += self.KNIGHT_TABLE[square]
                    elif piece.piece_type == chess.BISHOP:
                        score += self.BISHOP_TABLE[square]
                    elif piece.piece_type == chess.ROOK:
                        score += self.ROOK_TABLE[square]
                    elif piece.piece_type == chess.QUEEN:
                        score += self.QUEEN_TABLE[square]
                    elif piece.piece_type == chess.KING:
                        if is_endgame:
                            score += self.KING_ENDGAME_TABLE[square]
                        else:
                            score += self.KING_TABLE[square]
                else:
                    score -= value
                    # Subtract positional bonus (flip board for black pieces)
                    flipped_square = chess.square_mirror(square)
                    if piece.piece_type == chess.PAWN:
                        score -= self.PAWN_TABLE[flipped_square]
                    elif piece.piece_type == chess.KNIGHT:
                        score -= self.KNIGHT_TABLE[flipped_square]
                    elif piece.piece_type == chess.BISHOP:
                        score -= self.BISHOP_TABLE[flipped_square]
                    elif piece.piece_type == chess.ROOK:
                        score -= self.ROOK_TABLE[flipped_square]
                    elif piece.piece_type == chess.QUEEN:
                        score -= self.QUEEN_TABLE[flipped_square]
                    elif piece.piece_type == chess.KING:
                        if is_endgame:
                            score -= self.KING_ENDGAME_TABLE[flipped_square]
                    else:
                        score -= self.KING_TABLE[flipped_square]

        # White mobility
        board.turn = chess.WHITE
        white_mobility = len(list(board.legal_moves))

        # Count black's mobility
        board.turn = chess.BLACK
        black_mobility = len(list(board.legal_moves))


        # Factor in piece mobility into score with a small weight
        score += (white_mobility - black_mobility) * 2

        # Add a bishop pair bonus
        if len(board.pieces(chess.BISHOP, chess.WHITE)) >= 2:
            score += 50
        if len(board.pieces(chess.BISHOP, chess.BLACK)) >= 2:
            score -= 50
        return score

    """Negamax algorithm (minimax algorithm but taking the negative version of opponent's score)
    DFS with alpha-beta pruning and time limit, max depth"""
    def negamax(self, board, current_depth, target_depth, start_time, time_limit, alpha=-float('inf'), beta=float('inf'), color=1):
        # Calculate position hash at the start
        position_hash = self.hash_position(board)

        # Look up position in transposition table
        if position_hash in self.transposition_table:
            tt_entry = self.transposition_table[position_hash]
            # Only use entry if it searched at least as deep as we need to now
            remaining_depth = target_depth - current_depth
            if tt_entry['depth'] >= remaining_depth:
                self.tt_hits += 1
                # Return stored evaluation and PV line
                return tt_entry['score'], tt_entry['pv']
        # If run out of time, return none for score
        if time.time() - start_time > time_limit:
            return None, []
        
        # Base case, if we've reached end of search or game is over
        if current_depth == target_depth or board.is_game_over():
            self.nodes_searched += 1
            evaluation = self.evaluate_position(board)
            # Store leaf node in transposition table
            self.transposition_table[position_hash] = {
                'score': evaluation,
                # Store remaining depth
                'depth': target_depth - current_depth,
                'pv': []
            }
            return color * self.evaluate_position(board), []


            
        max_score = -float('inf')
        best_move = None
        pv_line = []

        # # Track a "best so far" move even if we time out
        # current_best_move = None
        # current_best_score = -float('inf')
        # current_best_line = []
        
        # Get ordered moves
        moves = self.order_moves(board, current_depth)
        # moves = list(board.legal_moves)
        
        for move in moves:
            board.push(move)
            # If timeout occurred
            # if time.time() - start_time > time_limit:
            #     board.pop()
            #     # If we have at least one move evaluated at this depth, return current best move seen
            #     if current_best_move:
            #         return current_best_score, [current_best_move] + current_best_line
            #     # If no move evaluated at depth, return current best move
            #     return None, []

            # Get the score and line from the recursive call, negate alpha and beta and switch
            # Because we are using negamax, perspective of best and worst outcome must be flipped
            score, line = self.negamax(board, current_depth + 1, target_depth, start_time, time_limit, -beta, -alpha, -color)
            # If timeout occurred
            if score is None:
                return None, []
            # Negate opponent's score by negamax algorithm
            score = -score
            board.pop()

            # If timeout occurred in deeper recursive call
            # if score is None:
            #     # If we have at least one move evaluated at this depth, return it
            #     if current_best_move:
            #         return current_best_score, [current_best_move] + current_best_line
            #     # If no move evaluated at depth, return current best move
            #     return None, []

            # Update current best at this depth
            # if score > current_best_score:
            #     current_best_score = score
            #     current_best_move = move
            #     current_best_line = line
            # Update best score seen
            if score > max_score:
                max_score = score
                best_move = move
                pv_line = [move] + line
            
            alpha = max(alpha, score)
            # Prune if beta (worst you can do) is less than alpha (best you can do)
            if alpha >= beta:
                self.number_of_prunes += 1
                break

        # Store result in transposition table
        self.transposition_table[position_hash] = {
            'score': max_score,
            # Store remaining depth
            'depth': target_depth - current_depth,
            'pv': pv_line
        }
        return max_score, pv_line

    """Performs iterative deepening, calling negamax algorithm with a time limit of 3.5 seconds
    Point of iterative deepening is to improve move ordering at each iterative layer with 'pv'"""
    def iterative_deepening(self, board, time_limit=3.5):
        start_time = time.time()
        best_move = None
        best_score = -float('inf')
        principal_variation = []

        # Clear the PV table for new search
        self.pv_table.clear()
        self.transposition_table.clear()
        
        for depth in range(1, self.MAX_DEPTH + 1):
        # for depth in range(1, 6):
            # Reset node counter for this depth
            self.nodes_searched = 0
            self.number_of_prunes = 0
            depth_start_time = time.time()
            
            # Search at current depth, setting color to 1 if white, -1 if black
            score, pv = self.negamax(board, 0, depth, start_time, time_limit, -float('inf'), float('inf'), 1 if board.turn else -1)

            # If timeout occurred while performing DFS, return the best move from the previous iteration
            if score is None:
                return best_move, best_score, principal_variation
            # Update new best score
            best_score = score
            # Update Principal Variation at each depth index with new "best" Principal Variation sequence
            for current_depth in range(1, depth + 1):
                self.pv_table[current_depth] = pv[0:current_depth]

            # Calculate time taken for this depth
            depth_time = time.time() - depth_start_time
            
            # Print statistics for this depth
            print(f"Depth {depth}: {self.nodes_searched} nodes in {depth_time:.2f}s, Prunes: {self.number_of_prunes} PV: ", " ".join(str(move) for move in principal_variation))
            
            # If we have a principal variation, update our best move and principal variation
            if pv:  
                best_move = pv[0]
                principal_variation = pv
                    
            # Check if we're out of time
            if time.time() - start_time > time_limit:
                print(f"Time limit reached after depth {depth}")
                break
        return best_move, best_score, principal_variation
    """
        Orders moves, putting the PV move first
    """
    def order_moves(self, board, depth):
        moves = list(board.legal_moves)
        ordered_moves = []
        # Calculate current position hash
        position_hash = self.hash_position(board)

        # Check if we have a transposition table hit with best move
        tt_move = None
        if position_hash in self.transposition_table:
            # Get the transposition table entry if we have a hit
            tt_entry = self.transposition_table[position_hash]
            if tt_entry['pv'] and tt_entry['pv'][0] in moves:
                tt_move = tt_entry['pv'][0]

        # First try transposition table move if available
        if tt_move and tt_move in moves:
            ordered_moves.append(tt_move)
            moves.remove(tt_move)
        #
        # # Get PV moves for this depth
        # if depth in self.pv_table:
        #     pv_moves = self.pv_table[depth]
        #     # Add all PV moves that are still legal
        #     for pv_move in pv_moves:
        #         if pv_move in moves:
        #             ordered_moves.append(pv_move)
        #             moves.remove(pv_move)
        #
        # Add remaining legal moves
        ordered_moves.extend(moves)
        return ordered_moves


    # def evaluate_capture_move(self,board, move):
    #     # Get the attacker piece (the piece that is making the move)
    #     attacker_piece = board.piece_at(move.from_square)
    #
    #     # Get the captured piece (the piece being captured by the move)
    #     captured_piece = board.piece_at(move.to_square)
    #
    #     captured_value = self.PIECE_VALUES.get(captured_piece.piece_type, 0)  # Value of the captured piece
    #     attacker_value = self.PIECE_VALUES.get(attacker_piece.piece_type, 0)  # Value of the attacking piece
    #
    #     # Calculate the score based on captured piece and attacker piece values
    #     score = 100 + captured_value - attacker_value
    #     return score
    """
    Initializes position hash with 64 bit random numbers for each piece on each square, random numbers for castling, 
    en passant files, side to move"""
    def init_zobrist_hash(self):
        hash = 0
        # Create array of size 64x2x7
        piece_keys = [[[0 for _ in range(64)] for _ in range(2)] for _ in range(7)]
        # Fill with random zobrist 64-bit values
        for piece_type in range(7):
            for color in range(2):
                for square in range(64):
                    piece_keys[piece_type][color][square] = random.getrandbits(64)

        # Random number for side to move (when white is to move)
        side_to_move = random.getrandbits(64)

        # Random numbers for castling rights
        castling_keys = [random.getrandbits(64) for _ in range(4)]

        # Random numbers for each en passant file
        en_passant_keys = [random.getrandbits(64) for _ in range(8)]

        # Returns dictionary with each key made
        return {
            'piece_keys': piece_keys,
            'side_to_move': side_to_move,
            'castling_keys': castling_keys,
            'en_passant_keys': en_passant_keys
        }
    """
    Hashes the current position using the zobrist hash values in the initialization function
    XOR operations (which are commutative and associative) to find the exact zobrist hash for current position"""
    def hash_position(self, board):
        hash = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            # Gets the number associated with the piece:
            # 1=pawn, 2=knight, 3=bishop, 4=rook, 5=queen, 6=king
            if piece:
                piece_type = piece.piece_type
                if piece.color == chess.WHITE:
                    piece_color = 0
                else:
                    piece_color = 1

                hash ^= self.zobrist_hash['piece_keys'][piece_type][piece_color][square]
        # Also XOR the hash for side to move if it's whites turn
        if board.turn == chess.WHITE:
            hash ^= self.zobrist_hash['side_to_move']

        # Hash all castling rights
        # White kingside
        if board.has_kingside_castling_rights(chess.WHITE):
            hash ^= self.zobrist_hash['castling_keys'][0]
        # White queenside
        if board.has_queenside_castling_rights(chess.WHITE):
            hash ^= self.zobrist_hash['castling_keys'][1]
        # Black kingside
        if board.has_kingside_castling_rights(chess.BLACK):
            hash ^= self.zobrist_hash['castling_keys'][2]
        # Black queenside
        if board.has_queenside_castling_rights(chess.BLACK):
            hash ^= self.zobrist_hash['castling_keys'][3]

        # If necessary, hash en passant square
        if board.ep_square is not None:
            file = chess.square_file(board.ep_square)  # Get the file (0-7) of the en passant square
            hash ^= self.zobrist_hash['en_passant_keys'][file]
        return hash

    # def score_move_heuristically(self, board, move):
    #     score = 0
    #     if board.is_capture(move):
    #         score += self.evaluate_capture_move(board, move)
    #     if board.is_check(move):
    #         score += 50
    #     if move.is_promotion(move):
    #         score += 80
    #     return score
    """
    Main method of chess engine, handles both user and computer moves
    """
    def play_game(self):
        # Create a new board
        board = chess.Board()
        print("\nStarting position:")
        print(board)
        moves_played = 0
        # Flag to track if we've deviated from the book
        book_deviation = False

        # Load the opening book
        reader = chess.polyglot.open_reader("Perfect2023.bin")

        # Main game loop
        while not board.is_game_over():
            moves_played += 1
            # Every 20 moves, clear table
            self.transposition_table = {}

            # Check if it's the user's turn (white)
            if board.turn == chess.WHITE:
                # Get user input
                user_input = input("\nYour move (or command): ").strip().lower()

                # Try to make the user's move
                try:
                    move = chess.Move.from_uci(user_input)
                    if move in board.legal_moves:
                        board.push(move)
                        print("\nYou played:", move)
                        print(board)
                    else:
                        print("Illegal move! Try again.")
                except ValueError:
                    print("Invalid move format! Use format like 'e2e4'")
            else:
                # Computer's turn (black)
                print("\nComputer is thinking...")

                if not book_deviation:
                    # Check if there's a book move available
                    book_move = None
                    for entry in reader.find_all(board):
                        book_move = entry.move
                        break  # Take the first available book move

                    if book_move:
                        board.push(book_move)
                        print("Computer played book move:", book_move)
                        print(board)
                    else:
                        # Mark that we deviated from book
                        book_deviation = True
                        best_move, best_score, principal_variation = engine.iterative_deepening(board)
                        board.push(best_move)
                        print("Computer played:", best_move)
                        print("Principal variation:", " ".join(str(move) for move in principal_variation))
                        print(board)

                # Fallback to engine after deviation
                else:
                    # Fallback to engine after deviation
                    best_move, best_score, principal_variation = engine.iterative_deepening(board)
                    board.push(best_move)
                    print("Computer played:", best_move)
                    print("Principal variation:", " ".join(str(move) for move in principal_variation))
                    print(board)


    # Game over
        if board.is_game_over():
            result = board.outcome().result()
            if result == "1-0":
                print("\nGame over! You won!")
            elif result == "0-1":
                print("\nGame over! Computer won!")
            else:
                print("\nGame over! It's a draw!")

            print("Final position:")
            print(board)
            print("PGN:", board.variation_san(board.move_stack))

if __name__ == "__main__":
    engine = ChessEngine()
    engine.play_game()