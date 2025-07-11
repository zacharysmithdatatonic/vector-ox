"""Data generator for Vector-OX training data."""

import random
import click
from rich.console import Console
from rich.progress import track

from .board import Board
from .bots import RandomBot, AlgorithmBot


class DataGenerator:
    """Generate training data for the vector database."""
    
    def __init__(self, board_size: int = 3):
        self.board_size = board_size
        self.console = Console()
        self.random_bot = RandomBot()
        self.algorithm_bot = AlgorithmBot()
        
    def generate_games(self, num_games: int = 1000) -> list:
        """Generate a specified number of games."""
        games_data = []
        
        self.console.print(f"Generating {num_games} games...")
        
        for _ in track(range(num_games), description="Generating games"):
            game_data = self._play_single_game()
            games_data.extend(game_data)
        
        self.console.print(f"Generated {len(games_data)} board states")
        return games_data
    
    def _play_single_game(self) -> list:
        """Play a single game and return all board states."""
        board = Board(self.board_size)
        game_states = []
        
        # Randomly choose bot types for both players
        bot1_type = random.choice(['random', 'algorithm'])
        bot2_type = random.choice(['random', 'algorithm'])
        
        bot1 = self.random_bot if bot1_type == 'random' else self.algorithm_bot
        bot2 = self.random_bot if bot2_type == 'random' else self.algorithm_bot
        
        while not board.is_game_over():
            # Record current state
            state_string = board.get_state_string()
            current_player = board.current_player
            
            # Get move
            if current_player == 'X':
                move = bot1.get_move(board)
            else:
                move = bot2.get_move(board)
            
            # Record the move
            game_states.append({
                'state': state_string,
                'move': move,
                'player': current_player,
                'board_size': self.board_size
            })
            
            # Make the move
            board.make_move(move[0], move[1], current_player)
        
        # Determine outcome
        winner = board.get_winner()
        outcome = winner if winner else 'tie'
        
        # Add outcome to all states
        for state in game_states:
            state['outcome'] = outcome
        
        return game_states
    
    def save_to_file(self, games_data: list, filename: str = "training_data.txt"):
        """Save generated data to a file."""
        with open(filename, 'w') as f:
            for state in games_data:
                line = f"{state['state']}|{state['move'][0]},{state['move'][1]}|{state['outcome']}\n"
                f.write(line)
        
        self.console.print(f"Saved {len(games_data)} states to {filename}")


@click.command()
@click.option('--board-size', default=3, help='Board size (default: 3)')
@click.option('--num-games', default=1000, help='Number of games to generate (default: 1000)')
@click.option('--output-file', default='training_data.txt', help='Output file name (default: training_data.txt)')
def main(board_size: int, num_games: int, output_file: str):
    """Generate training data for the vector database."""
    generator = DataGenerator(board_size)
    games_data = generator.generate_games(num_games)
    generator.save_to_file(games_data, output_file)


if __name__ == "__main__":
    main() 