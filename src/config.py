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
    VERSION: str = "v2.0"
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

    # 6. Document Header
    COURSE_HEADER: str = os.getenv(
        "COURSE_HEADER",
        "Comprehensive Lecture Study Guide"
    ).strip()

    @classmethod
    def reload(cls):
        """Reloads environment variables and updates class attributes."""
        _load_environment()
        cls.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
        cls.GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()
        cls.MAX_PDF_LIMIT = _get_int("MAX_PDF_LIMIT", 5)
        cls.OCR_SCALE = _get_float("OCR_SCALE", 2.0)
        cls.OUTPUT_DIR_NAME = os.getenv("OUTPUT_DIR", "output").strip()
        cls.OUTPUT_DIR = PROJECT_ROOT / cls.OUTPUT_DIR_NAME
        cls.COURSE_HEADER = os.getenv(
            "COURSE_HEADER",
            "Comprehensive Lecture Study Guide"
        ).strip()

    @classmethod
    def save_to_env(cls, key_values: dict):
        """Saves or updates given key-value pairs into the .env file and reloads config."""
        env_file = PROJECT_ROOT / ".env"
        lines = []
        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

        updated_keys = set()
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                k, _ = stripped.split("=", 1)
                k = k.strip()
                if k in key_values:
                    new_lines.append(f"{k}={key_values[k]}\n")
                    os.environ[k] = str(key_values[k])
                    updated_keys.add(k)
                    continue
            new_lines.append(line)

        # Append any remaining new keys
        for k, v in key_values.items():
            if k not in updated_keys:
                new_lines.append(f"{k}={v}\n")
                os.environ[k] = str(v)

        with open(env_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        cls.reload()

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
        print(f"  • Course Header   : {cls.COURSE_HEADER}")
        print(f"  • Output Directory: {cls.OUTPUT_DIR}")
        print("=" * 60)

if __name__ == "__main__":
    Config.display_summary()
