import string
import random

try:
    from getch import getch
except ImportError:
    from msvcrt import getch


def random_str(length):
    return ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(15)])
