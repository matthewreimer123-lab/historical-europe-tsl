#!/usr/bin/env python3
"""Generate the fixed Historical Europe Civ V map script and PNG preview."""

from __future__ import annotations

import csv
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 120, 80

# Nonlinear gameplay projection: central Europe gets more tiles per degree.
X_KNOTS = [(-25, 0), (-10, 11), (0, 29), (10, 49), (20, 69), (30, 87), (45, 108), (55, 119)]
Y_KNOTS = [(28, 0), (35, 11), (42, 26), (49, 42), (56, 58), (64, 72), (72, 79)]

MOUNTAIN_LINES = [
    [(-1.5, 42.7), (1.5, 42.8), (3.0, 42.5)],  # Pyrenees
    [(5.5, 44.5), (8.0, 46.0), (11.0, 46.5), (14.5, 46.2), (16.0, 47.0)],  # Alps
    [(7.0, 44.0), (10.0, 43.0), (13.5, 42.0), (16.0, 40.0)],  # Apennines
    [(17.0, 48.0), (20.0, 49.0), (23.5, 48.0), (25.5, 46.0), (24.0, 44.0)],  # Carpathians
    [(14.0, 66.0), (10.0, 63.0), (8.0, 60.0), (7.0, 57.5)],  # Scandinavian range
    [(19.0, 43.5), (23.0, 42.5), (27.0, 42.0)],  # Balkans
    [(38.0, 43.0), (43.0, 42.5), (48.0, 42.0)],  # Caucasus
    [(53.0, 64.0), (55.0, 59.0), (55.0, 54.0), (54.0, 50.0)],  # Ural edge
]


def interpolate(value, knots):
    for (a, out_a), (b, out_b) in zip(knots, knots[1:]):
        if value <= b:
            return out_a + (value - a) / (b - a) * (out_b - out_a)
    return knots[-1][1]


def project(lon, lat):
    return interpolate(lon, X_KNOTS), interpolate(lat, Y_KNOTS)


def inverse_project(x, y):
    return interpolate(x, [(b, a) for a, b in X_KNOTS]), interpolate(y, [(b, a) for a, b in Y_KNOTS])


def point_in_ring(lon, lat, ring):
    inside = False
    previous = ring[-1]
    for current in ring:
        x1, y1 = previous
        x2, y2 = current
        if (y1 > lat) != (y2 > lat):
            crossing = (x2 - x1) * (lat - y1) / (y2 - y1) + x1
            if lon < crossing:
                inside = not inside
        previous = current
    return inside


def point_in_polygon(lon, lat, rings):
    return bool(
        rings
        and point_in_ring(lon, lat, rings[0])
        and not any(point_in_ring(lon, lat, hole) for hole in rings[1:])
    )


def point_on_land(lon, lat, source_features):
    for item in source_features:
        geometry = item["geometry"]
        polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
        if any(point_in_polygon(lon, lat, polygon) for polygon in polygons):
            return True
    return False


