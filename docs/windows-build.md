# Windows build and test workflow

## Required tools

- Civilization V with Brave New World
- Sid Meier's Civilization V SDK from Steam
- WorldBuilder for editing the binary map
- ModBuddy for packaging and deploying the mod

## Map creation

1. Open WorldBuilder from the Civ V SDK.
2. Create a blank 120 x 80 map with wrapping disabled.
3. Draw only the coarse landmass and strategic seas in the first pass.
4. Do not define scenario players or fixed player slots.
5. Save as `Maps/HistoricalEurope.Civ5Map` in this repository.

## ModBuddy import

1. Create a new empty Civ V mod project.
2. Add the repository files while preserving their relative paths.
3. Confirm `Maps/HistoricalEurope.Civ5Map` has `Import into VFS` set to `False`.
4. Confirm `Lua/AssignStartingPlots.lua` has `Import into VFS` set to `True`.
5. Add the four XML files as `OnModActivated -> UpdateDatabase` actions.
6. Build the mod and enable logging before the first launch.

## First test

Use only England and France. The current Lua component is intentionally experimental: the test determines whether its initialization hook runs early enough. If the game has already placed initial units before `SetStartingPlot`, the next implementation moves assignment into map generation or safely relocates the complete starting unit group.
