#!/usr/bin/env python3
from rich.console import Console
from rich.table import Table
from fontTools.ttLib import TTFont
import sys


font = TTFont(sys.argv[1])
names = {}
for record in font["name"].names:
    names[record.nameID] = record.toUnicode()

table = Table(title="name")
table.add_column("Name ID", justify="right", style="cyan")
table.add_column("Name", justify="left")
for nameID in sorted(names.keys()):
    table.add_row(str(nameID), names[nameID])
console = Console()
console.print(table)

if "fvar" in font:
    table = Table(title="fvar instances")
    table.add_column("Name ID", justify="right", style="cyan")
    table.add_column("Name", no_wrap=True)
    table.add_column("Coordinates", no_wrap=True)
    for instance in font["fvar"].instances:
        name = font["name"].getDebugName(instance.subfamilyNameID)
        coords = ", ".join(
            f"{font['fvar'].axes[i].axisTag}: {instance.coordinates[font['fvar'].axes[i].axisTag]}"
            for i in range(len(font["fvar"].axes))
        )
        table.add_row(str(instance.subfamilyNameID), name, coords)
    console.print(table)

if "STAT" in font:
    table = Table(title="STAT")
    table.add_column("Name ID", justify="right", style="cyan")
    table.add_column("Name", no_wrap=True)
    table.add_column("Coordinate", no_wrap=True)
    axes = [a.AxisTag for a in font["STAT"].table.DesignAxisRecord.Axis]
    for particle in font["STAT"].table.AxisValueArray.AxisValue:
        name = font["name"].getDebugName(particle.ValueNameID)
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
        table.add_row(str(particle.ValueNameID), name, coords)
    console.print(table)
