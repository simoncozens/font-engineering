"""A user-friendlier way to use Harfbuzz in Python."""

import uharfbuzz as hb
from fontTools.ttLib import TTFont
import re


class Vharfbuzz:
    def __init__(self, filename):
        """Opens a font file and gets ready to shape text."""
        self.filename = filename
        with open(self.filename, "rb") as fontfile:
            self.fontdata = fontfile.read()
        self.ttfont = TTFont(filename)
        self.glyphOrder = self.ttfont.getGlyphOrder()
        self.prepare_shaper()

    def prepare_shaper(self):
        face = hb.Face(self.fontdata)
        font = hb.Font(face)
        upem = face.upem
        font.scale = (upem, upem)
        hb.ot_font_set_funcs(font)
        self.hbfont = font

    def make_message_handling_function(self, buf, onchange):
        self.history = {"GSUB": [], "GPOS": []}
        self.lastLookupID = None

        def handle_message(msg, buf2):
            m = re.match("start lookup (\\d+)", msg)
            if m:
                lookupid = int(m[1])
                self.history[self.stage].append(self.serialize_buf(buf2))

            m = re.match("end lookup (\\d+)", msg)
            if m:
                lookupid = int(m[1])
                if self.serialize_buf(buf2) != self.history[self.stage][-1]:
                    onchange(self, self.stage, lookupid, self._copy_buf(buf2))
                self.history[self.stage].pop()
            if msg.startswith("start GPOS stage"):
                self.stage = "GPOS"

        return handle_message

    def shape(self, text, onchange=None):
        """Shapes a text

    This shapes a piece of text, return a uharfbuzz `Buffer` object.

    Additionally, if an `onchange` function is provided, this will be called
    every time the buffer changes *during* shaping, with the following arguments:

    - ``self``: the vharfbuzz object.
    - ``stage``: either "GSUB" or "GPOS"
    - ``lookupid``: the current lookup ID
    - ``buffer``: a copy of the buffer as a list of lists (glyphname, cluster, position)
    """

        self.prepare_shaper()
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        self.stage = "GSUB"
        if onchange:
            f = self.make_message_handling_function(buf, onchange)
            buf.set_message_func(f)
        hb.shape(self.hbfont, buf)
        self.stage = "GPOS"
        return buf

    def _copy_buf(self, buf):
        # Or at least the bits we care about
        outs = []
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            l = [self.glyphOrder[info.codepoint], info.cluster]
            if self.stage == "GPOS":
                l.append(pos.position)
            else:
                l.append(None)
            outs.append(l)
        return outs

    def serialize_buf(self, buf):
        """Returns the contents of the given buffer in a string format similar to
    that used by hb-shape."""
        outs = []
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            outs.append("%s=%i" % (self.glyphOrder[info.codepoint], info.cluster))
            if self.stage == "GPOS":
                outs[-1] = outs[-1] + "+%i" % (pos.position[2])
            if self.stage == "GPOS" and (pos.position[0] != 0 or pos.position[1] != 0):
                outs[-1] = outs[-1] + "@<%i,%i>" % (pos.position[0], pos.position[1])
        return "|".join(outs)
