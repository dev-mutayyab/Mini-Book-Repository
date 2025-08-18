import logging
import logging.handlers
from pathlib import Path


def setup_logging():
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "app.log"

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Set to DEBUG for more detail in development

    # Create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler for production
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=10_000_000, backupCount=5  # 10MB per file, 5 backups
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


# Call this in your main app (e.g., main.py)
if __name__ == "__main__":
    setup_logging()
