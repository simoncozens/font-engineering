from glyphsLib import load
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform, Identity
import argparse
import os
from lxml import etree
import sys


def add_paths(layer, t, additional_transform=Identity):
    commands = ""
    for p in layer.paths:
        svgpen = SVGPathPen(None)
        transformpen = TransformPen(svgpen, t)
        componenttransformpen = TransformPen(transformpen, additional_transform)
        p.draw(componenttransformpen)
        commands += svgpen.getCommands()
    return commands


def write_glyph(dir, font, glyph, master_id):
    if glyph not in font.glyphs:
        print("Unknown glyph %s" % glyph)
        return
    print(glyph)

    if master_id is None:
        master_id = 0
    master = font.masters[master_id]
    layer = font.glyphs[glyph].layers[master.id]
    svg = etree.Element(
        "svg",
        width=str(layer.width),
        height=str(master.ascender - master.descender),
        xmlns="http://www.w3.org/2000/svg",
    )
    et = etree.ElementTree(svg)

    t = Identity.scale(1, -1).translate(0, -master.ascender)
    commands = add_paths(layer, t)

    # Components
    for c in layer.components:
        comp_layer = font.glyphs[c.name].layers[master.id]
        commands += add_paths(comp_layer, t, c.transform)

    svg_path = etree.fromstring(f'<path d="{commands}" />')
    svg.append(svg_path)

    et.write("%s/%s.svg" % (dir, glyph), pretty_print=True)


parser = argparse.ArgumentParser(description="Convert Glyphs file to SVG files")
parser.add_argument("--output-dir", metavar="DIRECTORY")
parser.add_argument("--master", help="Master name for .glyphs fonts", metavar="MASTER")
parser.add_argument("file", metavar="SOURCE")
parser.add_argument("glyph", metavar="GLYPH", nargs="*")

args = parser.parse_args()
gsfont = load(open(args.file))

output_dir = args.output_dir
if not output_dir:
    output_dir, _ = os.path.splitext(args.file)

print("Writing SVG files to %s" % output_dir)

if not os.path.exists(output_dir):
    os.mkdir(output_dir)

master_id = 0
if args.master:
    for master in gsfont.masters:
        if master.name == args.master:
            master_id = master.id
            break
    if not master_id:
        print(
            "Can't find master '%s' (Try one of %s)"
            % (master_id, ", ".join([x.name for x in font.masters]))
        )
        sys.exit(1)

if args.glyph:
    for g in args.glyph:
        write_glyph(output_dir, gsfont, g, master_id)
else:
    for g in gsfont.glyphs:
        write_glyph(output_dir, gsfont, g.name, master_id)
