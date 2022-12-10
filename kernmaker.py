from collections import defaultdict
import argparse
import random
import sys

parser = argparse.ArgumentParser(
    description="Turn a wordlist into a set of kerning words"
)
parser.add_argument(
    "--alphabet",
    help="which letters we care about (default: all letters in the wordlist)",
)
parser.add_argument(
    "--separate-sides",
    "-s",
    action="store_true",
    help="List words with the character of interest on the left and words"
    " with the character on the right separately",
)

parser.add_argument("wordlist", metavar="FILE", help="the wordlist file")

args = parser.parse_args()

try:
    fh = open(args.wordlist)
except Exception as e:
    print(f"Couldn't open wordlist: {e}")
    sys.exit(1)

all_letters = set()
ngrams = defaultdict(set)
for word in fh:
    word = word.rstrip()
    for i in range(max(1, len(word) - 1)):
        ngrams[word[i : i + 2]].add(word)
    all_letters.update(word)

if not args.alphabet:
    args.alphabet = all_letters

for first in sorted(args.alphabet):
    if args.separate_sides:
        line1 = [first + "+"]
        line2 = ["+" + first]
    else:
        line1 = [first]
        line2 = line1
    for second in sorted(args.alphabet):
        candidates = ngrams.get(first + second)
        if candidates:
            line1.append(random.choice(list(candidates)))
        if first == second:
            continue
        candidates = ngrams.get(second + first)
        if candidates:
            line2.append(random.choice(list(candidates)))
    if args.separate_sides:
        line1.append(first + "+")
        print(" ".join(line1))
        line2.append("+" + first)
        print(" ".join(line2))
    else:
        line1.append(first)
        print(" ".join(line1))
