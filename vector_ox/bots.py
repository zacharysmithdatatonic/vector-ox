"""Bot implementations for Vector-OX game."""

import random
import numpy as np
from typing import Tuple, List, Optional
import chromadb

from .board import Board


class BaseBot:
    """Base class for all bots."""
    
    def get_move(self, board: Board) -> Tuple[int, int]:
        """Get the next move for the given board state."""
        raise NotImplementedError


class RandomBot(BaseBot):
    """Random bot that makes random valid moves."""
    
    def get_move(self, board: Board) -> Tuple[int, int]:
        """Get a random valid move."""
        available_moves = board.get_available_moves()
        return random.choice(available_moves)


class AlgorithmBot(BaseBot):
    """Algorithm bot using minimax with alpha-beta pruning."""
    
    def get_move(self, board: Board) -> Tuple[int, int]:
        """Get the best move using minimax algorithm."""
        best_score = float('-inf')
        best_move = None
        alpha = float('-inf')
        beta = float('inf')
        
        for move in board.get_available_moves():
            row, col = move
            board.make_move(row, col, board.current_player)
            score = self._minimax(board, 0, False, alpha, beta)
            board.board[row, col] = ''  # Undo move
            board.current_player = 'X' if board.current_player == 'O' else 'O'
            
            if score > best_score:
                best_score = score
                best_move = move
            
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break
        
        return best_move
    
    def _minimax(self, board: Board, depth: int, is_maximizing: bool, 
                  alpha: float, beta: float) -> float:
        """Minimax algorithm with alpha-beta pruning."""
        if board.is_game_over():
            winner = board.get_winner()
            if winner == board.current_player:
                return 10 - depth
            elif winner is not None:
                return depth - 10
            else:
                return 0
        
        if is_maximizing:
            max_eval = float('-inf')
            for move in board.get_available_moves():
                row, col = move
                board.make_move(row, col, board.current_player)
                eval_score = self._minimax(board, depth + 1, False, alpha, beta)
                board.board[row, col] = ''  # Undo move
                board.current_player = 'X' if board.current_player == 'O' else 'O'
                
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in board.get_available_moves():
                row, col = move
                board.make_move(row, col, board.current_player)
                eval_score = self._minimax(board, depth + 1, True, alpha, beta)
                board.board[row, col] = ''  # Undo move
                board.current_player = 'X' if board.current_player == 'O' else 'O'
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval


class VectorBot(BaseBot):
    """Vector database bot that uses similarity search."""
    
    def __init__(self, collection_name: str = "vector_ox_moves"):
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize the vector database connection."""
        try:
            self.client = chromadb.PersistentClient(path="./vector_db")
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(self.collection_name)
            except:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Vector-OX game moves"}
                )
        except Exception as e:
            print(f"Warning: Could not initialize vector database: {e}")
            self.client = None
            self.collection = None
    
    def get_move(self, board: Board) -> Tuple[int, int]:
        """Get move using vector database similarity search."""
        if self.collection is None:
            # Fallback to random if vector DB is not available
            return RandomBot().get_move(board)
        
        try:
            # Get current board state
            state_vector = board.get_state_vector()
            state_string = board.get_state_string()
            
            # Search for similar states
            results = self.collection.query(
                query_embeddings=[state_vector.tolist()],
                n_results=5
            )
            
            if results['documents'] and len(results['documents'][0]) > 0:
                # Find the best move from similar states
                best_move = self._find_best_move_from_results(board, results)
                if best_move:
                    return best_move
            
            # Fallback to random if no good matches found
            return RandomBot().get_move(board)
            
        except Exception as e:
            print(f"Warning: Vector search failed: {e}")
            return RandomBot().get_move(board)
    
    def _find_best_move_from_results(self, board: Board, results: dict) -> Optional[Tuple[int, int]]:
        """Find the best move from vector search results."""
        available_moves = board.get_available_moves()
        if not available_moves:
            return None
        
        # Count moves from similar states
        move_counts = {}
        for i, doc in enumerate(results['documents'][0]):
            if doc and '|' in doc:
                try:
                    state_str, move_str = doc.split('|', 1)
                    row, col = map(int, move_str.split(','))
                    move = (row, col)
                    if move in available_moves:
                        move_counts[move] = move_counts.get(move, 0) + 1
                except:
                    continue
        
        if move_counts:
            # Return the most common move
            return max(move_counts.items(), key=lambda x: x[1])[0]
        
        return None
    
    def add_game_data(self, state_string: str, move: Tuple[int, int], outcome: str):
        """Add game data to the vector database."""
        if self.collection is None:
            return
        
        try:
            # Create state vector
            state_vector = self._string_to_vector(state_string)
            
            # Create document
            doc_id = f"{state_string}_{move[0]}_{move[1]}"
            document = f"{state_string}|{move[0]},{move[1]}"
            
            self.collection.add(
                documents=[document],
                embeddings=[state_vector.tolist()],
                ids=[doc_id],
                metadatas=[{"outcome": outcome}]
            )
        except Exception as e:
            print(f"Warning: Could not add data to vector database: {e}")
    
    def _string_to_vector(self, state_string: str) -> np.ndarray:
        """Convert state string to vector representation."""
        size = int(len(state_string) ** 0.5)
        vector = np.zeros(size * size)
        
        for i, char in enumerate(state_string):
            if char == 'X':
                vector[i] = 1
            elif char == 'O':
                vector[i] = -1
            # Empty cells remain 0
        
        return vector 