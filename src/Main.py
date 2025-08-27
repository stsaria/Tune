import os
import sys
from src.defined import SAVED_PATH

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.makedirs(SAVED_PATH, exist_ok=True)

from src.gui.app import main

if __name__ == "__main__":
    main()