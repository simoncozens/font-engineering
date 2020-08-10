from collidoscope import Collidoscope
from vharfbuzz import Vharfbuzz
from fontTools.ttLib import TTFont
import sys
from argparse import ArgumentParser
import warnings
import re
from termcolor import colored
from stringbrewer import StringBrewer


parser = ArgumentParser(description="Shaping regression tests")
parser.add_argument("font", help="Font file", metavar="FONT")
parser.add_argument("testfile", help="File containing tests", metavar="TESTFILE")
args = parser.parse_args()

vhb = Vharfbuzz(args.font)
col = Collidoscope(
    args.font,
    {
        "cursive": True,
        "marks": True,
        "faraway": True,
        "adjacentmarks": False,
        "area": 0.01,
    },
)

tests = []
ingredients = []
seen_blank = False

with open(args.testfile, "r") as testfile:
    for line in testfile.read().split("\n"):
        if re.match(r"^\s*#", line):
            continue
        if line == "":
            seen_blank = True
        if seen_blank:
            ingredients.append(line)
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


def tfail(test, string, message):
    global tested
    tested += 1
    print(f"{colored('🗴 ', 'red')} '{string}' {message}")


def tpass(test, string, message):
    global tested
    global passed
    tested += 1
    passed += 1
    print(f"{colored('🗸 ', 'green')} '{string}' {message}")


def do_test(string, options):
    glyphs = col.get_glyphs(string)
    collisions = col.has_collisions(glyphs)
    if collisions:
        tfail(test, string, "overlap test")
    else:
        tpass(test, string, "overlap test")

    if len(test["options"]) > 0:
        expected = test["options"][0]
        # XXX


for test in tests:
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
