"""
Module to help transposing a song.

This file is part of chordlab.
"""

from . import chopro

import logging
logger = logging.getLogger('chordlib.script')

def xpose(token, shift):
    if not shift:
        return token
    if  isinstance(token, chopro.Define):
        logger.warn("can't shift a define yet")
    if not isinstance(token, chopro.Line):
        return token

    parts = []
    for i, x in enumerate(token.arg):
        if i % 2 == 0:
            parts.append(x)
        else:
            parts.append(shift_chord(x, shift))

    return chopro.Line(parts)


def shift_chord(chord, shift):
    if shift == 0:
        return chord

    for l in (2,1):
        if chord[:l] in positions:
            shifted = invpos[(positions[chord[:l]] + shift) % 12]
            return shifted + chord[l:]
    else:
        logger.warn("can't shift chord: %s", chord)
        return chord


invpos = dict(enumerate('A A# B C C# D D# E F F# G G#'.split()))
positions = dict((c, p) for (p, c) in invpos.iteritems())

shmap = dict(('CD', 'DE', 'FG', 'GA', 'AB'))
for chord in positions.keys():
    if chord[1:2] == '#':
        positions[shmap[chord[0]] + 'b'] = positions[chord]


