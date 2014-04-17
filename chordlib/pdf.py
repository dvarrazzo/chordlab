"""
Rendering of songs in pdf

This file is part of chordlab.
"""

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
        self.usedchords = set()
        self.socpos = [0,0]
        self.colstart = 0

    def new_song(self, filename):
        super(PdfSongsRenderer, self).new_song(filename)
        self.draw_chord_boxes()
        self.xpos, self.ypos = self.canvas.newPage(filename)
        self.colw = self.canvas.get_right() # Any large number, really

    def column_break(self):
        self.ypos = self.colstart
        self.xpos += self.colw
        if (self.xpos + 1 > self.canvas.get_right()):
            self.xpos, self.ypos = self.canvas.newPage(self.filename)

    def draw_chord_boxes(self) :
        if self.skip_grid:
            self.skip_grid = False
            return

        boxw = 38
        xpos = self.canvas.get_right() - boxw + 10
        ypos = self.canvas.get_bottom() + 8
        for chord in reversed(sorted(self.usedchords)):
            self.draw_chord_box(xpos, ypos, chord)
            xpos -= boxw
            if xpos < self.canvas.get_left():
                xpos = self.canvas.get_right() - boxw + 10
                ypos += 55
        self.usedchords = set()

    def draw_chord_box(self, xpos, ypos, chord):
        dx = 5
        dy = 7

        self.canvas.saveState()
        clip = self.canvas.beginPath()
        clip.moveTo(xpos - dx,   ypos - dy/2)
        clip.lineTo(xpos + 6*dx, ypos - dy/2)
        clip.lineTo(xpos + 6*dx, ypos + 4*dy + 1)
        clip.lineTo(xpos - dx,   ypos + 4*dy + 1)
        clip.close()
        self.canvas.clipPath(clip, stroke=0)            # clipPath

        self.canvas.setLineWidth(0.3)
        self.canvas.grid([xpos + dx*x for x in range(6)], [ypos + dy*y for y in range(-1, 6)])
        self.canvas.restoreState()

        self.canvas.setFont("Helvetica-Oblique", 10)
        self.canvas.drawCentredString(xpos + dx*2.5, ypos + 5.1*dy, chord)

        the_chord = self.localchords.get(chord) or self.knownchords.get(chord)

        if the_chord != None:
            self.canvas.setFont("Helvetica", 7)
            if the_chord[0] > 1: # bare
                self.canvas.drawRightString(xpos-2.0*dx/5, ypos + 3*dy+1, str(the_chord[0]))
            else:
                self.canvas.setLineWidth(1)
                self.canvas.line(xpos, ypos+4*dy+0.5, xpos + 5*dx, ypos+4*dy+0.5)
            x = xpos
            for string in the_chord[1:]:
                if string == None:
                    self.canvas.drawCentredString(x, ypos + 4*dy + 1.7, 'x')
                elif string == 0:
                    self.canvas.drawCentredString(x, ypos + 4*dy + 1.7, 'o')
                else:
                    self.canvas.circle(x, ypos + (4.5-string)*dy, 2.0*dx/5, stroke=0, fill=1)

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
        self.canvas.setFont(style.font, style.size)
        self.canvas.setFillColor(style.color)
        self.ypos -= style.line_height
        self.canvas.draw_aligned_string(style.align, self.ypos, text)

    def handle_Comment(self, token):
        style = self.style['comment']
        self.canvas.setFont(style.font, style.size)
        self.canvas.setFillColor(style.color)
        self.ypos -= style.line_height
        self.canvas.drawString(self.xpos, self.ypos, token.arg)

    def handle_StartOfChorus(self, token):
        self.socpos = [self.xpos-5, self.ypos]
        self.xpos += self.style['chorus'].indent

    def handle_EndOfChorus(self, token):
        self.xpos -= self.style['chorus'].indent
        # TODO: box etc.
        self.canvas.line(self.socpos[0], self.socpos[1],
                         self.xpos-5, self.ypos-5)

    def handle_StartOfTab(self, token):
        style = self.style['tab']
        self.canvas.setFont(style.font, style.size)
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
        self.xpos,self.ypos = self.canvas.newPage(self.filename)

    def handle_NewSong(self, token):
        self.new_song(self.filename)

    def handle_Define(self, token):
        self.define_chord(token.arg)

    def handle_NoGrid(self, token):
        self.skip_grid = True

    def handle_Blank(self, token):
        style = self.style['blank']
        self.ypos -= style.line_height

    def handle_TabLine(self, token):
        style = self.style['tab']
        self.canvas.setFont(style.font, style.size)
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
        if self.disable_compact or len(parts) > 1:
            self.ypos -= sl.line_height + sc.line_height
        else:
            self.ypos -= sl.line_height

        to = self.canvas.beginText(self.xpos, self.ypos)
        ischord = 0
        okpos = 0
        for x in parts:
            if ischord :
                self.use_chord(x)
                csp = to.getCursor()
                while csp[0] < okpos :
                    to.textOut(u'\u00B7')
                    csp = to.getCursor()
                to.setFont(sc.font, sc.size)
                to.setRise(sc.rise)
                to.setFillColor(sc.color)
            else:
                to.setFont(sl.font, sl.size)
                to.setRise(0)
                to.setFillColor(sl.color)
            to.textOut(x)
            if ischord :
                okpos = to.getCursor()[0] + 3
                to.setTextOrigin(csp[0], csp[1])
            ischord = not ischord
        self.canvas.drawText(to)
