import logging
from logging.handlers import RotatingFileHandler
from core.config import Config

def setup_logger(name='DicomLogger'):
    """Initialize and configure logger with rotating file handler."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    handler = RotatingFileHandler(
        Config.LOG_FILE, 
        maxBytes=1_000_000, 
        backupCount=3
    )
    handler.setFormatter(
        logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    )
    logger.addHandler(handler)
    
    return logger
