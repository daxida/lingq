import sys

from loguru import logger

logger_format = (
    # "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    # "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> " "- <level>{message}</level>"
)
logger.remove()
logger.add(sys.stderr, format=logger_format)
