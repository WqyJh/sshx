__version__ = '0.32.1'

__all__ = ['sshx']

import logging

logger = logging.getLogger()


def set_debug(debug):
    # global logger
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)


logger.addHandler(logging.StreamHandler())
set_debug(False)
