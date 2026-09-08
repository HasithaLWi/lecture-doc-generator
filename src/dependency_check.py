import importlib
import subprocess
import sys
from pathlib import Path

# Mapping of import module name to package requirement name
REQUIRED_IMPORTS = {
    "pymupdf": "pymupdf",
    "winocr": "winocr",
    "PIL": "pillow",
    "docx": "python-docx",
    "google.genai": "google-genai",
    "dotenv": "python-dotenv",
    "customtkinter": "customtkinter",
}

def ensure_dependencies() -> bool:
    """
    Checks if all required packages are present in the current Python environment.
    If any dependency is missing, automatically installs all packages from requirements.txt.
    """
    missing = []
    for mod_name, pkg_name in REQUIRED_IMPORTS.items():
        try:
            importlib.import_module(mod_name)
        except ImportError:
            missing.append(pkg_name)

    if missing:
        req_file = Path(__file__).resolve().parent.parent / "requirements.txt"
        print("=" * 60)
        print(f"[Dependency Manager] Missing required packages: {', '.join(missing)}")
        print(f"[Dependency Manager] Auto-installing from {req_file.name} to environment...")
        print("=" * 60)

        if not req_file.exists():
            print(f"[Dependency Manager Error] requirements.txt not found at: {req_file}")
            return False

        try:
            cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_file)]
            subprocess.check_call(cmd)
            print("=" * 60)
            print("[Dependency Manager] All required packages installed successfully!")
            print("=" * 60)
            return True
        except subprocess.CalledProcessError as e:
            print(f"[Dependency Manager Error] Failed to install dependencies via pip: {e}")
            return False

    return True

if __name__ == "__main__":
    ensure_dependencies()
