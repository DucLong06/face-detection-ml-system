import os
import sys

# Make modules in src/ importable as top-level (e.g. `from main import app`)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
