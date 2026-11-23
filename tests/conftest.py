import sys
from pathlib import Path

# The project is not a package: the folder of the repository is added to the path to import its modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
