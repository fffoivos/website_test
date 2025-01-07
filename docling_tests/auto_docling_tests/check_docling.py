import os
import sys

# Add parent directory to Python path to import auto_docling
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auto_docling import is_docling_running

# Print all processes for debugging
result = is_docling_running()
print(f"Docling is {'running' if result else 'not running'}")
