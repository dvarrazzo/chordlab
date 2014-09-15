"""
Base songsheet renderer class.

This file is part of chordlab.
"""

import re
from collections import OrderedDict

import logging
logger = logging.getLogger("chordlib.render")

class SongsRenderer(object):
    """Handle rendering tokens received by a parser"""
    def __init__(self):
        self.filename = None
        self.knownchords = {}
        self.localchords = {}
        self.usedchords = OrderedDict()

    def new_song(self, filename):
        self.filename = filename
        self.localchords = {}

    def define_chord(self, name, args):
        def string_value(v):
            if v in ('-', 'X', 'x'):
                return None
            else:
                return int(v)

        if args[0] == 'base-fret' and args[2] == 'frets':
            base_fret = int(args[1])
            self.localchords[name] = [base_fret] + map(string_value, args[3:])
        else:
            logger.warn("Bad chorddef " + name + ": " + str(args))

    def use_chord(self, chord):
        chord = re.sub('\s*\(.*\)', '', chord)      # strip (parens)
        chord = re.sub('(\s*/\s*)*$', '', chord)    # strip trailing / / /
        if not (chord in ['N.C.', '%', '-', ''] or chord in self.usedchords):
            self.usedchords[chord] = True
            if not (chord in self.knownchords or chord in self.localchords):
                logger.warn("Unknown chord: %s", chord)

    def end_of_input(self):
        pass

    def handle_token(self, token):
        meth = 'handle_' + token.__class__.__name__
        meth = getattr(self, meth, None)
        if meth is None:
            meth = self.handle_unknown
        meth(token)

    def handle_unknown(self, token):
        logger.warn("%s can't handle %r", self.__class__.__name__, token)

    def handle_SourceComment(self, token):
        pass
