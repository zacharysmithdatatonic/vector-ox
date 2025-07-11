"""Board module for Vector-OX game."""

import numpy as np
from typing import Optional, List, Tuple


class Board:
    """Represents a noughts-and-crosses board."""
    
    def __init__(self, size: int = 3):
        self.size = size
        self.board = np.full((size, size), '', dtype=str)
        self.current_player = 'X'
        self.move_history = []
        
    def get_cell(self, row: int, col: int) -> str:
        """Get the value at a specific cell."""
        return self.board[row, col]
    
    def set_cell(self, row: int, col: int, value: str):
        """Set the value at a specific cell."""
        self.board[row, col] = value
        
    def is_valid_move(self, row: int, col: int) -> bool:
        """Check if a move is valid."""
        return (0 <= row < self.size and 
                0 <= col < self.size and 
                self.board[row, col] == '')
    
    def make_move(self, row: int, col: int, player: str):
        """Make a move on the board."""
        if self.is_valid_move(row, col):
            self.board[row, col] = player
            self.move_history.append((row, col, player))
            self.current_player = 'O' if player == 'X' else 'X'
            return True
        return False
    
    def get_available_moves(self) -> List[Tuple[int, int]]:
        """Get all available moves."""
        moves = []
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row, col] == '':
                    moves.append((row, col))
        return moves
    
    def is_full(self) -> bool:
        """Check if the board is full."""
        return len(self.get_available_moves()) == 0
    
    def get_winner(self) -> Optional[str]:
        """Get the winner of the game, if any."""
        # Check rows
        for row in range(self.size):
            if all(self.board[row, col] == self.board[row, 0] != '' 
                   for col in range(self.size)):
                return self.board[row, 0]
        
        # Check columns
        for col in range(self.size):
            if all(self.board[row, col] == self.board[0, col] != '' 
                   for row in range(self.size)):
                return self.board[0, col]
        
        # Check diagonals
        if all(self.board[i, i] == self.board[0, 0] != '' 
               for i in range(self.size)):
            return self.board[0, 0]
        
        if all(self.board[i, self.size - 1 - i] == self.board[0, self.size - 1] != '' 
               for i in range(self.size)):
            return self.board[0, self.size - 1]
        
        return None
    
    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return self.get_winner() is not None or self.is_full()
    
    def get_state_vector(self) -> np.ndarray:
        """Convert board state to a vector representation."""
        # Convert board to numerical representation
        # X = 1, O = -1, Empty = 0
        state = np.zeros((self.size, self.size))
        for row in range(self.size):
            for col in range(self.size):
                if self.board[row, col] == 'X':
                    state[row, col] = 1
                elif self.board[row, col] == 'O':
                    state[row, col] = -1
        return state.flatten()
    
    def get_state_string(self) -> str:
        """Convert board state to a string representation."""
        state = []
        for row in range(self.size):
            for col in range(self.size):
                cell = self.board[row, col]
                if cell == '':
                    state.append('.')
                else:
                    state.append(cell)
        return ''.join(state)
    
    def copy(self) -> 'Board':
        """Create a copy of the board."""
        new_board = Board(self.size)
        new_board.board = self.board.copy()
        new_board.current_player = self.current_player
        new_board.move_history = self.move_history.copy()
        return new_board
    
    def reset(self):
        """Reset the board to initial state."""
        self.board = np.full((self.size, self.size), '', dtype=str)
        self.current_player = 'X'
        self.move_history = []
    
    def __str__(self) -> str:
        """String representation of the board."""
        result = []
        for row in range(self.size):
            row_str = []
            for col in range(self.size):
                cell = self.board[row, col]
                if cell == '':
                    row_str.append('.')
                else:
                    row_str.append(cell)
            result.append(' '.join(row_str))
        return '\n'.join(result) 