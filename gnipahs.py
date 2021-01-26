#!/usr/bin/env python3
from collidoscope import Collidoscope
from vharfbuzz import Vharfbuzz
from fontTools.ttLib import TTFont
import sys
from argparse import ArgumentParser
import warnings
import re
from termcolor import colored
from stringbrewer import StringBrewer
import os


parser = ArgumentParser(description="Shaping regression tests")
parser.add_argument("--show-all", help="Adding passing tests to output file", action="store_true")
parser.add_argument("font", help="Font file", metavar="FONT")
parser.add_argument("testfile", help="File containing tests", metavar="TESTFILE")
args = parser.parse_args()

vhb = Vharfbuzz(args.font)
col = Collidoscope(
    args.font,
    {
        #"cursive": True,
        "marks": True,
        "faraway": True,
        "adjacentmarks": False,
        # "area": 0,
    },
)

tests = []
ingredients = []
seen_blank = False
failed = []
general_options = {}

with open(args.testfile, "r") as testfile:
    for line in testfile.read().split("\n"):
        if re.match(r"^\s*#", line):
            continue
        if line == "":
            seen_blank = True
        if seen_blank:
            ingredients.append(line)
        elif line.startswith("["):
            m = re.match(r"^\[(\w+)=([^]]+)\]$",line)
            general_options[m[1]] = m[2]
        else:
            elements = line.split(":")
            if elements[0].startswith('"') and elements[0].endswith('"'):
                tests.append(
                    {
                        "type": "literal",
                        "string": elements[0][1:-1],
                        "options": elements[1:],
                    }
                )
            else:
                tests.append(
                    {"type": "pattern", "string": elements[0], "options": elements[1:]}
                )

tested = 0
passed = 0
failreport = []


def tfail(test, string, message):
    global tested
    global failed
    failed.append(string)
    tested += 1
    print(f"{colored('🗴 ', 'red')} '{string}' {message}")


def tpass(test, string, message):
    global tested
    global passed
    global failed
    if args.show_all:
        failed.append(string)
    tested += 1
    passed += 1
    # print(f"{colored('🗸 ', 'green')} '{string}' {message}")


def do_test(string, options):
    glyphs = col.get_glyphs(string)
    collisions = col.has_collisions(glyphs)
    if collisions:
        tfail(test, string, "overlap test")
    else:
        tpass(test, string, "overlap test")
    if "forbidden" in general_options:
        forbidden = general_options["forbidden"].split(",")
        glyphnames = [x["name"] for x in glyphs]
        if any(x in forbidden for x in glyphnames):
            tfail(test, string, "forbidden glyph")
        else:
            tpass(test, string, "forbidden glyphs")
    if len(test["options"]) > 0:
        buf = vhb.shape(string)
        expected = options[0]
        got = vhb.serialize_buf(buf)
        if expected == got:
            tpass(test, string, "shaping test")
        else:
            tfail(test, string, "shaping text: expected %s got %s" % (expected, got))


for test in tests:
    failed = []
    failreport.append( (test["string"], failed ))
    if test["type"] == "pattern":
        b = StringBrewer(from_string=test["string"] + "\n" + "\n".join(ingredients))
        try:
            for s in b.generate_all():
                do_test(s, test["options"])
        except Exception as e:
            for i in range(1, 1000):
                do_test(b.generate(), test["options"])
    if test["type"] == "literal":
        do_test(test["string"], test["options"])

print("\n%i tests, %i passed, %i failing" % (tested, passed, tested - passed))

slug = " \\qquad "
# All your failing tests as a PDF
with open("test-failures.sil", "w") as sil:
    sil.write(f"""\\begin{{document}}
\\font[filename="{args.font}"]

\\script[src=packages/linespacing]
\\set[parameter=linespacing.method,value=fixed]
\\set[parameter=linespacing.fixed.baselinedistance,value=3em]
""")

    for (string, failed) in failreport:
        sil.write("\\bigskip \\font[family=Gentium Plus]{%s}\\bigskip" % string)
        sil.write(slug.join(failed))
    sil.write(r"\end{document}")
os.system("sile test-failures.sil >/dev/null 2>/dev/null")
os.system("open test-failures.pdf")
