# Windows build and test workflow

## Required tools

- Civilization V with Brave New World
- Sid Meier's Civilization V SDK from Steam
- WorldBuilder for optional inspection and touch-ups
- ModBuddy for packaging and deploying the mod

## Map generation

1. Run `python scripts/generate_map.py` from the repository root.
2. Review `docs/map-preview.png`.
3. Regenerate after changing the projection or terrain rules.
4. Use WorldBuilder only if a binary inspection or manual finishing pass is useful.

## ModBuddy import

1. Create a new empty Civ V mod project.
2. Add the repository files while preserving their relative paths.
3. Confirm `Maps/HistoricalEurope.lua` has `Import into VFS` set to `True`.
5. Add the four XML files as `OnModActivated -> UpdateDatabase` actions.
6. Build the mod and enable logging before the first launch.

## First test

Use only England and France. Starting plots are assigned inside `StartPlotSystem`, before initial units are created. Check the Lua log and verify both civilizations appear at their intended anchors.
