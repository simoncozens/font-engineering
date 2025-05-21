#!/usr/bin/env python3
from rich.console import Console
from rich.table import Table
from fontTools.ttLib import TTFont
import sys


font = TTFont(sys.argv[1])
seen_ids = set()

if "fvar" in font:
    fvar_table = Table(title="fvar instances")
    fvar_table.add_column("Name ID", justify="right", style="cyan")
    fvar_table.add_column("Name", no_wrap=True)
    fvar_table.add_column("Coordinates", no_wrap=True)
    for instance in font["fvar"].instances:
        name = font["name"].getDebugName(instance.subfamilyNameID)
        if instance.subfamilyNameID > 255:
            seen_ids.add(instance.subfamilyNameID)
        coords = ", ".join(
            f"{font['fvar'].axes[i].axisTag}: {instance.coordinates[font['fvar'].axes[i].axisTag]}"
            for i in range(len(font["fvar"].axes))
        )
        fvar_table.add_row(str(instance.subfamilyNameID), name, coords)

if "STAT" in font:
    stat_table = Table(title="STAT")
    stat_table.add_column("Name ID", justify="right", style="cyan")
    stat_table.add_column("Name", no_wrap=True)
    stat_table.add_column("Coordinate", no_wrap=True)
    axes = [a.AxisTag for a in font["STAT"].table.DesignAxisRecord.Axis]
    for particle in font["STAT"].table.AxisValueArray.AxisValue:
        name = font["name"].getDebugName(particle.ValueNameID)
        if particle.ValueNameID > 255:
            seen_ids.add(particle.ValueNameID)

        if particle.Format == 1:
            coords = f"{axes[particle.AxisIndex]}: {particle.Value}"
        elif particle.Format == 2:
            coords = f"{axes[particle.AxisIndex]}: {particle.RangeMinValue}-{particle.NominalValue}-{particle.RangeMaxValue}"
        elif particle.Format == 3:
            coords = f"{axes[particle.AxisIndex]}: {particle.Value} (linked to {particle.LinkedValue})"
        elif particle.Format == 4:
            # I mean, I *think*. Never actually come across this.
            coords = ", ".join(
                f"{axes[av.AxisIndex]}={av.Value}" for av in particle.AxisValueRecord
            )
        stat_table.add_row(str(particle.ValueNameID), name, coords)

names = {}
for record in font["name"].names:
    if record.nameID not in seen_ids:
        names[record.nameID] = record.toUnicode()

name_table = Table(title="name")
name_table.add_column("Name ID", justify="right", style="cyan")
name_table.add_column("Name", justify="left")
for nameID in sorted(names.keys()):
    name_table.add_row(str(nameID), names[nameID])
console = Console()
console.print(name_table)
if "fvar" in font:
    console.print(fvar_table)
if "STAT" in font:
    console.print(stat_table)
