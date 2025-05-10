import { Chess } from 'chess.js'

const chess = new Chess()

while (!chess.isGameOver()) {
  const moves = chess.moves()
  const move = moves[Math.floor(Math.random() * moves.length)]
  chess.move(move)
}
console.log(chess.pgn())

var calculateBestMove = function (game) {

  var newGameMoves = game.ugly_moves();
  var bestMove = null;
  var bestValue = -9999;

  for (var i = 0; i < newGameMoves.length; i++) {
      var newGameMove = newGameMoves[i];
      game.ugly_move(newGameMove);

      //take the negative as AI plays as black
      var boardValue = -evaluateBoard(game.board())
      game.undo();
      if (boardValue > bestValue) {
          bestValue = boardValue;
          bestMove = newGameMove
      }
  }

  return bestMove;

};