def segment_distance(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def mountain_distance(x, y):
    result = 999.0
    for line in MOUNTAIN_LINES:
        transformed = [project(lon, lat) for lon, lat in line]
        for a, b in zip(transformed, transformed[1:]):
            result = min(result, segment_distance(x, y, *a, *b))
    return result


def hash01(x, y, salt=0):
    value = (x * 374761393 + y * 668265263 + salt * 2246822519) & 0xFFFFFFFF
    value = ((value ^ (value >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((value ^ (value >> 16)) & 0xFFFFFFFF) / 0xFFFFFFFF


def neighbors(x, y):
    offsets = (
        ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1))
        if y % 2 == 0
        else ((-1, 0), (1, 0), (0, -1), (0, 1), (1, -1), (1, 1))
    )
    for dx, dy in offsets:
        if 0 <= x + dx < WIDTH and 0 <= y + dy < HEIGHT:
            yield x + dx, y + dy


def build_grid(source_features):
    coordinates, land = [], []
    for y in range(HEIGHT):
        coordinate_row, land_row = [], []
        for x in range(WIDTH):
            lon, lat = inverse_project(x + (0.5 if y % 2 else 0.0), y)
            coordinate_row.append((lon, lat))
            land_row.append(point_on_land(lon, lat, source_features))
        coordinates.append(coordinate_row)
        land.append(land_row)

    plots, terrains, map_features = [], [], []
    for y in range(HEIGHT):
        plot_row, terrain_row, feature_row = [], [], []
        for x in range(WIDTH):
            lon, lat = coordinates[y][x]
            if not land[y][x]:
                plot_row.append("O")
                terrain_row.append("C" if any(land[ny][nx] for nx, ny in neighbors(x, y)) else "O")
                feature_row.append("N")
                continue
            relief, jitter = mountain_distance(x, y), hash01(x, y, 1)
            plot = "M" if relief < 0.58 and jitter > 0.16 else ("H" if relief < 1.65 or jitter > 0.94 else "L")
            if lat >= 68:
                terrain = "S"
            elif lat >= 62:
                terrain = "T"
            elif lat < 35.3 and lon < 34:
                terrain = "D"
            elif lat < 42 or lon > 30 or lat > 57:
                terrain = "P"
            else:
                terrain = "G"
            forest_chance = {"T": 0.34, "P": 0.20, "G": 0.30}.get(terrain, 0)
            feature = "F" if plot != "M" and hash01(x, y, 2) < forest_chance else "N"
            plot_row.append(plot)
            terrain_row.append(terrain)
            feature_row.append(feature)
        plots.append("".join(plot_row))
        terrains.append("".join(terrain_row))
        map_features.append("".join(feature_row))
    return plots, terrains, map_features


def nearest_start_plot(x, y, plots, maximum_radius=6):
    candidates = []
    for candidate_y in range(max(0, y - maximum_radius), min(HEIGHT, y + maximum_radius + 1)):
        for candidate_x in range(max(0, x - maximum_radius), min(WIDTH, x + maximum_radius + 1)):
            if plots[candidate_y][candidate_x] in ("L", "H"):
                distance = math.hypot(candidate_x - x, candidate_y - y)
                candidates.append((distance, candidate_y, candidate_x))
    if not candidates:
        raise ValueError(f"No passable land within {maximum_radius} tiles of ({x}, {y})")
    _, candidate_y, candidate_x = min(candidates)
    return candidate_x, candidate_y


def load_starts(plots):
    with (ROOT / "data/major-starts.csv").open(newline="", encoding="utf-8") as source:
        starts = list(csv.DictReader(source))
    for start in starts:
        primary = tuple(map(round, project(float(start["primary_lon"]), float(start["primary_lat"]))))
        alternate = tuple(map(round, project(float(start["alternate_lon"]), float(start["alternate_lat"]))))
        start["primary_x"], start["primary_y"] = nearest_start_plot(*primary, plots)
        start["alternate_x"], start["alternate_y"] = nearest_start_plot(*alternate, plots)
    return starts


def lua_rows(rows):
    return "\n".join(f'  "{row}",' for row in rows)


def write_lua(plots, terrains, map_features, starts):
    start_rows = "\n".join(
        f'  {row["civilization_type"]} = {{{row["primary_x"]}, {row["primary_y"]}, '
        f'{row["alternate_x"]}, {row["alternate_y"]}, {row["priority"]}}},'
        for row in starts
    )
    script = f'''-- Generated by scripts/generate_map.py. Do not edit by hand.
include("MapGenerator")
include("AssignStartingPlots")
local WIDTH, HEIGHT = {WIDTH}, {HEIGHT}
local PLOT_ROWS = {{
{lua_rows(plots)}
}}
local TERRAIN_ROWS = {{
{lua_rows(terrains)}
}}
local FEATURE_ROWS = {{
{lua_rows(map_features)}
}}
local TSL = {{
{start_rows}
}}

function GetMapScriptInfo()
  return {{
    Name = "Historical Europe TSL",
    Description = "A fixed, gameplay-scaled map of Europe with true starting locations.",
    IsAdvancedMap = false,
    SupportsMultiplayer = true,
    IconIndex = 0,
    SortIndex = 1
  }}
end

function GetMapInitData(worldSize)
  return {{Width = WIDTH, Height = HEIGHT, WrapX = false}}
end

local function decodeRows(rows, legend)
  local values = {{}}
  for y = 1, #rows do
    for x = 1, string.len(rows[y]) do
      values[#values + 1] = legend[string.sub(rows[y], x, x)]
    end
  end
  return values
end

function GeneratePlotTypes()
  SetPlotTypes(decodeRows(PLOT_ROWS, {{
    O = PlotTypes.PLOT_OCEAN, L = PlotTypes.PLOT_LAND,
    H = PlotTypes.PLOT_HILLS, M = PlotTypes.PLOT_MOUNTAIN
  }}))
  GenerateCoasts()
end

function GenerateTerrain()
  local terrain = decodeRows(TERRAIN_ROWS, {{
    O = GameInfoTypes.TERRAIN_OCEAN, C = GameInfoTypes.TERRAIN_COAST,
    G = GameInfoTypes.TERRAIN_GRASS, P = GameInfoTypes.TERRAIN_PLAINS,
    D = GameInfoTypes.TERRAIN_DESERT, T = GameInfoTypes.TERRAIN_TUNDRA,
    S = GameInfoTypes.TERRAIN_SNOW
  }})
  for i = 0, Map.GetNumPlots() - 1 do
    Map.GetPlotByIndex(i):SetTerrainType(terrain[i + 1], false, false)
  end
end

function AddFeatures()
  local decoded = decodeRows(FEATURE_ROWS, {{N = -1, F = GameInfoTypes.FEATURE_FOREST}})
  for i = 0, Map.GetNumPlots() - 1 do
    if decoded[i + 1] ~= -1 then Map.GetPlotByIndex(i):SetFeatureType(decoded[i + 1], -1) end
  end
end

local function assignTSL()
  local claimed = {{}}
  for playerID = 0, GameDefines.MAX_MAJOR_CIVS - 1 do
    local player = Players[playerID]
    if player and player:IsEverAlive() then
      local civ = GameInfo.Civilizations[player:GetCivilizationType()]
      local start = civ and TSL[civ.Type]
      if start then
        local x, y = start[1], start[2]
        local key = x .. ":" .. y
        if claimed[key] then x, y, key = start[3], start[4], start[3] .. ":" .. start[4] end
        local plot = Map.GetPlot(x, y)
        if plot and not plot:IsWater() and not plot:IsMountain() and not claimed[key] then
          player:SetStartingPlot(plot)
          claimed[key] = true
        end
      end
    end
  end
end

function StartPlotSystem()
  local database = AssignStartingPlots.Create()
  database:GenerateRegions()
  database:ChooseLocations()
  database:BalanceAndAssign()
  database:PlaceNaturalWonders()
  database:PlaceResourcesAndCityStates()
  assignTSL()
end
'''
    (ROOT / "Maps/HistoricalEurope.lua").write_text(script, encoding="utf-8")


def write_starts(starts):
    fields = ["civilization_type", "primary_x", "primary_y", "alternate_x", "alternate_y", "priority", "region", "anchor"]
    with (ROOT / "data/generated-major-starts.csv").open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row[field] for field in fields} for row in starts)


