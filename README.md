# Historical Europe TSL for Civilization V

A gameplay-scaled Europe map for Civilization V: Brave New World, designed for dense settlement, true starting locations (TSL), and compatibility with separate gameplay mods.

## Design goals

- A purpose-built **120 x 80**, non-wrapping Europe map.
- Enlarged Western and Central Europe so nearby civilizations have usable territory.
- True starts selected dynamically rather than fixed scenario players.
- The map mod remains separate from the planned Historical Pacing mod.
- Normal mod selection remains available; no replacement Advanced Setup screen is planned.

## Current status

This repository is an initial design and implementation scaffold. It includes:

- the map scale and regional capacity specification;
- provisional major-civilization TSL anchors;
- the Civ V database schema for primary and alternate starts;
- an experimental Lua relocation component;
- a validator for the coordinate data;
- a placeholder for the WorldBuilder-generated `.Civ5Map` file.

The actual binary map must be drawn and saved with the Civilization V SDK WorldBuilder on Windows. The provisional TSL coordinates will then be adjusted against the finished coastline and terrain.

## Repository layout

```text
HistoricalEuropeTSL.modinfo
Maps/                       WorldBuilder map goes here
XML/                        database tables, TSL data, and text
Lua/                        experimental dynamic-start logic
data/                       editable source-of-truth CSV files
docs/                       map design and build notes
scripts/                    local validation tools
```

## First playable milestone

1. Draw a coarse 120 x 80 landmass in WorldBuilder.
2. Save it as `Maps/HistoricalEurope.Civ5Map` without scenario players.
3. Place England and France using the provisional London and Paris anchors.
4. Verify both civilizations start correctly in a normal modded-game setup.
5. Only then add the remaining civilization starts and collision handling.

## Validation

From the repository root:

```bash
python scripts/validate_starts.py
```

## Compatibility boundary

This repository is only the map and TSL system. Science, culture, production, settler, happiness, and expansion changes belong in a separate `historical-pacing` mod.

## Reference

The dynamic-start approach is informed by Gedemon's Civ V YnAEMP project, but this project is a clean, smaller implementation rather than a fork.
