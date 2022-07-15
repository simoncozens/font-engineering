# Font engineering tools

This repository contains a number of smaller scripts and libraries that I find useful in my font engineering work and don't want to keep to myself.

## [`shape`](./shape)

This is a simple wrapper for `hb-shape` and `hb-view`, but I use it _all the
time_ - like, _hundreds_ of times a day. You will need to either be using
[iTerm2](https://www.iterm2.com/index.html) for your terminal and install the
[shell integration](https://www.iterm2.com/documentation-shell-integration.html)
tools so that it can display images inline, or [Kovid Goyal's TTY,
`kitty`](https://github.com/kovidgoyal/kitty). Once you've done that, use
`shape <fontfile> <text>` to display both the shaped glyph string and the
output image in your termal. You can also pass any command line arguments that
make sense to `hb-shape` or `hb-view`: `-V` to get a shaping trace,
`--features=...` and so on:

![](shape.png)

Top tip: if you're using `zsh` for your shell, add this to your `.zshrc` and you will be able to tab-complete font files:

    compdef '_files -g "*.?tf"' shape

## [`gimmesometext`](./gimmesometext)

I often need sample text in lots of different scripts and languages. I
want to be able to say "give me a bunch of Tamil strings", and this does
just that:

    $ gimmesometext --script=Taml # ISO 15924 script code
    $ gimmesometext --script=tml2 # OpenType script code
    $ gimmesometext ta # ISO 639-1 language code

    $ gimmesometext --script=Cyrl az # Filter by script and language
    $ gimmesometext --script=Arab az # Filter by script and language

## [`interrofont`](./interrofont)

General purpose tool for investigating OTF/TTF information from the command line. See http://www.corvelsoftware.co.uk/software/interrofont/ for usage.

## [`otfsurgeon`](./otfsurgeon)

General purpose tool for slicing and dicing OTF/TTF binary table data. Like
[`dumptable`](./dumptable) but more so:

```shell
otfsurgeon -i f.ttf dump --ttx name # Dumps name table as XML to stdout
otfsurgeon -i f.ttf dump name > name.bin # Dumps name table as binary to stdout

otfsurgeon -i f2.ttf add name < name.bin # Adds the name table from stdin

otfsurgeon -i f.ttf strip Debg DSIG # Removes the Debg and DSIG tables from the font

otfsurgeon -i f.ttf steal f2.ttf DSIG # Copies the DSIG table from f2.ttf
```

## [`fontshell`](./fontshell)

Sometimes you need to poke at a font in its fontTools representation. I got very tired of typing

```python-console
>>> from fontTools.ttLib import TTFont
>>> font = TTFont("whatever.otf")
```

_every single time_, so I wrote `fontshell`. Run `fontshell whatever.otf` and you are dropped into a Python REPL with the `font` variable set to a `fontTools.ttLib.ttFont.TTFont` object. Bonus: If you have IPython installed, you get tab completion of methods _and_ pretty colours too!

## [`dumptable`](./dumptable)

(Superceded by otfsurgeon)

This extracts a table from a sfnt file and outputs it as a raw binary string. I use this when debugging glyph naming issues and other times TTX gets too clever and doesn't tell me everything I need to know about a table. It's rare that you'll need it, but if you need it, you'll _really_ need it.

## [`glyphs2svg.py`](./glyphs2svg.py)

Converts a .glyphs file to a directory of .svg files.

## [`compare_shape.py`](./compare_shape.py)

I was converting a font from one format to another, and wanted to make sure that the layout rules were equivalent between the two. This script takes two fonts and a list of words, and checks that the shaping output from Harfbuzz is equal, outputting a report of passed and failed tests, as well as any shaping differences.

## [`shape-diff.py`](./shape-diff.py)

So, `compare_shape.py` told you that a test failed and there was a difference between the shaping outputs of two fonts, but it didn't tell you _why_ that happened. That's what `shape-diff.py` does. Give it two fonts and a text, and it'll report what went wrong:

```console
$ python3 shape-diff.py NNU.ttf NNU2.ttf 'نسس'
   font1⮯ ⮮font2
✔ GSUB( 5/20)  Noon=0|Seen=1|SeenFin=2
✔ GSUB( 4/19)  Noon=0|SeenMed=1|SeenFin=2
✔ GSUB( 3/15)  BehxIni=0|OneDotAboveNS=0|SeenMed=1|SeenFin=2
✔ GSUB(26/85)  BehxIni.outT2=0|OneDotAboveNS=0|SeenMed.inT2outT2=1|SeenFin=2
✔ GSUB(27/86)  BehxIni.outT2tall=0|OneDotAboveNS=0|SeenMed.inT2outT2=1|SeenFin=2
✔ GSUB(28/87)  BehxIni.outD1=0|OneDotAboveNS=0|SeenMed.SWinAoutT2=1|SeenFin=2

First difference appeared at GSUB lookup 158 (font1) / 37 (font2)
font1          BehxIni.outD1=0|sp0=0|sp0=0|OneDotAboveNS=0|SeenMed.SWinAoutT2=1|SeenFin=2
font2          BehxIni.outD1=0|OneDotAboveNS=0|SeenMed.SWinAoutT2=1|SeenFin=2
```

## vharfbuzz

vharfbuzz has graduated to [its own repository](https://github.com/simoncozens/vharfbuzz).

## [`stringbrewer`](./stringbrewer)

StringBrewer has graduated to [its own repository](https://github.com/simoncozens/stringbrewer).

## [`fontbakery-shaping.py`](./fontbakery-shaping.py)

Superseded by `fontbakery check-profile fontbakery.profiles.shaping`

## [`gnipahs.py`](./gnipahs.py)

Superseded by `fontbakery check-profile fontbakery.profiles.shaping`

## [`glypholympics`](./glypholympics)

When composing test strings and writing OpenType rules, I often find myself wanting to know "What are the tallest glyphs in the font?" "What are the widest glyphs in the font?" And I haven't got time to open a font editor. I just want the answers.

```
$ ./glypholympics Hind-Regular.otf
Widest    :  dvK_S_P_LA(2082) dvmI.a31(2118) dvmI.a32(2169)
Narrowest :  NULL(0) CR(0) space(0)
                                                                [Horizontal ink]

Fattest   :  itfLogo(1648) dvL_K_YA(1670) dvK_S_P_LA(2038)
Thinnest  :  NULL(0) CR(0) dvmU(0)
                                                            [Horizontal advance]

Tallest   :  dvCandrabindu(1003) dvmEcandra_Anusvara(1003) dvmOcandra_Anusvara(1003)
Shortest  :  dvNukta(-75) dvVirama(-68) cedilla(-51)
                                                                          [yMax]

Highest   :  zerowidthnonjoiner(1041) zerowidthjoiner(1046) radical(1096)
Lowest    :  NULL(0) CR(0) space(0)
                                                                  [Vertical ink]

Deepest   :  dvmvRR(-440) dvmvLL(-437) dvNG_R(-373)
Shallowest:  dvCandrabindu(739) dvmEcandra_Anusvara(739) dvAnusvara.amI(834)
                                                                          [yMin]
```

## [`find-nested-components.py`](./find-nested-components.py)

ftxvalidator tells you if the font has deeply nested components (TTF components
which call other TTF components). But it doesn't tell you *which* glyphs have
the problem. This finds nested components in a TrueType font over a given depth:

```
$ python3 find-nested-components.py --depth=3 MyFont-Regular.ttf
Atilde has depth 3: Atilde -> tildecomb.cap -> tilde -> tildecomb
Ohungarumlaut has depth 4: Ohungarumlaut -> uni030B.cap -> uni030B -> acute -> acutecomb
...
```
