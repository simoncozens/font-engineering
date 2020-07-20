from rstr import xeger
import string
import re
import random


class StringBrewer(object):
    """docstring for StringBrewer"""

    def __init__(self, from_string=None, from_file=None, recipe=None, ingredients=None):
        if from_file:
            self.parse_recipe_file(from_file)
        elif from_string:
            self.parse_recipe_string(from_string)
        elif recipe and ingredients:
            self.recipe = recipe
            self.ingredients = ingredients
        else:
            raise ValueError(
                "Need to instantiate StringBrewer with file, string or recipe"
            )
        self._initialize()

    def _initialize(self):
        if len(self.ingredients.keys()) > 52:
            raise ValueError("Too many ingredients")
        self.regex = self.recipe
        self.ingredient_map = {}
        for i, k in enumerate(sorted(self.ingredients.keys(), key=lambda x: -len(x))):
            self.ingredient_map[string.ascii_letters[i]] = self.ingredients[k]
            self.regex = re.sub(f"\\b{k}\\b", string.ascii_letters[i], self.regex)
        self.regex = re.sub(r"\s", "", self.regex)

    def parse_recipe_file(self, filename):
        with open(filename, "r") as file:
            self.parse_recipe_string(file.read())

    def generate(self, min_length=0, max_length=None):
        attempts = 0
        while attempts < 100:
            trial = xeger(self.regex)
            attempts = attempts + 1
            if max_length and len(trial) > max_length:
                continue
            if min_length and len(trial) < min_length:
                continue
            break
        for k, v in self.ingredient_map.items():
            trial = re.sub(k, lambda _: random.choice(v), trial)
        return trial

    def parse_recipe_string(self, s):
        got_recipe = False
        self.ingredients = {}
        while len(s):
            s, sn = re.subn(r"^(\s+|#.*)", "", s)
            if sn:
                continue
            if not got_recipe:
                m = re.match(r"^(.*?)\s*$", s, flags=re.MULTILINE)
                if not m:
                    raise ValueError("Couldn't find recipe")
                self.recipe = m[1]
                got_recipe = True
                s = s[m.end() :]
                continue
            m = re.match(r"^(\w+)\s*=\s*(.*)\s*$", s, flags=re.MULTILINE)
            if not m:
                raise ValueError("Couldn't parse ingredients")
            s = s[m.end() :]
            self.ingredients[m[1]] = self.parse_ingredient(m[2])

    def parse_ingredient(self, ingredient):
        bits = re.split(r"\s+", ingredient)
        res = []
        for bit in bits:
            if bit in self.ingredients:
                res.extend(self.ingredients[bit])
            elif "-" in bit:
                range_begin, range_end = re.split("-", bit)
                if len(range_begin) > 1:
                    range_begin = int(range_begin, 16)
                else:
                    range_begin = ord(range_begin)
                if len(range_end) > 1:
                    range_end = int(range_end, 16)
                else:
                    range_end = ord(range_end)
                for x in range(range_begin, range_end + 1):
                    res.append(chr(x))
            else:
                if len(bit) > 1:
                    res.append(chr(int(bit, 16)))
                else:
                    res.append(bit)
        return res


if __name__ == "__main__":
    s = StringBrewer(
        from_string="""

# Generate random Telugu-like morphemes
(Base (Halant Base){0,2} TopPositionedVowel?){1,3}

Base = 0C15-0C28 0C2A-0C39
Halant = 0C4D
TopPositionedVowel = 0C46-0C48 0C4A-0C4C

    """
    )
    for _ in range(10):
        print(s.generate())
