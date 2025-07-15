import logging
import sys

logger = logging.getLogger(__name__)

def setup_logging():
    # Don't use basicConfig - configure your named logger directly
    if logger.handlers:  # Prevent duplicate handlers
        return
    
    logger.setLevel(logging.INFO)
    
    # Add stdout handler
    # stdout_handler = logging.StreamHandler(sys.stdout)
    # stdout_handler.setFormatter(logging.Formatter(
    #     "%(asctime)s - %(levelname)s - %(message)s [in %(filename)s:%(lineno)d]"
    # ))
    # logger.addHandler(stdout_handler)



    # # Add stdout handler
    # stdout_handler = logging.StreamHandler(sys.stdout)
    stderr_handler = logging.StreamHandler(sys.stderr) # needed for azure log stream, probably a flushing issue

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s [in %(filename)s:%(lineno)d]"
    )
    # stdout_handler.setFormatter(formatter)
    stderr_handler.setFormatter(formatter)

    # logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)

    
    # # Add file handler
    # file_handler = logging.FileHandler("app.log", mode="a")
    # file_handler.setFormatter(logging.Formatter(
    #     "%(asctime)s - %(levelname)s - %(message)s [in %(filename)s:%(lineno)d]"
    # ))
    # logger.addHandler(file_handler)


