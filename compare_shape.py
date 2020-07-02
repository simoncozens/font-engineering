import uharfbuzz as hb
from fontTools.ttLib import TTFont
import sys
from argparse import ArgumentParser
import warnings

parser = ArgumentParser(description="Compare shaping results for two fonts")
parser.add_argument("file1", help="First font to compare", metavar="FILE1")
parser.add_argument("file2", help="Second font to compare", metavar="FILE2")
parser.add_argument("wordlist", help="File containing words", metavar="WORDLIST")
parser.add_argument(
    "--ignorables",
    help="Glyph names to ignore in output (comma separated)",
    metavar="GLYPHS",
)
parser.add_argument(
    "--features",
    help="OpenType feature string (+xxxx, -xxxx, comma separated)",
    metavar="FEATURES",
)
args = parser.parse_args()

ignorables = []
if args.ignorables:
    ignorables = args.ignorables.split(",")

features = {}
if args.features:
    for f in args.features.split(","):
        if f[0] == "+":
            features[f[1:]] = True
        elif f[0] == "-":
            features[f[1:]] = True
        else:
            warnings.warn("Unable to parse feature '%s'" % f)


def shaping_string(fontdata, glyphOrder, text, language=None):
    face = hb.Face(fontdata)
    font = hb.Font(face)
    upem = face.upem
    font.scale = (upem, upem)
    hb.ot_font_set_funcs(font)

    buf = hb.Buffer()

    buf.add_str(text)
    buf.guess_segment_properties()
    if language:
        buf.language = language

    features = {"kern": True, "liga": True}
    hb.shape(font, buf, features)

    infos = buf.glyph_infos
    positions = buf.glyph_positions
    outs = []
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        name = glyphOrder[info.codepoint]
        if name in ignorables:
            continue
        outs.append("%s=%i" % (name, info.cluster))
        if pos.position[0] != 0 or pos.position[1] != 0:
            outs[-1] = outs[-1] + "<%i,%i>" % (pos.position[0], pos.position[1])
    return "|".join(outs)


font1 = TTFont(args.file1)
font2 = TTFont(args.file2)

with open(args.file1, "rb") as fontfile:
    fontdata1 = fontfile.read()
with open(args.file2, "rb") as fontfile:
    fontdata2 = fontfile.read()
with open(args.wordlist, "r") as wordlist:
    test_strings = wordlist.read().split()

tested = 0
passed = 0
for test in test_strings:
    ss1 = shaping_string(fontdata1, font1.getGlyphOrder(), test)
    ss2 = shaping_string(fontdata2, font2.getGlyphOrder(), test)
    tested += 1
    if ss1 == ss2:
        passed += 1
    else:
        print("Shaping %s" % test)
        print("With %s: %s" % (args.file1, ss1))
        print("With %s: %s\n" % (args.file2, ss2))

print("\n%i tests, %i passed, %i failing" % (tested, passed, tested - passed))
