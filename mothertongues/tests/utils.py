from contextlib import contextmanager

from loguru import logger


# See https://loguru.readthedocs.io/en/latest/resources/migration.html#replacing-assertlogs-method-from-unittest-library
@contextmanager
def capture_logs(level="INFO", format="{level}:{name}:{message}"):
    """Capture loguru-based logs. Particularly useful for unit testing"""
    output = []
    handler_id = logger.add(output.append, level=level, format=format)
    yield output
    logger.remove(handler_id)
