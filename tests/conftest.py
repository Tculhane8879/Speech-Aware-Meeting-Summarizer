import sys
from pathlib import Path

# Add src/ to Python path so tests can import the package
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))