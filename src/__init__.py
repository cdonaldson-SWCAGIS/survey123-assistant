"""Survey123 Assistant package."""

# Add the current directory to the Python path to enable relative imports
import sys
from pathlib import Path

# Add the src directory to the Python path if it's not already there
src_path = str(Path(__file__).parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)
