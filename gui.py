import sys
from pathlib import Path

# Ensure lecture_doc_generator directory is in sys.path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from src.dependency_check import ensure_dependencies
ensure_dependencies()

from src.gui_app import launch_gui

if __name__ == "__main__":
    launch_gui()
