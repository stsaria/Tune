import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.makedirs("dbs", exist_ok=True)

from src.gui.app import main

if __name__ == "__main__":
    main()