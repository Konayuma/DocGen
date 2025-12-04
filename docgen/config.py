import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    """Application configuration from environment variables."""
    # Gemini API settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # OpenAI API settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # OpenRouter API settings
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "amazon/nova-2-lite-v1:free")
    
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    TEMP_DIR: str = os.getenv("TEMP_DIR", "./temp")
    UPLOAD_RETENTION_SECONDS: int = int(os.getenv("UPLOAD_RETENTION_SECONDS", "3600"))
    JOB_RETENTION_SECONDS: int = int(os.getenv("JOB_RETENTION_SECONDS", "86400"))
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
    
    def __init__(self):
        # At least one API key must be set
        if not self.GEMINI_API_KEY and not self.OPENAI_API_KEY and not self.OPENROUTER_API_KEY:
            raise ValueError("At least one API key (GEMINI_API_KEY, OPENAI_API_KEY, or OPENROUTER_API_KEY) must be set")
        
        # Log available providers
        if self.GEMINI_API_KEY:
            logger.info(f"✓ Gemini API key loaded successfully (model: {self.GEMINI_MODEL})")
        else:
            logger.info("✗ Gemini API key not configured")
            
        if self.OPENAI_API_KEY:
            logger.info(f"✓ OpenAI API key loaded successfully (model: {self.OPENAI_MODEL})")
        else:
            logger.info("✗ OpenAI API key not configured")
            
        if self.OPENROUTER_API_KEY:
            logger.info(f"✓ OpenRouter API key loaded successfully (model: {self.OPENROUTER_MODEL})")
        else:
            logger.info("✗ OpenRouter API key not configured")
        
        if not os.path.exists(self.TEMP_DIR):
            os.makedirs(self.TEMP_DIR, exist_ok=True)
            logger.info(f"Created temp directory: {self.TEMP_DIR}")
    
    @property
    def has_gemini(self) -> bool:
        return bool(self.GEMINI_API_KEY)
    
    @property
    def has_openai(self) -> bool:
        return bool(self.OPENAI_API_KEY)
    
    @property
    def has_openrouter(self) -> bool:
        return bool(self.OPENROUTER_API_KEY)

config = Config()
