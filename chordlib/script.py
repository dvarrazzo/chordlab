"""
Main script and command line parsing.

This file is part of chordlab.
"""

import sys
from copy import copy
from optparse import Option, OptionValueError, OptionParser

from . import consts
from . import guitar
from .canvas import CanvasAdapter
from .chopro import ChoProParser
from .error import ChordLibError
from .pdf import PdfSongsRenderer

import logging
logger = logging.getLogger('chordlib.script')

def script():
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s %(message)s')

    try:
        sys.exit(main())

    except ChordLibError, e:
        logger.error("%s", e)
        sys.exit(1)

    except Exception:
        logger.exception("unexpected error")
        sys.exit(1)

    except KeyboardInterrupt:
        logger.info("user interrupt")
        sys.exit(1)


def main():
    opt = make_option_parser()
    (options, sourcefiles) = opt.parse_args()

    # TODO: per-renderer config
    c = CanvasAdapter(options.output, showfilenames=options.showfiles,
                      pagesize=options.pagesize,
                      title=options.doctitle, author=options.docauthor)
    r = PdfSongsRenderer(c)
    if options.styles:
        r.style.read(*options.styles)
    r.disable_compact = options.disable_compact

    # TODO: ukulele!
    r.knownchords = guitar.knownchords

    p = ChoProParser(default_encoding='latin1') # bad choice
    for fn in sourcefiles:
        r.new_song(fn)
        try:
            for token in p.parse_file(fn):
                r.handle_token(token)
        except p.ParseError, e:
            logger.error("error parsing file '%s': %s", fn, e)
            return 1

    r.draw_chord_boxes()
    r.end_of_input()


def get_unit_factor(name, default=1):
    from reportlab.lib.units import toLength
    if name:
        return toLength('1' + name)
    else:
        return default

def get_page_size(descr):
    import reportlab.lib.pagesizes
    if descr.upper() in dir(reportlab.lib.pagesizes):
        return reportlab.lib.pagesizes.__getattribute__(descr.upper())
    else:
        import re
        unit = '(cm|in|pt|i|mm|pica)'
        pformat = re.compile("^(\d+) ?"+unit+"? ?(x|by)(\d+) ?"+unit+"?$")
        m = pformat.match(descr)
        if m:
            yunit = get_unit_factor(m.group(5))
            xunit = get_unit_factor(m.group(2), default=yunit)
            return (float(m.group(1))*xunit, float(m.group(4))*yunit)
        else:
            return None

def check_page_size(option, opt, value):
    result = get_page_size(value)
    if result != None:
        return result
    else:
        raise OptionValueError("option %s: invalid page size: %r"
                               % (opt, value))

class MyOption(Option):
    """Option class with common option support and an added pagesize type"""
    TYPES = Option.TYPES + ("pagesize",)
    TYPE_CHECKER = copy(Option.TYPE_CHECKER)
    TYPE_CHECKER["pagesize"] = check_page_size


description = """Takes a set of chopro files and converts them to a single
pdf file.  If no file names are given as arguments, a single chopro files
is read from stdin.  Chopro files is simply text files with chord names in
brackets and some other options in braces, on separate lines."""

def make_option_parser():
    opt = OptionParser(usage="usage: %prog [options] file.chopro ...",
                       version="%prog " + consts.version + " by " + consts.author,
                       description=description,
                       epilog=consts.license + '\n\n' + consts.progurl,
                       option_class=MyOption)
    opt.add_option("-o", "--output", dest="output", default="chords.pdf",
                   help="output file to write [default: %default]", metavar="FILE")
    opt.add_option("-p", "--pagesize", dest="pagesize", type="pagesize",
                   default="A4", metavar="SZ",
                   help="output page size, name or dimensions [default: %default]")
    opt.add_option("--style", dest="styles", action="append",
                   help="use this style sheet (can be used more than once)")
    opt.add_option("--title", dest="doctitle", metavar="TITLE",
                   help="document title to put in PDF metadata")
    opt.add_option("--author", dest="docauthor", metavar="AUTHOR",
                   help="author name/address to put in PDF metadata")
    opt.add_option("--showfilenames",
                   action="store_true", dest="showfiles", default=False,
                   help="Show source filenames in output")
    opt.add_option("--no-compact",
                   action="store_true", dest="disable_compact", default=False,
                   help="Make place for chords even on lines w/o chords")
    return opt
