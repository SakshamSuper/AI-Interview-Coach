import logging
import sys
from typing import Optional
from config.settings import get_settings

def setup_logger(name: Optional[str] = "ai_interview_coach") -> logging.Logger:
    """Configures and returns a structured logger."""
    settings = get_settings()
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        level = logging.DEBUG if settings.DEBUG else logging.INFO
        logger.setLevel(level)
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
        
    return logger

logger = setup_logger()
