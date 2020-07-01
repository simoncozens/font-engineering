import uharfbuzz as hb
from fontTools.ttLib import TTFont
import re

class Vharfbuzz:
  def __init__(self, filename):
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
    self.history = { "GSUB": [], "GPOS": [] }
    self.stage = "GSUB"
    self.lastLookupID = None
    def handle_message(msg, buf2):
      print(msg)
      m = re.match("start lookup (\\d+)", msg)
      if m:
        lookupid = int(m[1])
        self.history[self.stage].append(self._debug_buf(buf))

      m = re.match("end lookup (\\d+)", msg)
      if m:
        lookupid = int(m[1])
        if self._debug_buf(buf) != self.history[self.stage][-1]:
          onchange(self, self.stage, lookupid, self._copy_buf(buf))
        self.history[self.stage].pop()
      if msg.startswith("start GPOS stage"):
        self.stage = "GPOS"

    return handle_message

  def shape(self, text, onchange = None):
    self.prepare_shaper()
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    test = self.make_message_handling_function(buf, onchange)
    if onchange:
      buf.set_message_func(test)
    hb.shape(self.hbfont, buf)

  def _copy_buf(self, buf):
    # Or at least the bits we care about
    outs = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
      outs.append(
        (self.glyphOrder[info.codepoint],
         info.cluster,
         pos.position)
      )
    return outs

  def _debug_buf(self,buf):
    outs = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
      outs.append( "%s=%i" % (self.glyphOrder[info.codepoint], info.cluster))
      if pos.position[0] != 0 or pos.position[1] != 0:
        outs[-1] = outs[-1] + "<%i,%i>" % (pos.position[0],pos.position[1])
    return "|".join(outs)
