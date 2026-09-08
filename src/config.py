import os
from pathlib import Path

# Locate project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def _load_environment():
    """
    Loads environment variables from .env file.
    Uses native standard library parsing first (works 100% offline with zero dependencies),
    and optionally enhances with python-dotenv if available.
    """
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        return

    # 1. Native standard library parser
    try:
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key not in os.environ:
                        os.environ[key] = val
    except Exception:
        pass

    # 2. Optional python-dotenv enhancement
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file, override=False)
    except ImportError:
        pass

_load_environment()

def _get_int(key: str, default: int) -> int:
    try:
        val = os.getenv(key)
        return int(val) if val is not None else default
    except (ValueError, TypeError):
        return default

def _get_float(key: str, default: float) -> float:
    try:
        val = os.getenv(key)
        return float(val) if val is not None else default
    except (ValueError, TypeError):
        return default

class Config:
    """Application configuration loaded from environment variables."""

    # Project & Author Metadata
    VERSION: str = "v1.0"
    AUTHOR: str = "Hasitha Wijesinghe"
    GITHUB: str = "https://github.com/HasithaLWi"

    # 1. API Key
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()

    # 2. Model Name
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()

    # 3. PDF Input Limit
    MAX_PDF_LIMIT: int = _get_int("MAX_PDF_LIMIT", 5)

    # 4. OCR Scale Factor
    OCR_SCALE: float = _get_float("OCR_SCALE", 2.0)

    # 5. Output Directory
    OUTPUT_DIR_NAME: str = os.getenv("OUTPUT_DIR", "output").strip()
    OUTPUT_DIR: Path = PROJECT_ROOT / OUTPUT_DIR_NAME

    @classmethod
    def validate_api_key(cls) -> bool:
        """Checks whether a valid API key is present."""
        return bool(cls.GEMINI_API_KEY and len(cls.GEMINI_API_KEY) > 10)

    @classmethod
    def display_summary(cls):
        """Prints active configuration summary with author credentials."""
        key_status = "Configured (Hidden)" if cls.validate_api_key() else "Missing / Offline Mode"
        print("=" * 60)
        print(f"LECTURE DOCUMENT GENERATOR  |  {cls.VERSION}")
        print(f"Developed by {cls.AUTHOR} (GitHub: @HasithaLWi)")
        print("=" * 60)
        print(f"  • Gemini API Key  : {key_status}")
        print(f"  • Gemini Model    : {cls.GEMINI_MODEL}")
        print(f"  • Max PDF Limit   : {cls.MAX_PDF_LIMIT} files")
        print(f"  • OCR Resolution  : {cls.OCR_SCALE}x")
        print(f"  • Output Directory: {cls.OUTPUT_DIR}")
        print("=" * 60)

if __name__ == "__main__":
    Config.display_summary()
