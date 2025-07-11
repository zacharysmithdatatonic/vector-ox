"""Setup module for Vector-OX project."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .data_generator import DataGenerator
from .vector_builder import VectorBuilder


@click.command()
@click.option('--board-size', default=3, help='Board size (default: 3)')
@click.option('--num-games', default=1000, help='Number of games to generate (default: 1000)')
@click.option('--skip-data-generation', is_flag=True, help='Skip data generation step')
def main(board_size: int, num_games: int, skip_data_generation: bool):
    """Setup Vector-OX project with specified board size."""
    console = Console()
    
    console.print(Panel(
        f"[bold green]Vector-OX Setup[/bold green]\n"
        f"Board Size: {board_size}x{board_size}\n"
        f"Games to Generate: {num_games}",
        style="green"
    ))
    
    if not skip_data_generation:
        console.print("\n[bold]Step 1: Generating training data...[/bold]")
        try:
            generator = DataGenerator(board_size)
            games_data = generator.generate_games(num_games)
            generator.save_to_file(games_data, "training_data.txt")
            console.print("[green]✓ Training data generated successfully[/green]")
        except Exception as e:
            console.print(f"[red]✗ Error generating training data: {e}[/red]")
            return
    else:
        console.print("[yellow]Skipping data generation...[/yellow]")
    
    console.print("\n[bold]Step 2: Building vector database...[/bold]")
    try:
        builder = VectorBuilder()
        builder.load_from_file("training_data.txt")
        count = builder.get_collection_info()
        if count > 0:
            console.print("[green]✓ Vector database built successfully[/green]")
        else:
            console.print("[yellow]⚠ Vector database is empty[/yellow]")
    except Exception as e:
        console.print(f"[red]✗ Error building vector database: {e}[/red]")
        return
    
    console.print("\n[bold]Step 3: Testing vector database...[/bold]")
    try:
        # Test with a simple board state
        test_state = "." * (board_size * board_size)
        builder.test_query(test_state)
        console.print("[green]✓ Vector database test successful[/green]")
    except Exception as e:
        console.print(f"[yellow]⚠ Vector database test failed: {e}[/yellow]")
    
    console.print(Panel(
        "[bold green]Setup Complete![/bold green]\n\n"
        "You can now play the game using:\n"
        "  make play\n"
        "  poetry run python -m vector_ox.game\n\n"
        "Available bot types:\n"
        "  - random: Makes random moves\n"
        "  - algorithm: Uses minimax algorithm\n"
        "  - vector: Uses vector database similarity search",
        style="green"
    ))


if __name__ == "__main__":
    main() 