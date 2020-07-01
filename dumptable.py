from fontTools.ttLib import TTFont
import argparse
import sys

parser = argparse.ArgumentParser(description='Dump a sfnt table')
parser.add_argument('fontfile', metavar='FILE', help='font file')
parser.add_argument('table', metavar='TABLE', help='table to dump')

args = parser.parse_args()
font = TTFont(args.fontfile)
if not args.table in font:
	print("No table found in font")
	sys.exit(1)

sys.stdout.buffer.write(font[args.table].compile(font))
