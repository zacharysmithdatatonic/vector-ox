"""Tests for the board module."""

import pytest
import numpy as np

from vector_ox.board import Board


class TestBoard:
    """Test cases for the Board class."""
    
    def test_board_initialization(self):
        """Test board initialization."""
        board = Board(3)
        assert board.size == 3
        assert board.current_player == 'X'
        assert len(board.get_available_moves()) == 9
    
    def test_make_valid_move(self):
        """Test making a valid move."""
        board = Board(3)
        assert board.make_move(0, 0, 'X')
        assert board.get_cell(0, 0) == 'X'
        assert board.current_player == 'O'
    
    def test_make_invalid_move(self):
        """Test making an invalid move."""
        board = Board(3)
        board.make_move(0, 0, 'X')
        assert not board.make_move(0, 0, 'O')  # Already occupied
    
    def test_get_winner_horizontal(self):
        """Test horizontal win condition."""
        board = Board(3)
        board.make_move(0, 0, 'X')
        board.make_move(1, 0, 'O')
        board.make_move(0, 1, 'X')
        board.make_move(1, 1, 'O')
        board.make_move(0, 2, 'X')
        assert board.get_winner() == 'X'
    
    def test_get_winner_vertical(self):
        """Test vertical win condition."""
        board = Board(3)
        board.make_move(0, 0, 'X')
        board.make_move(0, 1, 'O')
        board.make_move(1, 0, 'X')
        board.make_move(1, 1, 'O')
        board.make_move(2, 0, 'X')
        assert board.get_winner() == 'X'
    
    def test_get_winner_diagonal(self):
        """Test diagonal win condition."""
        board = Board(3)
        board.make_move(0, 0, 'X')
        board.make_move(0, 1, 'O')
        board.make_move(1, 1, 'X')
        board.make_move(1, 0, 'O')
        board.make_move(2, 2, 'X')
        assert board.get_winner() == 'X'
    
    def test_is_game_over(self):
        """Test game over conditions."""
        board = Board(3)
        assert not board.is_game_over()
        
        # Fill the board
        for i in range(3):
            for j in range(3):
                board.make_move(i, j, 'X')
        
        assert board.is_game_over()
    
    def test_get_state_vector(self):
        """Test state vector conversion."""
        board = Board(3)
        board.make_move(0, 0, 'X')
        board.make_move(1, 1, 'O')
        
        vector = board.get_state_vector()
        expected = np.array([1, 0, 0, 0, -1, 0, 0, 0, 0])
        np.testing.assert_array_equal(vector, expected)
    
    def test_get_state_string(self):
        """Test state string conversion."""
        board = Board(3)
        board.make_move(0, 0, 'X')
        board.make_move(1, 1, 'O')
        
        state_string = board.get_state_string()
        assert state_string == "X..O....."
    
    def test_copy(self):
        """Test board copying."""
        board = Board(3)
        board.make_move(0, 0, 'X')
        
        copied_board = board.copy()
        assert copied_board.size == board.size
        assert copied_board.get_cell(0, 0) == board.get_cell(0, 0)
        
        # Ensure they are independent
        copied_board.make_move(1, 1, 'O')
        assert board.get_cell(1, 1) == ''
        assert copied_board.get_cell(1, 1) == 'O' 