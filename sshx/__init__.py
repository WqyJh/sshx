__version__ = '0.3.1'

__all__ = ['sshx']

import logging

logger = logging.getLogger()

logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
