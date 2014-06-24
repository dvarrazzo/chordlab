"""
Rendering of songs in pdf

This file is part of chordlab.
"""

from collections import OrderedDict
from .render import SongsRenderer
from . import style

class PdfSongsRenderer(SongsRenderer):
    def __init__(self, canvas):
        super(PdfSongsRenderer, self).__init__()

        # config
        self.disable_compact = False
        self.style = style.get_base_stylesheet()

        self.canvas = canvas
        self.xpos = self.ypos = self.colw = None
        self.tabmode = False
        self.skip_grid = False
        self.in_chorus = False
        self.socpos = [0,0]
        self.colstart = 0
        self.pageno = 0

    def new_song(self, filename):
        super(PdfSongsRenderer, self).new_song(filename)
        if self.pageno:
            self.draw_chord_boxes()
        self.xpos, self.ypos = self.newPage(filename)
        self.colw = self.canvas.get_right() # Any large number, really

    def column_break(self):
        in_chorus = self.in_chorus
        if in_chorus:
            self.handle_EndOfChorus(None)
        self.ypos = self.colstart
        self.xpos += self.colw
        if (self.xpos + 1 > self.canvas.get_right()):
            self.xpos, self.ypos = self.newPage(self.filename)
        if in_chorus:
            self.handle_StartOfChorus(None)

    def draw_chord_boxes(self):
        if self.skip_grid:
            self.skip_grid = False
            return

        style = self.style['chordbox']
        self.canvas.saveState()
        boxw = 38
        xpos = (self.canvas.get_right()) / style.scale - boxw + 10
        ypos = (self.canvas.get_bottom()) / style.scale + 8
        self.canvas.scale(style.scale, style.scale)
        for cname in reversed(self.usedchords):
            chord = self.localchords.get(cname) or self.knownchords.get(cname)
            if not chord:
                continue
            self.draw_chord_box(xpos, ypos, cname, chord)
            xpos -= boxw
            if xpos < self.canvas.get_left():
                xpos = self.canvas.get_right() - boxw + 10
                ypos += 55
        self.usedchords = OrderedDict()
        self.canvas.restoreState()

    def draw_chord_box(self, xpos, ypos, cname, chord):
        nstrings = len(chord) - 1
        dx = 5 * 6 / nstrings
        dy = 7

        self.canvas.saveState()
        clip = self.canvas.beginPath()
        clip.moveTo(xpos - dx,   ypos - dy/2)
        clip.lineTo(xpos + nstrings*dx, ypos - dy/2)
        clip.lineTo(xpos + nstrings*dx, ypos + 4*dy + 1)
        clip.lineTo(xpos - dx,   ypos + 4*dy + 1)
        clip.close()
        self.canvas.clipPath(clip, stroke=0)            # clipPath

        self.canvas.setLineWidth(0.3)
        self.canvas.grid(
            [xpos + dx*x for x in range(nstrings)],
            [ypos + dy*y for y in range(-1, 6)])
        self.canvas.restoreState()

        self.canvas.setFont("Helvetica-Oblique", 10)
        self.canvas.drawCentredString(
            xpos + dx * 0.5 * (nstrings - 1), ypos + 5.1 * dy, cname)

        self.canvas.setFont("Helvetica", 7)
        if chord[0] > 1: # bare
            self.canvas.drawRightString(
                xpos - 2.0 * dx / 5, ypos + 3 * dy + 1, str(chord[0]))
        else:
            self.canvas.setLineWidth(1)
            self.canvas.line(
                xpos, ypos + 4 * dy + 0.5,
                xpos + (nstrings - 1) * dx, ypos + 4 * dy + 0.5)
        x = xpos

        self.canvas.setLineWidth(0.5)
        for string in chord[1:]:
            if string == None:
                self.canvas.line(
                    x - 1.8, ypos + 4.5 * dy - 1.8,
                    x + 1.8, ypos + 4.5 * dy + 1.8)
                self.canvas.line(
                    x + 1.8, ypos + 4.5 * dy - 1.8,
                    x - 1.8, ypos + 4.5 * dy + 1.8)
            elif string == 0:
                self.canvas.circle(
                    x, ypos + (4.5 - string) * dy, 1.8,
                    stroke=1, fill=0)
            else:
                self.canvas.circle(
                    x, ypos + (4.5 - string) * dy, 2,
                    stroke=0, fill=1)

            x += dx

    def end_of_input(self):
        super(PdfSongsRenderer, self).end_of_input()
        self.canvas.showPage()
        self.canvas.save()


    def handle_Title(self, token):
        self._draw_title('title', token.arg)

    def handle_SubTitle(self, token):
        self._draw_title('subtitle', token.arg)

    def _draw_title(self, style_name, text):
        style = self.style[style_name]
        self._set_font(self.canvas, style)
        self.canvas.setFillColor(style.color)
        self.ypos -= style.line_height
        self.canvas.draw_aligned_string(style.align, self.ypos, text)

    def handle_Comment(self, token):
        style = self.style['comment']
        self._set_font(self.canvas, style)
        self.canvas.setFillColor(style.color)
        self.ypos -= style.line_height
        self.canvas.drawString(self.xpos, self.ypos, token.arg)

    def handle_StartOfChorus(self, token):
        self.in_chorus = True
        self.socpos = [self.xpos-5, self.ypos]
        self.xpos += self.style['chorus'].indent

    def handle_EndOfChorus(self, token):
        self.xpos -= self.style['chorus'].indent
        # TODO: box etc.
        self.canvas.line(self.socpos[0], self.socpos[1],
                         self.xpos-5, self.ypos-5)
        self.in_chorus = False

    def handle_StartOfTab(self, token):
        style = self.style['tab']
        self._set_font(self.canvas, style)
        self.tabmode = True

    def handle_EndOfTab(self, token):
        self.tabmode = False

    def handle_Columns(self, token):
        self.colw = (self.canvas.get_right() - self.canvas.get_left()) \
                / token.arg
        self.colstart = self.ypos
        # print "Pagew:", A4[0] - 2*margin, "cols:", coln, "colw:", colw

    def handle_ColumnBreak(self, token):
        self.column_break()

    def handle_NewPage(self, token):
        self.xpos,self.ypos = self.newPage(self.filename)

    def handle_NewSong(self, token):
        self.new_song(self.filename)

    def handle_Define(self, token):
        self.define_chord(token.arg[0], token.arg[1:])

    def handle_NoGrid(self, token):
        self.skip_grid = True

    def handle_Blank(self, token):
        style = self.style['blank']
        self.ypos -= style.line_height

    def handle_TabLine(self, token):
        style = self.style['tab']
        self._set_font(self.canvas, style)
        self.canvas.setFillColor(style.color)
        h = style.line_height
        if self.ypos < self.canvas.get_bottom() + (h * 1.33):
            self.column_break()
        self.ypos -= h
        self.canvas.drawString(self.xpos, self.ypos, token.arg)

    def handle_Line(self, token):
        sl = self.style['line']
        sc = self.style['chord']

        if self.ypos < self.canvas.get_bottom() \
                + (sl.line_height + sc.line_height) * 1.1:
            self.column_break()

        parts = token.arg

        for txt in parts[::2]:
            if txt and not txt.isspace():
                only_chords = False
                break
        else:
            only_chords = True

        if not only_chords and (self.disable_compact or len(parts) > 1):
            self.ypos -= sl.line_height + sc.line_height
        else:
            self.ypos -= sl.line_height

        to = self.canvas.beginText(self.xpos, self.ypos)
        ischord = 0
        if not only_chords:
            okpos = 0
            for i, x in enumerate(parts):
                if ischord:
                    self.use_chord(x)

                    # fill with dots but only in the middle of a word
                    csp = to.getCursor()
                    if i + 1 < len(parts) \
                            and (not parts[i+1] or parts[i+1].isspace()):
                        cfill = ' '
                    else:
                        cfill = u'\u00B7'

                    while csp[0] < okpos:
                        to.textOut(cfill)
                        csp = to.getCursor()
                    self._set_font(to, sc)
                    to.setRise(sc.rise)
                    to.setFillColor(sc.color)
                else:
                    self._set_font(to, sl)
                    to.setRise(0)
                    to.setFillColor(sl.color)
                to.textOut(x)
                if ischord:
                    okpos = to.getCursor()[0] + 3
                    to.setTextOrigin(csp[0], csp[1])
                ischord = not ischord

        else:
            for x in parts:
                if ischord:
                    self.use_chord(x)
                    to.setFont(sc.font, sl.font_size)
                    to.setFillColor(sc.color)
                else:
                    self._set_font(to, sl)
                    to.setFillColor(sl.color)
                to.textOut(x)
                ischord = not ischord

        self.canvas.drawText(to)

    def _set_font(self, obj, style):
        obj.setFont(style.font, style.font_size)

    def newPage(self, filename):
        canvas = self.canvas

        if self.pageno > 0: canvas.showPage()
        self.pageno += 1

        ss = self.style['songsheet']
        sp = self.style['page-number']

        canvas.top = canvas.pagesize[1] - ss.margin_top
        canvas.bottom = ss.margin_bottom

        if ss.duplex and (self.pageno % 2 == 1):
            canvas.left = ss.margin_left + ss.margin_gutter
            canvas.right = canvas.pagesize[0] \
                    - (ss.margin_right - ss.margin_gutter)

            if sp.display:
                self._set_font(self.canvas, sp)
                canvas.drawRightString(canvas.right, canvas.bottom - 9,
                    str(self.pageno))
        else:
            canvas.left = ss.margin_left - ss.margin_gutter
            canvas.right = canvas.pagesize[0] \
                - (ss.margin_right + ss.margin_gutter)

            if sp.display:
                self._set_font(self.canvas, sp)
                canvas.drawString(canvas.left, canvas.bottom - 9,
                    str(self.pageno))

        canvas.line(canvas.left, canvas.top,
            canvas.right, canvas.top)
        canvas.line(canvas.left, canvas.bottom,
            canvas.right, canvas.bottom)

        if canvas.showfilenames:
            canvas.setFont('Helvetica', 8)
            if ss.duplex and (self.pageno % 2 == 1):
                canvas.drawString(canvas.left, canvas.bottom - 9, filename)
            else:
                canvas.drawRightString(canvas.right, canvas.bottom - 9, filename)

        return (canvas.left, canvas.top)

