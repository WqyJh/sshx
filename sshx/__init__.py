__version__ = '0.4.3'

__all__ = ['sshx']

import logging

logger = logging.getLogger()

logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
