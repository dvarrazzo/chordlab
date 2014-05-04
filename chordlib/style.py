"""
Style management for pdf output.

This file is part of chordlab.
"""

import re
import pkgutil
import ConfigParser
from cStringIO import StringIO

from reportlab.lib import colors
from reportlab.lib.colors import Color
from reportlab.lib.fonts import tt2ps

from .error import ChordLibError

def get_base_stylesheet():
    """Return as `StyleSheet` populated with a default style."""
    conf = ConfigParser.ConfigParser()
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

sect_hierarchy = {
    'title': 'songsheet',
    'subtitle': 'songsheet',
    'comment': 'songsheet',
    'line': 'songsheet',
    'chord': 'songsheet',
    'tab': 'songsheet',
    'chorus': 'songsheet',
    'chordbox': 'songsheet',
    'blank': 'songsheet',
}

class Style(object):
    def __init__(self, config, item):
        self.config = config
        self.item = item

    @property
    def ttfont(self):
        return self._parse('font')

    @property
    def font_weight(self):
        return self._parse_choices('font-weight', ['normal', 'bold'])

    @property
    def font_style(self):
        return self._parse_choices('font-style', ['normal', 'italic'])

    @property
    def font(self):
        font = self.ttfont
        bold = self.font_weight == 'bold'
        italic = self.font_style == 'italic'
        return tt2ps(font, bold, italic)

    @property
    def font_size(self):
        return self._parse_int('font-size')

    @property
    def line_height(self):
        return self._parse_int('line-height')

    @property
    def rise(self):
        return self._parse_int('rise')

    @property
    def indent(self):
        return self._parse_int('indent')

    @property
    def color(self):
        return self._parse_color('color')

    LEFT = 'left'
    RIGHT = 'right'
    CENTER = 'center'

    @property
    def align(self):
        return self._parse_choices('align',
            [self.LEFT, self.RIGHT, self.CENTER])

    @property
    def scale(self):
        return self._parse_percent('scale')

    @property
    def duplex(self):
        return self._parse_bool('duplex')

    @property
    def margin_top(self):
        return self._parse_float('margin-top')

    @property
    def margin_bottom(self):
        return self._parse_float('margin-bottom')

    @property
    def margin_left(self):
        return self._parse_float('margin-left')

    @property
    def margin_right(self):
        return self._parse_float('margin-right')

    @property
    def margin_gutter(self):
        return self._parse_float('margin-gutter')

    def _parse(self, opt):
        sect = self.item
        while sect:
            try:
                return self.config.get(sect, opt)
            except ConfigParser.NoOptionError:
                # option not found: maybe specified in an ancestor?
                sect = sect_hierarchy.get(sect)
            except ConfigParser.Error, e:
                raise ChordLibError(str(e))
        else:
            raise ChordLibError(
                "no option '%s' in section '%s' or above"
                % (opt, self.item))

    def _parse_int(self, opt):
        val = self._parse(opt)
        try:
            return int(val)
        except ValueError:
            raise ChordLibError(
                "bad integer value for '%s' in section '%s': %s"
                    % (opt, self.item, val))

    def _parse_float(self, opt):
        val = self._parse(opt)
        try:
            return float(val)
        except ValueError:
            raise ChordLibError(
                "bad float value for '%s' in section '%s': %s"
                    % (opt, self.item, val))

    def _parse_color(self, opt):
        col = self._parse(opt)

        # color like #FFF
        m = re.match('#([0-9a-fA-F]{3}$)', col)
        if m:
            return Color(*[int(c, 16) / 15. for c in m.group(1)])

        # color like #FFFFFF
        m = re.match('#([0-9a-fA-F]{6})$', col)
        if m:
            return Color(
                *[int(m.group(1)[c:c+2], 16) / 255. for c in (0,2,4)])

        # color by name
        rv = getattr(colors, col, None)
        if isinstance(rv, Color):
            return rv
        else:
            raise ChordLibError(
                "bad color in section '%s': %s"
                    % (self.item, col))

    def _parse_choices(self, opt, choices):
        val = self._parse(opt)
        if val.lower() in choices:
            return val.lower()
        else:
            raise ChordLibError(
                "bad value for '%s' in section %s: %s"
                    % (opt, self.item, val))

    def _parse_percent(self, opt):
        val = self._parse(opt)
        try:
            if '%' in val:
                return float(val.replace('%', '')) * 0.01
            else:
                return float(val)
        except ValueError:
            raise ChordLibError(
                "bad percent value for '%s' in section '%s': %s"
                    % (opt, self.item, val))

    def _parse_bool(self, opt):
        val = self._parse(opt)
        if val.lower() in ("1", "yes", "true", "on"):
            return True
        elif val.lower() in ("0", "no", "false", "off"):
            return False
        else:
            raise ChordLibError(
                "bad boolean value for '%s' in section '%s': %s"
                    % (opt, self.item, val))
