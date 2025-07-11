"""Main game module for Vector-OX."""

import click
import sys
import tty
import termios
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.align import Align
from rich.columns import Columns
from typing import List, Tuple, Optional

from .board import Board
from .bots import RandomBot, AlgorithmBot, VectorBot


class GameState:
    """Represents a game state with thinking information."""
    
    def __init__(self, board: Board, thinking: str = "", move: Optional[Tuple[int, int]] = None):
        self.board = board.copy()
        self.thinking = thinking
        self.move = move


class Game:
    """Main game class for Vector-OX."""
    
    def __init__(self, board_size: int = 3):
        self.board_size = board_size
        self.board = Board(board_size)
        self.console = Console()
        self.bots = {
            'random': RandomBot(),
            'algorithm': AlgorithmBot(),
            'vector': VectorBot()
        }
        self.game_history: List[GameState] = []
        self.current_state_index = -1
        self.thinking_display = ""
    
    def get_keypress(self) -> str:
        """Get a single keypress without requiring Enter."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        
    def create_layout(self) -> Layout:
        """Create the game layout with thinking panel."""
        layout = Layout()
        
        # Add top margin for input space
        layout.split_column(
            Layout(name="margin", size=3),  # Fixed 3-line margin at top
            Layout(name="game_area")
        )
        
        # Split game area into main area and thinking panel
        layout["game_area"].split_column(
            Layout(name="main", ratio=5),
            Layout(name="thinking", ratio=1)
        )
        
        # Split main area into board and controls
        layout["main"].split_row(
            Layout(name="board", ratio=4),  # Increased board ratio
            Layout(name="controls", ratio=2)
        )
        
        return layout
    
    def display_board(self) -> Panel:
        """Display the current board state."""
        table = Table(show_header=False, show_edge=True, box=None, padding=(1, 2))  # Increased padding
        
        # Add columns with increased width
        for i in range(self.board_size):
            table.add_column(f"col_{i}", justify="center", width=5)  # Increased width
        
        # Add rows
        for row in range(self.board_size):
            row_data = []
            for col in range(self.board_size):
                cell = self.board.get_cell(row, col)
                if cell == 'X':
                    row_data.append(Text("X", style="bold red"))
                elif cell == 'O':
                    row_data.append(Text("O", style="bold blue"))
                else:
                    # Show position numbers for 3x3 board
                    if self.board_size == 3:
                        pos = row * self.board_size + col + 1
                        row_data.append(Text(str(pos), style="dim"))
                    else:
                        row_data.append(Text("·", style="dim"))
            table.add_row(*row_data)
        
        # Add padding around the board with a title
        return Panel(
            Align.center(table),  # Center the table in the panel
            title="Board",
            border_style="blue",
            padding=(1, 1)  # Add padding inside the panel
        )
    
    def display_thinking_panel(self) -> Panel:
        """Display the thinking panel."""
        if not self.thinking_display:
            content = Text("Waiting for bot...", style="dim")
        else:
            # Limit thinking display to 3 lines
            lines = self.thinking_display.split('\n')
            if len(lines) > 3:
                content = Text('\n'.join(lines[:3]) + '\n...', style="green")
            else:
                content = Text(self.thinking_display, style="green")
        
        return Panel(content, title="Bot Thinking", border_style="green")
    
    def display_controls(self) -> Panel:
        """Display navigation controls."""
        controls = []
        
        # Navigation controls
        if self.current_state_index > 0:
            controls.append("[bold blue][[/bold blue] Previous")
        if self.current_state_index < len(self.game_history) - 1:
            controls.append("[bold blue]][/bold blue] Next")
        if self.current_state_index < len(self.game_history) - 1:
            controls.append("[bold green]>[/bold green] Fast-forward")
        
        # Game controls
        controls.append("[bold yellow]r[/bold yellow] Reset")
        controls.append("[bold red]q[/bold red] Quit")
        
        if not controls:
            controls.append("No navigation")
        
        return Panel("\n".join(controls), title="Controls", border_style="yellow")
    
    def display_game_info(self) -> Panel:
        """Display game information."""
        info = []
        info.append(f"Size: {self.board_size}x{self.board_size}")
        
        # Show current turn with emphasis
        if not self.board.is_game_over():
            current_player = self.board.current_player
            if current_player == 'X':
                info.append("[bold red]Turn: X (You)[/bold red]")
            else:
                info.append("[bold blue]Turn: O (Bot)[/bold blue]")
        else:
            info.append("Game: Over")
        
        info.append(f"Moves: {len(self.game_history)}")
        
        if self.board.is_game_over():
            winner = self.board.get_winner()
            if winner:
                if winner == 'X':
                    info.append("[bold green]Winner: You![/bold green]")
                else:
                    info.append("[bold red]Winner: Bot![/bold red]")
            else:
                info.append("[bold yellow]Tie![/bold yellow]")
        
        return Panel("\n".join(info), title="Game Info", border_style="cyan")
    

    
    def update_display(self, layout: Layout):
        """Update the game display."""
        # Update board
        layout["board"].update(self.display_board())
        
        # Update thinking panel
        layout["thinking"].update(self.display_thinking_panel())
        
        # Update controls
        controls_layout = Layout()
        controls_layout.split_column(
            Layout(self.display_controls()),
            Layout(self.display_game_info())
        )
        layout["controls"].update(controls_layout)
    
    def get_player_move(self) -> tuple[int, int]:
        """Get move from human player."""
        while True:
            try:
                move = Prompt.ask("Enter your move (1-9 for 3x3, or row,col format)")
                
                # Handle 1-9 format for 3x3 board
                if self.board_size == 3 and move.isdigit():
                    num = int(move) - 1
                    if 0 <= num <= 8:
                        row = num // 3
                        col = num % 3
                        if self.board.is_valid_move(row, col):
                            return row, col
                        else:
                            self.console.print("[red]That position is already taken![/red]")
                            continue
                    else:
                        self.console.print("[red]Invalid number! Use 1-9.[/red]")
                        continue
                
                # Handle row,col format
                if ',' in move:
                    row_str, col_str = move.split(',')
                    row = int(row_str.strip()) - 1
                    col = int(col_str.strip()) - 1
                    
                    if 0 <= row < self.board_size and 0 <= col < self.board_size:
                        if self.board.is_valid_move(row, col):
                            return row, col
                        else:
                            self.console.print("[red]That position is already taken![/red]")
                            continue
                    else:
                        self.console.print(f"[red]Invalid position! Use 1-{self.board_size} for row and column.[/red]")
                        continue
                
                self.console.print("[red]Invalid input! Use 1-9 for 3x3 or row,col format.[/red]")
                
            except ValueError:
                self.console.print("[red]Invalid input! Please try again.[/red]")
    
    def _parse_move_input(self, move_input: str) -> Tuple[int, int]:
        """Parse move input and return (row, col)."""
        # Handle 1-9 format for 3x3 board
        if self.board_size == 3 and move_input.isdigit():
            num = int(move_input) - 1
            if 0 <= num <= 8:
                row = num // 3
                col = num % 3
                return row, col
            else:
                raise ValueError("Invalid number! Use 1-9.")
        
        # Handle row,col format
        if ',' in move_input:
            row_str, col_str = move_input.split(',')
            row = int(row_str.strip()) - 1
            col = int(col_str.strip()) - 1
            
            if 0 <= row < self.board_size and 0 <= col < self.board_size:
                return row, col
            else:
                raise ValueError(f"Invalid position! Use 1-{self.board_size} for row and column.")
        
        raise ValueError("Invalid input! Use 1-9 for 3x3 or row,col format.")
    
    def add_to_history(self, thinking: str = "", move: Optional[Tuple[int, int]] = None):
        """Add current state to history."""
        state = GameState(self.board, thinking, move)
        self.game_history.append(state)
        self.current_state_index = len(self.game_history) - 1
    
    def navigate_to_state(self, index: int):
        """Navigate to a specific game state."""
        if 0 <= index < len(self.game_history):
            self.current_state_index = index
            state = self.game_history[index]
            self.board = state.board.copy()
            self.thinking_display = state.thinking
    
    def handle_navigation(self, key: str) -> bool:
        """Handle navigation keys. Returns True if navigation occurred."""
        if key == "[" and self.current_state_index > 0:
            self.navigate_to_state(self.current_state_index - 1)
            return True
        elif key == "]" and self.current_state_index < len(self.game_history) - 1:
            self.navigate_to_state(self.current_state_index + 1)
            return True
        elif key == ">" and len(self.game_history) > 0:
            self.navigate_to_state(len(self.game_history) - 1)
            return True
        elif key == "r":
            self.reset_game()
            return True
        elif key == "q":
            return "quit"
        return False
    
    def reset_game(self):
        """Reset the game to initial state."""
        self.board = Board(self.board_size)
        self.game_history = []
        self.current_state_index = -1
        self.thinking_display = ""
    
    def play_game(self, player_symbol: str = 'X', bot_type: str = 'random'):
        """Play a complete game with enhanced interface."""
        bot = self.bots[bot_type]
        bot_symbol = 'O' if player_symbol == 'X' else 'X'
        
        # Initialize layout
        layout = self.create_layout()
        
        # Print initial game info
        self.console.clear()
        self.console.print("\n")  # Add extra line at top
        self.console.print(Panel(
            "[bold green]Playing against " + bot_type.title() + " Bot[/bold green]\n" +
            "Use [ and ] to navigate, '>' to fast-forward, 'r' to reset, 'q' to quit",
            border_style="green"
        ))
        
        while True:  # Main app loop
            # Clear screen and update display
            self.console.clear()
            self.console.print("\n")  # Add extra line at top
            self.update_display(layout)
            self.console.print(layout)
            
            # Show game result if game is over
            if self.board.is_game_over():
                winner = self.board.get_winner()
                if winner:
                    if winner == player_symbol:
                        self.console.print(f"\n[bold green]You win! 🎉[/bold green] [dim]Press [ or ] to review moves, 'r' to play again, or 'q' to quit[/dim]")
                    else:
                        self.console.print(f"\n[bold red]{bot_type.title()} Bot wins! 🤖[/bold red] [dim]Press [ or ] to review moves, 'r' to play again, or 'q' to quit[/dim]")
                else:
                    self.console.print(f"\n[bold yellow]It's a tie! 🤝[/bold yellow] [dim]Press [ or ] to review moves, 'r' to play again, or 'q' to quit[/dim]")
                while True:
                    try:
                        key = self.get_keypress()
                        if key in ['[', ']', '>', 'r', 'q']:
                            result = self.handle_navigation(key)
                            if result == "quit":
                                return
                            elif result:
                                break  # Break inner loop to refresh display
                            elif key == 'r':  # Start new game
                                break  # Break inner loop to start new game
                    except KeyboardInterrupt:
                        return
                continue  # Continue main loop to refresh display
            
            if self.board.current_player == player_symbol:
                # Human turn
                self.console.print(f"\n[bold red]Your turn ({player_symbol})[/bold red]")
                
                # Get player move with immediate keypress input
                move_input = ""
                while True:
                    try:
                        # Get single keypress
                        key = self.get_keypress()
                        
                        # Handle navigation commands
                        if key in ['[', ']', '>', 'r', 'q']:
                            result = self.handle_navigation(key)
                            if result == "quit":
                                return
                            elif result:
                                self.update_display(layout)
                                self.console.print("\n")  # Add extra line at top
                                self.console.print(layout)
                                continue
                        
                        # Handle backspace
                        elif key == '\x7f' or key == '\x08':  # Backspace
                            if move_input:
                                move_input = move_input[:-1]
                                self.console.print(f"\r[dim]Move: {move_input}[/dim]", end="")
                            continue
                        
                        # Handle enter
                        elif key == '\r' or key == '\n':  # Enter
                            if move_input:
                                try:
                                    row, col = self._parse_move_input(move_input)
                                    if self.board.is_valid_move(row, col):
                                        self.board.make_move(row, col, player_symbol)
                                        self.add_to_history(f"Player moved to ({row+1}, {col+1})", (row, col))
                                        break
                                    else:
                                        self.console.print("\n[red]Invalid move! Position already taken.[/red]")
                                        move_input = ""
                                except ValueError:
                                    self.console.print("\n[red]Invalid input! Use 1-9 for 3x3 or row,col format.[/red]")
                                    move_input = ""
                            continue
                        
                        # Add character to input
                        elif key.isprintable():
                            move_input += key
                            self.console.print(f"\r[dim]Move: {move_input}[/dim]", end="")
                        
                    except KeyboardInterrupt:
                        return
            else:
                # Bot turn
                self.console.print(f"\n[bold blue]{bot_type.title()} Bot's turn ({bot_symbol})[/bold blue]")
                self.thinking_display = "Bot is thinking..."
                self.update_display(layout)
                self.console.print("\n")  # Add extra line at top
                self.console.print(layout)
                
                # Get bot's move with explanation
                move, explanation = self._get_bot_move_with_explanation(bot, bot_type)
                row, col = move
                
                # Update thinking display
                self.thinking_display = f"🤖 {bot_type.title()} Bot's reasoning:\n{explanation}"
                self.board.make_move(row, col, bot_symbol)
                self.add_to_history(self.thinking_display, (row, col))
    
    def _get_bot_move_with_explanation(self, bot, bot_type: str) -> tuple[tuple[int, int], str]:
        """Get bot's move with explanation of its reasoning."""
        if bot_type == 'random':
            move = bot.get_move(self.board)
            explanation = "Randomly selected from available moves"
            return move, explanation
        
        elif bot_type == 'algorithm':
            move, explanation = self._get_algorithm_explanation(bot)
            return move, explanation
        
        elif bot_type == 'vector':
            move, explanation = self._get_vector_explanation(bot)
            return move, explanation
        
        else:
            move = bot.get_move(self.board)
            return move, "No explanation available"
    
    def _get_algorithm_explanation(self, bot) -> tuple[tuple[int, int], str]:
        """Get explanation for algorithm bot's move."""
        # Get the move
        move = bot.get_move(self.board)
        
        # Analyze the board state to provide explanation
        explanation_parts = []
        
        # Check for winning moves
        for row, col in self.board.get_available_moves():
            test_board = self.board.copy()
            test_board.make_move(row, col, self.board.current_player)
            if test_board.get_winner() == self.board.current_player:
                if (row, col) == move:
                    explanation_parts.append("Found winning move!")
                break
        
        # Check for blocking moves
        opponent = 'O' if self.board.current_player == 'X' else 'X'
        for row, col in self.board.get_available_moves():
            test_board = self.board.copy()
            test_board.make_move(row, col, opponent)
            if test_board.get_winner() == opponent:
                if (row, col) == move:
                    explanation_parts.append("Blocking opponent's winning move")
                break
        
        # Check for center move (good strategy)
        center = self.board_size // 2
        if move == (center, center) and self.board.get_cell(center, center) == '':
            explanation_parts.append("Taking center position (strong strategic move)")
        
        # Check for corner moves
        corners = [(0, 0), (0, self.board_size-1), (self.board_size-1, 0), (self.board_size-1, self.board_size-1)]
        if move in corners and self.board.get_cell(move[0], move[1]) == '':
            explanation_parts.append("Taking corner position (good strategic move)")
        
        # Check for edge moves
        edges = []
        for i in range(self.board_size):
            if i != center:
                edges.extend([(i, 0), (i, self.board_size-1), (0, i), (self.board_size-1, i)])
        
        if move in edges and self.board.get_cell(move[0], move[1]) == '':
            explanation_parts.append("Taking edge position")
        
        if not explanation_parts:
            explanation_parts.append("Using minimax algorithm to find optimal move")
        
        return move, " | ".join(explanation_parts)
    
    def _get_vector_explanation(self, bot) -> tuple[tuple[int, int], str]:
        """Get explanation for vector bot's move."""
        # Get the move
        move = bot.get_move(self.board)
        
        # Get current board state
        state_string = self.board.get_state_string()
        
        # Try to get similar states from vector database
        explanation_parts = []
        
        try:
            if hasattr(bot, 'collection') and bot.collection is not None:
                state_vector = self.board.get_state_vector()
                results = bot.collection.query(
                    query_embeddings=[state_vector.tolist()],
                    n_results=3
                )
                
                if results['documents'] and len(results['documents'][0]) > 0:
                    similar_moves = []
                    for doc in results['documents'][0]:
                        if doc and '|' in doc:
                            try:
                                state_str, move_str = doc.split('|', 1)
                                row, col = map(int, move_str.split(','))
                                similar_moves.append((row, col))
                            except:
                                continue
                    
                    if similar_moves:
                        move_counts = {}
                        for m in similar_moves:
                            move_counts[m] = move_counts.get(m, 0) + 1
                        
                        if move in move_counts:
                            count = move_counts[move]
                            total = sum(move_counts.values())
                            percentage = (count / total) * 100
                            explanation_parts.append(f"Found {count}/{total} similar moves in database ({percentage:.0f}% confidence)")
                        else:
                            explanation_parts.append("No exact match found in database, using fallback strategy")
                    else:
                        explanation_parts.append("No similar states found in database")
                else:
                    explanation_parts.append("Database search returned no results")
            else:
                explanation_parts.append("Vector database not available, using fallback")
                
        except Exception as e:
            explanation_parts.append(f"Database search failed: {str(e)}")
        
        # Add strategic analysis
        if not explanation_parts:
            explanation_parts.append("Using vector similarity search")
        
        return move, " | ".join(explanation_parts)


@click.command()
@click.option('--board-size', default=3, help='Board size (default: 3)')
@click.option('--player-symbol', default='X', help='Player symbol (default: X)')
@click.option('--bot-type', default='random', 
              type=click.Choice(['random', 'algorithm', 'vector']),
              help='Bot type (default: random)')
def main(board_size: int, player_symbol: str, bot_type: str):
    """Play Vector-OX game."""
    game = Game(board_size)
    game.play_game(player_symbol, bot_type)


if __name__ == "__main__":
    main() 