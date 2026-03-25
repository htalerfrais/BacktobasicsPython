import time
import functools

from src.infrastructure.logging_config import logger

def time_logger(func):
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        # ajouter au logger l'info que l'on veut 
        logger.info(f"Performance : {func.__name__} took {duration:.4f}s")
        
        return result
    
    return wrapper