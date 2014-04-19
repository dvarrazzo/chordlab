"""
Style management for pdf output.

This file is part of chordlab.
"""

import re
import pkgutil
from cStringIO import StringIO
from ConfigParser import ConfigParser

from reportlab.lib import colors
from reportlab.lib.colors import Color

from .error import ChordLibError

def get_base_stylesheet():
    """Return as `StyleSheet` populated with a default style."""
    conf = ConfigParser()
    conf.readfp(StringIO(pkgutil.get_data('chordlib', 'data/base.ini')))
    return StyleSheet(conf)


class StyleSheet(object):
    def __init__(self, config):
        self.config = config

    def __getitem__(self, item):
        return Style(self.config, item)

    def read(self, *files):
        out = self.config.read(files)
        if list(out) != list(files):
            raise ChordLibError("stylesheet not found: %s"
                % ', '.join(sorted(set(files) - set(out))))


class Style(object):
    def __init__(self, config, item):
        self.config = config
        self.item = item

    @property
    def font(self):
        return self.config.get(self.item, 'font')

    @property
    def font_size(self):
        return self.config.getint(self.item, 'font-size')

    @property
    def line_height(self):
        return self.config.getint(self.item, 'line-height')

    @property
    def rise(self):
        return self.config.getint(self.item, 'rise')

    @property
    def indent(self):
        return self.config.getint(self.item, 'indent')

    @property
    def color(self):
        col = self.config.get(self.item, 'color')

        # color like #FFF
        m = re.match('#([0-9a-fA-F]{3})', col)
        if m:
            return Color(*[int(c, 16) / 15. for c in m.group(1)])

        # color like #FFFFFF
        m = re.match('#([0-9a-fA-F]{6})', col)
        if m:
            return Color(*[int(m.group(1)[c:c+2], 16) / 255.  for c in (0,2,4)])

        # color by name
        rv = getattr(colors, col, None)
        if isinstance(rv, Color):
            return rv
        else:
            raise ValueError('bad color: %s' % col)

    LEFT = 'left'
    RIGHT = 'right'
    CENTER = 'center'

    @property
    def align(self):
        align = self.config.get(self.item, 'align').lower()
        if align == 'left':
            return self.LEFT
        elif align == 'right':
            return self.RIGHT
        elif align in ('centre', 'center'):
            return self.CENTER
        else:
            raise ValueError('bad align: %s' % align)

    @property
    def scale(self):
        scale = self.config.get(self.item, 'scale')
        if '%' in scale:
            return float(scale.replace('%', '')) * 0.01
        else:
            return float(scale)
