"""Bot testing module for Vector-OX."""

import random
import click
from rich.console import Console
from rich.progress import track
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from typing import Dict, List, Tuple
import statistics

from .board import Board
from .bots import RandomBot, AlgorithmBot, VectorBot


class BotTester:
    """Test bots against each other and track performance."""
    
    def __init__(self, board_size: int = 3, games_per_matchup: int = 100):
        self.board_size = board_size
        self.games_per_matchup = games_per_matchup
        self.console = Console()
        self.bots = {
            'random': RandomBot(),
            'algorithm': AlgorithmBot(),
            'vector': VectorBot()
        }
        self.results = {}
        
    def run_tournament(self) -> Dict:
        """Run a complete tournament between all bots."""
        self.console.print(Panel(
            f"[bold green]Vector-OX Bot Tournament[/bold green]\n"
            f"Board Size: {self.board_size}x{self.board_size}\n"
            f"Games per matchup: {self.games_per_matchup}",
            style="green"
        ))
        
        bot_names = list(self.bots.keys())
        matchups = []
        
        # Generate all possible matchups
        for i, bot1 in enumerate(bot_names):
            for j, bot2 in enumerate(bot_names):
                if i != j:  # Don't test bot against itself
                    matchups.append((bot1, bot2))
        
        self.console.print(f"\n[bold]Running {len(matchups)} matchups...[/bold]")
        
        for bot1_name, bot2_name in track(matchups, description="Testing matchups"):
            self.console.print(f"\n[dim]Testing {bot1_name.title()} vs {bot2_name.title()}...[/dim]")
            self._test_matchup(bot1_name, bot2_name)
        
        return self.results
    
    def _test_matchup(self, bot1_name: str, bot2_name: str):
        """Test a specific matchup between two bots."""
        bot1 = self.bots[bot1_name]
        bot2 = self.bots[bot2_name]
        
        bot1_wins = 0
        bot2_wins = 0
        ties = 0
        
        for _ in range(self.games_per_matchup):
            result = self._play_single_game(bot1, bot2, bot1_name, bot2_name)
            if result == bot1_name:
                bot1_wins += 1
            elif result == bot2_name:
                bot2_wins += 1
            else:
                ties += 1
        
        # Store results
        matchup_key = f"{bot1_name}_vs_{bot2_name}"
        self.results[matchup_key] = {
            'bot1': bot1_name,
            'bot2': bot2_name,
            'bot1_wins': bot1_wins,
            'bot2_wins': bot2_wins,
            'ties': ties,
            'total_games': self.games_per_matchup
        }
        
        # Also store reverse matchup for easier analysis
        reverse_key = f"{bot2_name}_vs_{bot1_name}"
        self.results[reverse_key] = {
            'bot1': bot2_name,
            'bot2': bot1_name,
            'bot1_wins': bot2_wins,
            'bot2_wins': bot1_wins,
            'ties': ties,
            'total_games': self.games_per_matchup
        }
    
    def _play_single_game(self, bot1, bot2, bot1_name: str, bot2_name: str) -> str:
        """Play a single game between two bots."""
        board = Board(self.board_size)
        
        while not board.is_game_over():
            if board.current_player == 'X':
                move = bot1.get_move(board)
                board.make_move(move[0], move[1], 'X')
            else:
                move = bot2.get_move(board)
                board.make_move(move[0], move[1], 'O')
        
        winner = board.get_winner()
        if winner == 'X':
            return bot1_name
        elif winner == 'O':
            return bot2_name
        else:
            return 'tie'
    
    def calculate_bot_stats(self) -> Dict:
        """Calculate overall statistics for each bot."""
        bot_stats = {}
        
        for bot_name in self.bots.keys():
            total_wins = 0
            total_losses = 0
            total_ties = 0
            total_games = 0
            
            # Count all games for this bot
            for matchup_key, result in self.results.items():
                if result['bot1'] == bot_name:
                    total_wins += result['bot1_wins']
                    total_losses += result['bot2_wins']
                    total_ties += result['ties']
                    total_games += result['total_games']
                elif result['bot2'] == bot_name:
                    total_wins += result['bot2_wins']
                    total_losses += result['bot1_wins']
                    total_ties += result['ties']
                    total_games += result['total_games']
            
            if total_games > 0:
                win_rate = total_wins / total_games
                loss_rate = total_losses / total_games
                tie_rate = total_ties / total_games
            else:
                win_rate = loss_rate = tie_rate = 0
            
            bot_stats[bot_name] = {
                'total_games': total_games,
                'wins': total_wins,
                'losses': total_losses,
                'ties': total_ties,
                'win_rate': win_rate,
                'loss_rate': loss_rate,
                'tie_rate': tie_rate
            }
        
        return bot_stats
    
    def display_results_table(self, bot_stats: Dict):
        """Display results in a table format."""
        table = Table(title="Bot Performance Summary")
        table.add_column("Bot", style="cyan", no_wrap=True)
        table.add_column("Games", justify="right", style="green")
        table.add_column("Wins", justify="right", style="green")
        table.add_column("Losses", justify="right", style="red")
        table.add_column("Ties", justify="right", style="yellow")
        table.add_column("Win Rate", justify="right", style="bold")
        
        for bot_name, stats in bot_stats.items():
            win_rate_pct = f"{stats['win_rate']:.1%}"
            table.add_row(
                bot_name.title(),
                str(stats['total_games']),
                str(stats['wins']),
                str(stats['losses']),
                str(stats['ties']),
                win_rate_pct
            )
        
        self.console.print(table)
    
    def display_ascii_charts(self, bot_stats: Dict):
        """Display ASCII bar charts showing bot performance."""
        self.console.print("\n[bold]Win Rate Comparison[/bold]")
        
        # Find the highest win rate for scaling
        max_win_rate = max(stats['win_rate'] for stats in bot_stats.values())
        chart_width = 50
        
        for bot_name, stats in sorted(bot_stats.items(), key=lambda x: x[1]['win_rate'], reverse=True):
            win_rate = stats['win_rate']
            bar_length = int((win_rate / max_win_rate) * chart_width) if max_win_rate > 0 else 0
            
            # Create the bar
            bar = "█" * bar_length + "░" * (chart_width - bar_length)
            
            # Color code based on performance
            if win_rate >= 0.6:
                color = "green"
            elif win_rate >= 0.4:
                color = "yellow"
            else:
                color = "red"
            
            self.console.print(f"{bot_name.title():<10} {bar} {win_rate:.1%}", style=color)
        
        self.console.print("\n[bold]Detailed Matchup Results[/bold]")
        
        # Create matchup table
        matchup_table = Table()
        matchup_table.add_column("Bot 1", style="cyan")
        matchup_table.add_column("Bot 2", style="cyan")
        matchup_table.add_column("Bot 1 Wins", justify="right", style="green")
        matchup_table.add_column("Bot 2 Wins", justify="right", style="red")
        matchup_table.add_column("Ties", justify="right", style="yellow")
        matchup_table.add_column("Win Rate", justify="right", style="bold")
        
        for matchup_key, result in self.results.items():
            if result['bot1'] < result['bot2']:  # Only show each matchup once
                bot1_wins = result['bot1_wins']
                bot2_wins = result['bot2_wins']
                ties = result['ties']
                total = result['total_games']
                
                if total > 0:
                    win_rate = bot1_wins / total
                    win_rate_str = f"{win_rate:.1%}"
                else:
                    win_rate_str = "N/A"
                
                matchup_table.add_row(
                    result['bot1'].title(),
                    result['bot2'].title(),
                    str(bot1_wins),
                    str(bot2_wins),
                    str(ties),
                    win_rate_str
                )
        
        self.console.print(matchup_table)
    
    def display_performance_analysis(self, bot_stats: Dict):
        """Display detailed performance analysis."""
        self.console.print("\n[bold]Performance Analysis[/bold]")
        
        # Find the best and worst performers
        sorted_bots = sorted(bot_stats.items(), key=lambda x: x[1]['win_rate'], reverse=True)
        best_bot = sorted_bots[0]
        worst_bot = sorted_bots[-1]
        
        self.console.print(f"🏆 Best Performer: {best_bot[0].title()} ({best_bot[1]['win_rate']:.1%} win rate)")
        self.console.print(f"📉 Worst Performer: {worst_bot[0].title()} ({worst_bot[1]['win_rate']:.1%} win rate)")
        
        # Calculate average win rates
        avg_win_rate = statistics.mean(stats['win_rate'] for stats in bot_stats.values())
        self.console.print(f"📊 Average Win Rate: {avg_win_rate:.1%}")
        
        # Performance insights
        self.console.print("\n[bold]Insights:[/bold]")
        for bot_name, stats in bot_stats.items():
            if stats['win_rate'] > avg_win_rate:
                self.console.print(f"✅ {bot_name.title()} performs above average")
            elif stats['win_rate'] < avg_win_rate:
                self.console.print(f"❌ {bot_name.title()} performs below average")
            else:
                self.console.print(f"➖ {bot_name.title()} performs at average level")


@click.command()
@click.option('--board-size', default=3, help='Board size (default: 3)')
@click.option('--games-per-matchup', default=100, help='Games per matchup (default: 100)')
@click.option('--output-file', help='Save results to file')
def main(board_size: int, games_per_matchup: int, output_file: str):
    """Run bot tournament and display performance charts."""
    tester = BotTester(board_size, games_per_matchup)
    
    # Run tournament
    results = tester.run_tournament()
    
    # Calculate statistics
    bot_stats = tester.calculate_bot_stats()
    
    # Display results
    tester.display_results_table(bot_stats)
    tester.display_ascii_charts(bot_stats)
    tester.display_performance_analysis(bot_stats)
    
    # Save results if requested
    if output_file:
        import json
        with open(output_file, 'w') as f:
            json.dump({
                'results': results,
                'bot_stats': bot_stats,
                'config': {
                    'board_size': board_size,
                    'games_per_matchup': games_per_matchup
                }
            }, f, indent=2)
        tester.console.print(f"\n[green]Results saved to {output_file}[/green]")


if __name__ == "__main__":
    main() 