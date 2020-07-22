from vharfbuzz import Vharfbuzz
from stringbrewer import StringBrewer
import argparse
import cairosvg
import imageio
import numpy as np


parser = argparse.ArgumentParser(description='Find differences between ot and CoreText')
parser.add_argument('font',
                    help='a font file')
parser.add_argument('recipe', help='a StringBrewer recipe file')

args = parser.parse_args()

ot_shaper = Vharfbuzz(args.font)
ct_shaper = Vharfbuzz(args.font)
ct_shaper.shapers = ["coretext"]

sb = StringBrewer(from_file = args.recipe)

def buffers_differ(buf1, buf2, tolerance =2):
    outs = []
    if len(buf1.glyph_infos) != len(buf2.glyph_infos): return True
    for info1, info2 in zip(buf1.glyph_infos, buf2.glyph_infos):
      if info1.codepoint != info2.codepoint: return True
      # if info1.cluster != info2.cluster: return True
    for pos1, pos2 in zip(buf1.glyph_positions, buf2.glyph_positions):
      if abs(pos1.position[0] - pos2.position[0]) > tolerance: return True
      if abs(pos1.position[1] - pos2.position[1]) > tolerance: return True
      if abs(pos1.position[2] - pos2.position[2]) > tolerance: return True
    return False

def pad_max_shape(arrays, before=None, after=1, value=0, tie_break=np.floor):
    shapes = np.array([x.shape for x in arrays])
    if before is not None:
        before = np.zeros_like(shapes) + before
    else:
        before = np.ones_like(shapes) - after
    max_size = shapes.max(axis=0, keepdims=True)
    margin = (max_size - shapes)
    pad_before = tie_break(margin * before.astype(float)).astype(int)
    pad_after = margin - pad_before
    pad = np.stack([pad_before, pad_after], axis=2)
    return [np.pad(x, w, mode='constant', constant_values=value) for x, w in zip(arrays, pad)]

def visual_diff(s1, buf1, s2, buf2):
  png1 = cairosvg.svg2png(bytestring=s1.buf_to_svg(buf1))
  png2 = cairosvg.svg2png(bytestring=s2.buf_to_svg(buf2))
  im1 = imageio.imread(png1).sum(axis=2)
  im2 = imageio.imread(png2).sum(axis=2)
  padded = pad_max_shape([im1,im2])
  diff = padded[0]-padded[1]
  total_diff = np.sum(np.abs(diff))
  return (total_diff / (im1.shape[0] * im1.shape[1]) * 100)

while True:
  text = sb.generate()
  ot_buf = ot_shaper.shape(text)
  ct_buf = ct_shaper.shape(text)
  ot = ot_shaper.serialize_buf(ot_buf)
  ct = ct_shaper.serialize_buf(ct_buf)
  if buffers_differ(ot_buf, ct_buf):
    vdiff = visual_diff(ot_shaper, ot_buf, ct_shaper, ct_buf)
    if vdiff > 0.05:
      print(f"Found a difference in {text} : (visual difference = {vdiff}%)")
      print(f"OT: {ot}")
      print(f"CT: {ct}\n")
