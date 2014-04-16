"""
chopro format parser

This file is part of chordlab.
"""

import re
import codecs

import logging
logger = logging.getLogger('chordlib.chopro')

class Token(object):
    def __init__(self, arg):
        self.arg = self.parse_arg(arg)

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.arg)

    def parse_arg(self, arg):
        return arg

class NoArg(object):
    def parse_arg(self, arg):
        if arg:
            logger.warn('statement %s expects no arg, got %s',
                self.__class__.__name__, arg)
        return None

class IntArg(object):
    def parse_arg(self, arg):
        try:
            return int(arg)
        except ValueError:
            raise ChoProParser.ParseError(
                'statement %s expects an integer, got %s'
                % (self.__class__.__name__, arg))

class ListArg(object):
    def parse_arg(self, arg):
        return arg.split()

class Title(Token): pass
class SubTitle(Token): pass
class Comment(Token): pass
class StartOfChorus(NoArg, Token): pass
class EndOfChorus(NoArg, Token): pass
class StartOfTab(NoArg, Token): pass
class EndOfTab(NoArg, Token): pass
class Columns(IntArg, Token): pass
class ColumnBreak(NoArg, Token): pass
class NewPage(NoArg, Token): pass
class NewSong(NoArg, Token): pass
class Define(ListArg, Token): pass
class NoGrid(NoArg, Token): pass
class Blank(NoArg, Token): pass
class SourceComment(Token): pass
class TabLine(Token): pass
class Line(Token): pass


statements = {
    'title': Title,
    'subtitle': SubTitle,
    'comment': Comment,
    'start_of_chorus': StartOfChorus,
    'end_of_chorus': EndOfChorus,
    'start_of_tab': StartOfTab,
    'end_of_tab': EndOfTab,
    'columns': Columns,
    'column_break': ColumnBreak,
    'new_page': NewPage,
    'new_song': NewSong,
    'define': Define,
    'no_grid': NoGrid,
}

aliases = {
    't': 'title',
    'st': 'subtitle',
    'c': 'comment',
    'ci': 'comment',
    'soc': 'start_of_chorus',
    'eoc': 'end_of_chorus',
    'sot': 'start_of_tab',
    'eot': 'end_of_tab',
    'col': 'columns',
    'cols': 'columns',
    'colb': 'column_break',
    'np': 'new_page',
    'ng': 'no_grid',
}
for k, v in aliases.iteritems():
    statements[k] = statements[v]


class ChoProParser(object):
    """Parse a chopro file into a sequence of tokens"""

    class ParseError(Exception):
        pass

    def __init__(self, default_encoding='utf-8'):
        self.default_encoding = default_encoding

    def open_file(self, fn):
        # Check the two first lines for an encoding mark!
        f = open(fn)
        coding = re.search(r'-\*- +(en)?coding: (?P<c>[a-z0-9_-]+) +-\*-', 
                           f.readline() + f.readline())
        f.close()
        enc = coding.group('c') if coding else self.default_encoding
        return codecs.open(fn, 'r', enc)


    def parse_file(self, f):
        if isinstance(f, basestring):
            f = self.open_file(f)

        stmt_re = re.compile('\s*{([a-z_]+)(:? *(.*))?}\s*', re.I)
        chord_re = re.compile('\[([^]]*)\]')
        tabmode = False

        for line in f:
            line = line.rstrip()
            m = stmt_re.match(line)
            if m:
                try:
                    cls = statements[m.group(1).lower()]
                except KeyError:
                    logger.warn("Unknown statement: " + m.group(1) + " param: " + str(m.group(3)))
                    continue

                if cls is StartOfTab:
                    if not tabmode:
                        self.tabmode = True
                    else:
                        logger.warn("Ignoring unmatched start_of_tab")
                        continue

                elif cls is EndOfTab:
                    if tabmode:
                        self.tabmode = False
                    else:
                        logger.warn("Ignoring unmatched end_of_tab")
                        continue

                stmt = cls(m.group(3))
                yield stmt


            elif not line:
                yield Blank(None)
            
            elif line.lstrip().startswith('#'):
                yield SourceComment(line.split('#', 1)[1].lstrip())
            
            elif tabmode:
                yield TabLine(line)

            else:
                parts = chord_re.split(line)
                yield Line(parts)