def write_starts_xml(starts):
    game_data = ET.Element("GameData")
    table = ET.SubElement(game_data, "HistoricalEuropeCivilizationStarts")
    for row in starts:
        ET.SubElement(
            table,
            "Row",
            {
                "CivilizationType": row["civilization_type"],
                "PrimaryX": str(row["primary_x"]),
                "PrimaryY": str(row["primary_y"]),
                "AlternateX": str(row["alternate_x"]),
                "AlternateY": str(row["alternate_y"]),
                "Priority": row["priority"],
                "Region": row["region"],
            },
        )
    tree = ET.ElementTree(game_data)
    ET.indent(tree, space="  ")
    tree.write(ROOT / "XML/MajorStarts.xml", encoding="utf-8", xml_declaration=True)


def write_preview(plots, terrains):
    codes = {
        ("O", "O"): 0, ("O", "C"): 1, ("L", "G"): 2, ("L", "P"): 3, ("L", "D"): 4,
        ("L", "T"): 5, ("L", "S"): 6, ("H", "G"): 7, ("H", "P"): 7, ("H", "D"): 7,
        ("H", "T"): 7, ("H", "S"): 7, ("M", "G"): 8, ("M", "P"): 8, ("M", "D"): 8,
        ("M", "T"): 8, ("M", "S"): 8,
    }
    image = [[codes[(plots[y][x], terrains[y][x])] for x in range(WIDTH)] for y in range(HEIGHT)]
    colors = ["#173b62", "#3e78a8", "#67a35c", "#b8aa67", "#d7c36b", "#819b79", "#d9e5e8", "#806f54", "#584f49"]
    figure, axis = plt.subplots(figsize=(15, 10), dpi=160)
    axis.imshow(image, origin="lower", interpolation="nearest", cmap=ListedColormap(colors), vmin=0, vmax=8)
    axis.set(title="Historical Europe TSL — generated 120×80 prototype", xlabel="X", ylabel="Y")
    axis.set_aspect("equal")
    figure.tight_layout()
    figure.savefig(ROOT / "docs/map-preview.png")
    plt.close(figure)


def main():
    source = json.loads((ROOT / "data/europe-countries.geojson").read_text(encoding="utf-8"))
    plots, terrains, map_features = build_grid(source["features"])
    starts = load_starts(plots)
    write_lua(plots, terrains, map_features, starts)
    write_starts(starts)
    write_starts_xml(starts)
    write_preview(plots, terrains)
    land_count = sum(row.count("L") + row.count("H") + row.count("M") for row in plots)
    print(f"Generated {WIDTH}x{HEIGHT} map with {land_count} land tiles.")


if __name__ == "__main__":
    main()
