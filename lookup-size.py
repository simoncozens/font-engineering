from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.otBase import OTTableWriter
import sys
from fontTools.feaLib.lookupDebugInfo import LOOKUP_DEBUG_INFO_KEY

font = TTFont(sys.argv[1])

def locate(table, ix):
    if "Debg" not in font:
        return "Lookup "+str(ix)
    debg = font["Debg"].data[LOOKUP_DEBUG_INFO_KEY][table].get(str(ix))
    if debg:
        return f"{ix} = {debg[0]} ({debg[1]})"
    return str(ix)

for table in ["GSUB", "GPOS"]:
    print(f"{table} table")
    print("==========\n")
    lookups = font.get(table).table.LookupList.Lookup
    sizes = []
    for ix, lookup in enumerate(lookups):
        writer = OTTableWriter()
        lookup.compile(writer, font)
        try:
            size = len(writer.getAllData())
        except:
            size = 123456789
        sizes.append((locate(table, ix), size))

    for location, size in (list(sorted(sizes, key=lambda a:-a[1])))[0:10]:
        if size == 123456789:
            print(location, "\t(overflowed)")
        else:
            print(location, "\t", size)
