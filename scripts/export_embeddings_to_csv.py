"""
Export embeddings from JSON to CSV format for easier import into vector databases.
"""

import json
import csv
from pathlib import Path
import pandas as pd

# Configuration
EMBEDDINGS_DIR = Path(__file__).parent.parent / "embeddings_output"
INPUT_FILE = EMBEDDINGS_DIR / "embeddings.json"
OUTPUT_CSV = EMBEDDINGS_DIR / "embeddings.csv"
OUTPUT_PARQUET = EMBEDDINGS_DIR / "embeddings.parquet"


def load_embeddings(json_path: Path):
    """Load embeddings from JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def export_to_csv(embeddings, output_path: Path):
    """Export embeddings to CSV file."""
    print(f"Exporting {len(embeddings)} embeddings to CSV...")
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow([
            'file_name',
            'file_path',
            'chunk_index',
            'chunk_text',
            'embedding',
            'total_chunks',
            'chunk_size',
            'model'
        ])
        
        # Write data
        for item in embeddings:
            writer.writerow([
                item['file_name'],
                item['file_path'],
                item['chunk_index'],
                item['chunk_text'],
                json.dumps(item['embedding']),  # Store as JSON string
                item['metadata']['total_chunks'],
                item['metadata']['chunk_size'],
                item['metadata']['model']
            ])
    
    print(f"CSV export complete: {output_path}")
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"File size: {size_mb:.2f} MB")


def export_to_parquet(embeddings, output_path: Path):
    """Export embeddings to Parquet format for efficient storage."""
    print(f"Exporting {len(embeddings)} embeddings to Parquet...")
    
    # Flatten the data structure
    flattened_data = []
    for item in embeddings:
        flattened_data.append({
            'file_name': item['file_name'],
            'file_path': item['file_path'],
            'chunk_index': item['chunk_index'],
            'chunk_text': item['chunk_text'],
            'embedding': item['embedding'],
            'total_chunks': item['metadata']['total_chunks'],
            'chunk_size': item['metadata']['chunk_size'],
            'model': item['metadata']['model']
        })
    
    # Create DataFrame
    df = pd.DataFrame(flattened_data)
    
    # Save to Parquet
    df.to_parquet(output_path, compression='snappy', index=False)
    
    print(f"Parquet export complete: {output_path}")
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"File size: {size_mb:.2f} MB")
    
    return df


def print_stats(embeddings):
    """Print statistics about the embeddings."""
    print("\n" + "=" * 60)
    print("Embeddings Statistics")
    print("=" * 60)
    
    # Count by file
    files = {}
    for item in embeddings:
        file_name = item['file_name']
        files[file_name] = files.get(file_name, 0) + 1
    
    print(f"Total embeddings: {len(embeddings)}")
    print(f"Files processed: {len(files)}")
    print("\nChunks per file:")
    for file_name, count in sorted(files.items()):
        print(f"  {file_name}: {count} chunks")
    
    # Embedding dimensions
    if embeddings:
        embedding_dim = len(embeddings[0]['embedding'])
        print(f"\nEmbedding dimensions: {embedding_dim}")
        print(f"Model used: {embeddings[0]['metadata']['model']}")


def main():
    """Main function to export embeddings."""
    print("=" * 60)
    print("Export Embeddings to CSV/Parquet")
    print("=" * 60)
    
    # Check if input file exists
    if not INPUT_FILE.exists():
        print(f"Error: Input file not found: {INPUT_FILE}")
        print("Please run create_embeddings.py first.")
        return
    
    # Load embeddings
    print(f"Loading embeddings from {INPUT_FILE}...")
    embeddings = load_embeddings(INPUT_FILE)
    
    # Print statistics
    print_stats(embeddings)
    
    # Export to CSV
    print("\n" + "=" * 60)
    export_to_csv(embeddings, OUTPUT_CSV)
    
    # Export to Parquet
    print("\n" + "=" * 60)
    export_to_parquet(embeddings, OUTPUT_PARQUET)
    
    print("\n" + "=" * 60)
    print("Export Complete!")
    print("=" * 60)
    print(f"CSV: {OUTPUT_CSV}")
    print(f"Parquet: {OUTPUT_PARQUET}")


if __name__ == "__main__":
    main()
