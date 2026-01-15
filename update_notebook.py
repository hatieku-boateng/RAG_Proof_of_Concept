"""
Script to update openai_1.ipynb to use environment variables consistently
"""

import json
import os

def update_notebook():
    """Update the notebook to use environment variables"""
    
    notebook_path = "openai_1.ipynb"
    
    # Read the notebook
    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    # Track changes
    changes_made = []
    
    # Iterate through cells
    for i, cell in enumerate(notebook['cells']):
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])
            original_source = source
            
            # Update 1: Fix MODEL_EMBEDDING to OPENAI_MODEL_EMBEDDING
            if 'MODEL_EMBEDDING' in source and 'OPENAI_MODEL_EMBEDDING' not in source:
                source = source.replace(
                    'os.getenv("MODEL_EMBEDDING")',
                    'os.getenv("OPENAI_MODEL_EMBEDDING")'
                )
                if source != original_source:
                    changes_made.append(f"Cell {i}: Updated MODEL_EMBEDDING -> OPENAI_MODEL_EMBEDDING")
                    cell['source'] = source.split('\n')
                    # Keep newlines
                    cell['source'] = [line + '\n' if idx < len(cell['source']) - 1 else line 
                                     for idx, line in enumerate(cell['source'])]
    
    # Save the updated notebook
    backup_path = "openai_1_backup.ipynb"
    
    # Create backup
    with open(backup_path, 'w', encoding='utf-8') as f:
        with open(notebook_path, 'r', encoding='utf-8') as orig:
            f.write(orig.read())
    
    # Save updated notebook
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
    
    # Report changes
    print("="*60)
    print("NOTEBOOK UPDATE COMPLETE")
    print("="*60)
    print(f"✅ Backup created: {backup_path}")
    print(f"✅ Updated notebook: {notebook_path}")
    print(f"\nChanges made: {len(changes_made)}")
    for change in changes_made:
        print(f"  • {change}")
    print("="*60)
    
    if not changes_made:
        print("\n✅ Notebook already uses consistent environment variables!")
        print("\n📝 Manual updates needed:")
        print("   1. In cells with hardcoded vector_store_id, replace with:")
        print("      vector_store_id = os.getenv('VECTOR_STORE_ID')")
        print("   2. Or use: vector_store_id = vector_store.id")
    
    return len(changes_made)

if __name__ == "__main__":
    try:
        changes = update_notebook()
        print("\n✅ Script completed successfully!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
