import logging
import sys

# ici nous définissons la configuration du logger
# Handler ; logger ; Formatter
# Handler à modifier pour envoyer les logging à un Prometheus puis Grafana

def setup_logging():
    # Logger
    logger = logging.getLogger("app_logger")
    logger.setLevel(logging.DEBUG) # prendre tous les logs à partir de DEBUG (donc tous)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handlers ===============
    
    # Console Handlers =======
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # File Handlers ==========
    file_handler = logging.FileHandler("app.log")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO) # override le level du logger racine
    
    # === ajout des handlers au logger ===
    if not logger.handlers : 
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
    return logger


logger = setup_logging()