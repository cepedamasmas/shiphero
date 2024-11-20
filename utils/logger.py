# utils/logger.py

import logging
import os
from logging.handlers import TimedRotatingFileHandler
from config.config import Config

def setup_logger(name: str) -> logging.Logger:
    """
    Set up a logger with the specified configuration.
    
    Args:
        name (str): Name of the logger
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Create logs directory if it doesn't exist
    os.makedirs(Config.LOG_DIR, exist_ok=True)
    
    # File handler with daily rotation
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(Config.LOG_DIR, f"{name}.log"),
        when="midnight",
        interval=1,
        backupCount=Config.LOG_RETENTION_DAYS
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    
    # Formatter
    formatter = logging.Formatter(
        fmt=Config.LOG_FORMAT,
        datefmt=Config.LOG_DATE_FORMAT
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger