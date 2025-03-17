import logging
import sys

logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(message)s - {%(filename)s:%(lineno)d}',
    level=logging.INFO,
    stream=sys.stdout,
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger("app_logger")
