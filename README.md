# Historical Europe TSL for Civilization V

A gameplay-scaled Europe map for Civilization V: Brave New World, designed for dense settlement, true starting locations (TSL), and compatibility with separate gameplay mods.

This repository now contains two independently selectable mods:

- The repository root is **Historical Europe TSL**, the map mod.
- [`HistoricalPacing/`](HistoricalPacing/) is **Historical Development Pacing**,
  the optional science, culture, production, and expansion overhaul.

## Design goals

- A purpose-built **96 x 60**, non-wrapping Europe map.
- Enlarged Western and Central Europe so nearby civilizations have usable territory.
- True starts selected dynamically rather than fixed scenario players.
- The map mod remains separate from the optional Historical Development Pacing mod.
- Normal mod selection remains available; no replacement Advanced Setup screen is planned.

## Current status

This repository is an initial design and implementation scaffold. It includes:

- the map scale and regional capacity specification;
- provisional major-civilization TSL anchors;
- the Civ V database schema for primary and alternate starts;
- a deterministic Lua map generator with start assignment during map creation;
- a validator for the coordinate data;
- a rendered PNG preview of the generated terrain.

The map is generated from geographic polygon data and a nonlinear gameplay projection. WorldBuilder is only needed for optional inspection and small finishing changes.

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

1. Generate the 96 x 60 map script and inspect `docs/map-preview.png`.
2. Adjust the projection, coastline, and terrain rules in `scripts/generate_map.py`.
3. Test England and France using the generated London and Paris anchors.
4. Verify both civilizations start correctly in a normal modded-game setup.
5. Only then add the remaining civilization starts and collision handling.

The current test build is mod version 10. Version 10 crops Iceland, the high
Arctic, the Caspian, Iran, and Mesopotamia; moves the eastern boundary to the
eastern Black Sea; and narrows Scandinavia. Version 9 added deterministic
tributaries to every river system and gives the Nile a three-mouth delta.
Version 8 added the Thames, moved the Nile's source away from the map boundary,
and restored automatic flood plains on desert river tiles. Version 7 compressed the Russian and steppe region and
added Mongol, Persian, Babylonian, and Assyrian starts. Version 6 introduced
continuous guided river paths and added Egypt.

## Validation

From the repository root:

```bash
python scripts/generate_map.py
python scripts/validate_starts.py
```

## Compatibility boundary

This repository is only the map and TSL system. Science, culture, production, settler, happiness, and expansion changes belong in a separate `historical-pacing` mod.

## Reference

The dynamic-start approach is informed by Gedemon's Civ V YnAEMP project, but this project is a clean, smaller implementation rather than a fork.
