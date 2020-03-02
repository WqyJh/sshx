# -*- coding: future_fstrings -*-

class Forward(object):
    def __init__(self, maps, local_forward):
        self.maps = ''

        if maps:
            if isinstance(maps, (list, tuple)):
                self.maps = maps
            elif isinstance(maps, str):
                self.maps = [maps]

        self.local_forward = local_forward

    def split(self):
        if self.maps:
            return [m.split(':') for m in self.maps]

    def compile(self):
        if not self.maps:
            return ''

        arg = '-L' if self.local_forward else '-R'
        forwards = ['%s %s' % (arg, m) for m in self.maps]
        return ' '.join(forwards)


class Forwards(object):
    def __init__(self, maps, rmaps):
        self.forward = Forward(maps, True) if maps else None
        self.rforward = Forward(rmaps, False) if rmaps else None

    def compile(self):
        forward = self.forward.compile() if self.forward else ''
        rforward = self.rforward.compile() if self.rforward else ''
        return f'{forward} {rforward}'.strip()
