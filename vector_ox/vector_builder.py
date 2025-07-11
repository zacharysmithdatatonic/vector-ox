"""Vector database builder for Vector-OX."""

import click
import numpy as np
from rich.console import Console
from rich.progress import track
import chromadb

from .bots import VectorBot


class VectorBuilder:
    """Build vector database from training data."""
    
    def __init__(self, collection_name: str = "vector_ox_moves"):
        self.collection_name = collection_name
        self.console = Console()
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize the vector database connection."""
        try:
            self.client = chromadb.PersistentClient(path="./vector_db")
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(self.collection_name)
                self.console.print(f"Using existing collection: {self.collection_name}")
            except:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Vector-OX game moves"}
                )
                self.console.print(f"Created new collection: {self.collection_name}")
                
        except Exception as e:
            self.console.print(f"[red]Error initializing vector database: {e}[/red]")
            raise
    
    def load_from_file(self, filename: str = "training_data.txt"):
        """Load training data from file and add to vector database."""
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
            
            self.console.print(f"Loading {len(lines)} training examples...")
            
            documents = []
            embeddings = []
            ids = []
            metadatas = []
            
            for i, line in enumerate(track(lines, description="Processing data")):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # Parse line: state|move|outcome
                    parts = line.split('|')
                    if len(parts) >= 3:
                        state_string = parts[0]
                        move_str = parts[1]
                        outcome = parts[2]
                        
                        # Parse move
                        row, col = map(int, move_str.split(','))
                        
                        # Create vector representation
                        state_vector = self._string_to_vector(state_string)
                        
                        # Create document
                        document = f"{state_string}|{row},{col}"
                        doc_id = f"{state_string}_{row}_{col}_{i}"
                        
                        documents.append(document)
                        embeddings.append(state_vector.tolist())
                        ids.append(doc_id)
                        metadatas.append({"outcome": outcome})
                        
                except Exception as e:
                    self.console.print(f"[yellow]Warning: Skipping malformed line {i+1}: {e}[/yellow]")
                    continue
            
            if documents:
                # Add to collection in batches
                batch_size = 100
                for i in range(0, len(documents), batch_size):
                    batch_end = min(i + batch_size, len(documents))
                    
                    self.collection.add(
                        documents=documents[i:batch_end],
                        embeddings=embeddings[i:batch_end],
                        ids=ids[i:batch_end],
                        metadatas=metadatas[i:batch_end]
                    )
                
                self.console.print(f"[green]Successfully added {len(documents)} examples to vector database[/green]")
            else:
                self.console.print("[red]No valid data found in file[/red]")
                
        except FileNotFoundError:
            self.console.print(f"[red]File not found: {filename}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error loading data: {e}[/red]")
    
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
    
    def get_collection_info(self):
        """Get information about the collection."""
        try:
            count = self.collection.count()
            self.console.print(f"Collection contains {count} documents")
            return count
        except Exception as e:
            self.console.print(f"[red]Error getting collection info: {e}[/red]")
            return 0
    
    def test_query(self, state_string: str):
        """Test a query against the vector database."""
        try:
            state_vector = self._string_to_vector(state_string)
            
            results = self.collection.query(
                query_embeddings=[state_vector.tolist()],
                n_results=3
            )
            
            self.console.print(f"Query results for state: {state_string}")
            for i, doc in enumerate(results['documents'][0]):
                self.console.print(f"  {i+1}. {doc}")
                
        except Exception as e:
            self.console.print(f"[red]Error testing query: {e}[/red]")


@click.command()
@click.option('--input-file', default='training_data.txt', help='Input file with training data')
@click.option('--test-query', help='Test query with a board state (e.g., "X.O.X.O..")')
def main(input_file: str, test_query: str):
    """Build vector database from training data."""
    builder = VectorBuilder()
    
    if test_query:
        builder.test_query(test_query)
    else:
        builder.load_from_file(input_file)
        builder.get_collection_info()


if __name__ == "__main__":
    main() 