# config/config.py

from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration settings for ShipHero integration."""
    
    # API Configuration
    BASE_URL_AUTH = "https://public-api.shiphero.com/"
    BASE_URL = "https://public-api.shiphero.com/graphql"
    ACCESS_TOKEN = os.getenv("SHIPHERO_ACCESS_TOKEN")
    REFRESH_TOKEN = os.getenv("SHIPHERO_REFRESH_TOKEN")
    EMAIL = os.getenv("SHIPHERO_EMAIL")
    
    # Rate Limiting
    MAX_REQUESTS_PER_MINUTE = 100
    
    # Cache Configuration
    CACHE_TTL = timedelta(minutes=5)
    
    # Retry Configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    
    # Output Configuration
    CSV_SEPARATOR = ","
    CSV_ENCODING = "UTF-8"
    OUTPUT_DIR = "output"
    
    # Logging Configuration
    LOG_DIR = "logs"
    LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(module)s] - %(message)s"
    LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    LOG_RETENTION_DAYS = 30
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration values are present."""
        required_vars = ["ACCESS_TOKEN", "REFRESH_TOKEN", "EMAIL"]
        missing_vars = [var for var in required_vars if not getattr(cls, var)]
        if missing_vars:
            raise ValueError(f"Missing required configuration variables: {', '.join(missing_vars)}")