"""Chat assistant for Survey123 form creation."""

__version__ = "1.0.0"

# Add relative import support
import sys
from pathlib import Path

# Add the src directory to the Python path if it's not already there
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.insert(0, src_path)
