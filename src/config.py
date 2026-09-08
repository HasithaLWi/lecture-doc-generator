import os
from pathlib import Path
from dotenv import load_dotenv

# Locate project root and load .env
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

class Config:
    """Application configuration loaded from environment variables."""
    
    # 1. API Key
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    
    # 2. Model Name
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()
    
    # 3. PDF Input Limit
    try:
        MAX_PDF_LIMIT: int = int(os.getenv("MAX_PDF_LIMIT", "5"))
    except ValueError:
        MAX_PDF_LIMIT: int = 5
        
    # 4. OCR Scale Factor
    try:
        OCR_SCALE: float = float(os.getenv("OCR_SCALE", "2.0"))
    except ValueError:
        OCR_SCALE: float = 2.0
        
    # 5. Output Directory
    OUTPUT_DIR_NAME: str = os.getenv("OUTPUT_DIR", "output").strip()
    OUTPUT_DIR: Path = PROJECT_ROOT / OUTPUT_DIR_NAME

    @classmethod
    def validate_api_key(cls) -> bool:
        """Checks whether a valid API key is present."""
        return bool(cls.GEMINI_API_KEY and len(cls.GEMINI_API_KEY) > 10)

    @classmethod
    def display_summary(cls):
        """Prints active configuration summary."""
        key_status = "Configured (Hidden)" if cls.validate_api_key() else "Missing / Not Set"
        print("=" * 60)
        print("LECTURE DOCUMENT GENERATOR - ACTIVE CONFIGURATION")
        print("=" * 60)
        print(f"  • Gemini API Key  : {key_status}")
        print(f"  • Gemini Model    : {cls.GEMINI_MODEL}")
        print(f"  • Max PDF Limit   : {cls.MAX_PDF_LIMIT} files")
        print(f"  • OCR Resolution  : {cls.OCR_SCALE}x")
        print(f"  • Output Directory: {cls.OUTPUT_DIR}")
        print("=" * 60)
