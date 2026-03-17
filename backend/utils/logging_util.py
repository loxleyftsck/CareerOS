import logging
import os
import time
import asyncio
from functools import wraps
from datetime import datetime

# Ensure logs directory exists (absolute path relative to project root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Generate log filename based on current date
log_filename = os.path.join(LOG_DIR, f"careeros_{datetime.now().strftime('%Y-%m-%d')}.log")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

def get_logger(name):
    return logging.getLogger(name)

def time_it(func):
    """Decorator to log execution time of a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        logger = get_logger(func.__module__)
        logger.info(f"Execution of {func.__name__} took {duration:.4f} seconds.")
        return result
    
    # Handle async functions
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            result = await func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            logger = get_logger(func.__module__)
            logger.info(f"Async execution of {func.__name__} took {duration:.4f} seconds.")
            return result
        return async_wrapper
        
    return wrapper
