
from __future__ import nested_scopes, generators, division, absolute_import, with_statement, print_function, unicode_literals

__version__ = '0.3.1'

__all__ = ['sshx']

import logging

logger = logging.getLogger()

logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
