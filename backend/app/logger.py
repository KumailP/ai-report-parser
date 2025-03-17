import logging
import sys

# Configure application-wide logging with timestamp, log level, and source location
logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(message)s - {%(filename)s:%(lineno)d}',
    level=logging.INFO,
    stream=sys.stdout,
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Create a named logger for the application
logger = logging.getLogger("app_logger")
