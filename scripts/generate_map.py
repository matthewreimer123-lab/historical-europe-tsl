#!/usr/bin/env python3
"""Generate the fixed Historical Europe Civ V map script and PNG preview."""

from __future__ import annotations

import csv
import json
import math
import xml.etree.ElementTree as ET
from collections import deque
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

ROOT = Path(__file__).resolve().parents[1]
WIDTH, HEIGHT = 120, 80

# Nonlinear gameplay projection: central Europe gets more tiles per degree.
X_KNOTS = [(-25, 0), (-10, 10), (0, 29), (10, 51), (20, 74), (30, 94), (45, 111), (55, 119)]
Y_KNOTS = [(28, 0), (35, 11), (42, 26), (49, 42), (56, 58), (64, 72), (72, 79)]

MOUNTAIN_LINES = [
    [(-1.5, 42.7), (1.5, 42.8), (3.0, 42.5)],  # Pyrenees
    [(5.5, 44.5), (8.0, 46.0), (11.0, 46.5), (14.5, 46.2), (16.0, 47.0)],  # Alps
    [(7.0, 44.0), (10.0, 43.0), (13.5, 42.0), (16.0, 40.0)],  # Apennines
    [(17.0, 49.2), (20.0, 49.8), (23.5, 48.5), (25.5, 46.0), (24.5, 44.2)],  # Carpathian arc
    [(14.0, 66.0), (10.0, 63.0), (8.0, 60.0), (7.0, 57.5)],  # Scandinavian range
    [(19.0, 43.5), (23.0, 42.5), (27.0, 42.0)],  # Balkans
    [(38.0, 43.0), (43.0, 42.5), (48.0, 42.0)],  # Caucasus
    [(53.0, 64.0), (55.0, 59.0), (55.0, 54.0), (54.0, 50.0)],  # Ural edge
    [(-10.0, 31.2), (-7.5, 32.0), (-5.0, 33.0), (-2.0, 34.5)],  # Atlas
    [(31.0, 40.5), (35.0, 40.8), (39.0, 40.5)],  # Pontic Mountains
    [(29.0, 37.0), (34.0, 37.2), (39.5, 37.0)],  # Taurus Mountains
    [(44.0, 38.0), (47.0, 35.5), (50.0, 32.5), (53.0, 29.5)],  # Zagros
    [(48.0, 36.5), (52.0, 36.2), (55.0, 36.5)],  # Alborz
]

# Lower upland belts. Width is measured in projected map tiles and density
# controls how much of each belt becomes hills rather than level land.
HILL_BANDS = [
    ([(-6.0, 58.5), (-4.5, 56.5), (-3.2, 55.0)], 3.5, 0.90),  # Scottish Highlands
    ([(-3.0, 55.2), (-2.2, 53.0), (-1.8, 51.8)], 2.4, 0.70),  # Pennines
    ([(-4.5, 53.0), (-3.5, 51.5)], 2.5, 0.78),  # Cambrian Mountains
    ([(-10.0, 53.5), (-9.0, 51.5)], 2.8, 0.62),  # western Ireland
    ([(-8.5, 43.0), (-5.0, 43.1), (-2.0, 42.8)], 3.0, 0.84),  # Cantabrian Mountains
    ([(-5.5, 41.0), (-3.0, 40.5), (-1.0, 39.5)], 4.0, 0.66),  # Spanish central uplands
    ([(-4.5, 38.3), (-2.5, 37.2), (-0.5, 37.0)], 2.8, 0.75),  # Baetic ranges
    ([(1.0, 46.5), (3.0, 45.2), (4.0, 44.3)], 4.0, 0.78),  # Massif Central
    ([(6.0, 48.0), (7.5, 47.0)], 2.2, 0.72),  # Vosges and Black Forest
    ([(9.5, 51.5), (11.5, 50.5), (13.5, 49.5)], 3.5, 0.57),  # German central uplands
    ([(12.0, 50.5), (15.0, 49.5), (17.0, 49.0)], 3.0, 0.75),  # Bohemian Massif
    ([(15.0, 46.5), (17.5, 45.5), (19.0, 44.5)], 2.8, 0.72),  # Dinaric foothills
    ([(19.0, 44.0), (22.0, 42.5), (24.0, 40.0)], 3.5, 0.82),  # Dinaric Alps and Pindus
    ([(24.0, 43.5), (27.0, 42.5), (29.0, 42.5)], 3.0, 0.68),  # Balkan Mountains
    ([(25.0, 38.5), (23.0, 37.0), (22.0, 35.5)], 2.7, 0.70),  # Greek uplands
    ([(27.0, 39.0), (32.0, 39.0), (37.0, 38.5), (41.0, 39.0)], 5.0, 0.68),  # Anatolian plateau
    ([(34.0, 44.0), (35.0, 45.0)], 2.0, 0.66),  # Crimean Mountains
    ([(31.0, 57.0), (34.0, 56.0)], 3.5, 0.48),  # Valdai Hills
    ([(36.0, 52.0), (40.0, 50.0)], 4.0, 0.40),  # Central Russian Upland
    ([(43.0, 39.0), (47.0, 36.0), (51.0, 32.0), (55.0, 29.0)], 5.0, 0.78),  # Iranian plateau
]

# Simplified geographic centerlines, ordered roughly from source to mouth.
# They are converted to Civ V hex edges after the fixed land grid is built.
RIVER_LINES = {
    "Thames": [(-1.8, 51.7), (-1.0, 51.6), (-0.1, 51.5), (0.7, 51.5)],
    "Tagus": [(-1.0, 40.3), (-3.0, 40.0), (-5.5, 39.6), (-7.5, 39.2), (-9.0, 38.7)],
    "Ebro": [(-3.0, 42.8), (-1.5, 42.4), (0.0, 41.8), (1.2, 41.2), (0.8, 40.8)],
    "Guadalquivir": [(-4.8, 38.0), (-4.3, 37.6), (-5.3, 37.2), (-6.3, 36.9)],
    "Tensift": [(-6.6, 31.7), (-7.8, 31.6), (-9.2, 31.5)],
    "Loire": [(4.0, 45.8), (2.8, 46.4), (1.0, 47.0), (-0.8, 47.2), (-2.0, 47.3)],
    "Seine": [(5.0, 47.6), (3.2, 48.4), (2.35, 48.9), (0.2, 49.4)],
    "Rhone": [(8.3, 46.6), (6.9, 46.1), (5.0, 45.0), (4.8, 43.4)],
    "Rhine": [(9.0, 46.6), (7.8, 48.0), (7.5, 50.0), (6.5, 51.5), (5.0, 52.0)],
    "Elbe": [(15.5, 50.7), (13.7, 51.2), (12.0, 52.2), (10.0, 53.6), (8.8, 54.0)],
    "Po": [(7.0, 44.7), (9.0, 45.0), (11.0, 45.1), (13.0, 44.9)],
    "Danube": [(8.2, 48.0), (11.8, 48.5), (14.5, 48.3), (16.4, 48.2), (19.1, 47.5), (22.5, 45.5), (26.0, 44.5), (29.5, 45.2)],
    "Vistula": [(19.0, 49.5), (19.8, 51.0), (20.8, 52.5), (19.0, 54.4)],
    "Dniester": [(24.0, 49.0), (26.0, 47.5), (28.5, 46.0), (30.0, 45.5)],
    "Dnieper": [(33.0, 54.5), (31.0, 52.0), (30.5, 50.4), (32.0, 48.0), (34.5, 46.0)],
    "Don": [(38.0, 54.0), (39.5, 51.0), (40.5, 48.0), (39.5, 47.0)],
    "Volga": [(37.0, 57.0), (41.0, 55.5), (45.0, 52.0), (48.0, 48.0), (48.5, 45.0)],
    "Nile": [(31.2, 29.0), (31.0, 29.8), (31.1, 30.7), (31.2, 31.4)],
    "Jordan": [(35.6, 33.2), (35.5, 32.3), (35.5, 31.5)],
    "Euphrates": [(38.0, 38.5), (40.0, 36.5), (42.0, 34.0), (44.5, 32.0), (47.0, 30.5)],
    "Tigris": [(42.5, 38.0), (43.5, 36.0), (44.0, 34.0), (46.0, 31.5)],
}


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


def hill_probability(x, y):
    result = 0.0
    for line, width, density in HILL_BANDS:
        transformed = [project(lon, lat) for lon, lat in line]
        distance = min(segment_distance(x, y, *a, *b) for a, b in zip(transformed, transformed[1:]))
        if distance < width:
            result = max(result, density * (1.0 - distance / width))
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
            upland = hill_probability(x, y)
            plot = "M" if relief < 0.58 and jitter > 0.16 else (
                "H" if relief < 1.65 or jitter < upland or jitter > 0.965 else "L"
            )
            if lat >= 68:
                terrain = "S"
            elif lat >= 62:
                terrain = "T"
            elif -10.8 <= lon <= -4.0 and 30.0 <= lat <= 35.5:
                terrain = "P"
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


def nearest_land_plot(x, y, plots, maximum_radius=4):
    candidates = []
    for candidate_y in range(max(0, y - maximum_radius), min(HEIGHT, y + maximum_radius + 1)):
        for candidate_x in range(max(0, x - maximum_radius), min(WIDTH, x + maximum_radius + 1)):
            if plots[candidate_y][candidate_x] in ("L", "H"):
                candidates.append((math.hypot(candidate_x - x, candidate_y - y), candidate_y, candidate_x))
    if not candidates:
        return None
    _, candidate_y, candidate_x = min(candidates)
    return candidate_x, candidate_y


def land_path(start, goal, plots, maximum_steps=18):
    queue = deque([(start, [start])])
    visited = {start}
    while queue:
        current, path = queue.popleft()
        if current == goal:
            return path
        if len(path) >= maximum_steps:
            continue
        for candidate in neighbors(*current):
            if candidate not in visited and plots[candidate[1]][candidate[0]] in ("L", "H"):
                visited.add(candidate)
                queue.append((candidate, path + [candidate]))
    return []


def build_river_guides(plots):
    guides = []
    for name, points in RIVER_LINES.items():
        route = []
        for (lon_a, lat_a), (lon_b, lat_b) in zip(points, points[1:]):
            ax, ay = project(lon_a, lat_a)
            bx, by = project(lon_b, lat_b)
            samples = max(2, math.ceil(math.hypot(bx - ax, by - ay) * 2))
            for step in range(samples):
                amount = step / (samples - 1)
                snapped = nearest_land_plot(round(ax + (bx - ax) * amount), round(ay + (by - ay) * amount), plots)
                if snapped and (not route or snapped != route[-1]):
                    route.append(snapped)
        connected = []
        for target in route:
            if not connected:
                connected.append(target)
                continue
            segment = land_path(connected[-1], target, plots)
            if segment:
                connected.extend(segment[1:])
        guide = []
        guide_indices = {}
        for position in connected:
            if position in guide_indices:
                keep = guide_indices[position] + 1
                for removed in guide[keep:]:
                    guide_indices.pop(removed, None)
                guide = guide[:keep]
            elif not guide or position != guide[-1]:
                guide_indices[position] = len(guide)
                guide.append(position)
        if len(guide) >= 2:
            guides.append((name, guide))
    return guides


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


def improve_start_region(lon, lat, plots, terrains, map_features, radius):
    projected = tuple(map(round, project(lon, lat)))
    center_x, center_y = nearest_start_plot(*projected, plots)
    for y in range(max(0, center_y - radius), min(HEIGHT, center_y + radius + 1)):
        for x in range(max(0, center_x - radius), min(WIDTH, center_x + radius + 1)):
            if math.hypot(x - center_x, y - center_y) <= radius and plots[y][x] != "O":
                if plots[y][x] == "M":
                    plots[y] = plots[y][:x] + "H" + plots[y][x + 1:]
                terrains[y] = terrains[y][:x] + "P" + terrains[y][x + 1:]
                map_features[y] = map_features[y][:x] + "N" + map_features[y][x + 1:]
    plots[center_y] = plots[center_y][:center_x] + "L" + plots[center_y][center_x + 1:]


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


def load_minor_starts(plots):
    with (ROOT / "data/minor-starts.csv").open(newline="", encoding="utf-8") as source:
        starts = list(csv.DictReader(source))
    for start in starts:
        position = tuple(map(round, project(float(start["longitude"]), float(start["latitude"]))))
        start["x"], start["y"] = nearest_start_plot(*position, plots)
    return starts


def write_lua(plots, terrains, map_features, starts, minor_starts, river_guides):
    start_rows = "\n".join(
        f'  {row["civilization_type"]} = {{{row["primary_x"]}, {row["primary_y"]}, '
        f'{row["alternate_x"]}, {row["alternate_y"]}, {row["priority"]}}},'
        for row in starts
    )
    minor_rows = "\n".join(
        f'  {row["minor_civilization_type"]} = {{{row["x"]}, {row["y"]}}},'
        for row in minor_starts
    )
    river_rows = "\n".join(
        '  {name = "' + name + '", points = {'
        + ", ".join(f"{{{x}, {y}}}" for x, y in points)
        + "}},"
        for name, points in river_guides
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
local MINOR_TSL = {{
{minor_rows}
}}
local RIVER_GUIDES = {{
{river_rows}
}}
local ORIGINAL_RIVER_VALUE = GetRiverValueAtPlot
local ACTIVE_RIVER_GUIDE = nil

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
  local desert = GameInfoTypes.TERRAIN_DESERT
  local floodPlains = GameInfoTypes.FEATURE_FLOOD_PLAINS
  for i = 0, Map.GetNumPlots() - 1 do
    local plot = Map.GetPlotByIndex(i)
    if plot:GetTerrainType() == desert and plot:IsRiver() and not plot:IsMountain() then
      plot:SetFeatureType(floodPlains, -1)
    end
  end
end

function AddRivers()
  nextRiverID = 0
  _rivers = {{}}
  for _, river in ipairs(RIVER_GUIDES) do
    local source = Map.GetPlot(river.points[1][1], river.points[1][2])
    local corner = source and source:GetInlandCorner()
    if corner then
      ACTIVE_RIVER_GUIDE = river.points
      DoRiver(corner)
      ACTIVE_RIVER_GUIDE = nil
    end
  end
end

function GetRiverValueAtPlot(plot)
  if not ACTIVE_RIVER_GUIDE then return ORIGINAL_RIVER_VALUE(plot) end
  local bestValue = math.huge
  for index, waypoint in ipairs(ACTIVE_RIVER_GUIDE) do
    local distance = Map.PlotDistance(plot:GetX(), plot:GetY(), waypoint[1], waypoint[2])
    local value = distance * 100 + (#ACTIVE_RIVER_GUIDE - index) * 3
    if value < bestValue then bestValue = value end
  end
  if plot:IsWater() then bestValue = bestValue - 50 end
  return bestValue
end

function AddLakes()
  print("Historical Europe TSL: random lake generation disabled")
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
  local occupied = {{}}
  for playerID = 0, GameDefines.MAX_MAJOR_CIVS - 1 do
    local player = Players[playerID]
    if player and player:IsEverAlive() then
      local plot = player:GetStartingPlot()
      if plot then occupied[#occupied + 1] = {{plot:GetX(), plot:GetY()}} end
    end
  end
  return occupied
end


local function farEnoughFromStarts(x, y, occupied, minimumDistance)
  for _, position in ipairs(occupied) do
    if Map.PlotDistance(x, y, position[1], position[2]) < minimumDistance then return false end
  end
  return true
end


local function chooseMinorPlot(start, occupied)
  local bestPlot, bestDistance = nil, 999
  for radius = 0, 8 do
    for y = math.max(0, start[2] - radius), math.min(HEIGHT - 1, start[2] + radius) do
      for x = math.max(0, start[1] - radius), math.min(WIDTH - 1, start[1] + radius) do
        local distance = Map.PlotDistance(start[1], start[2], x, y)
        if distance <= radius and distance < bestDistance then
          local plot = Map.GetPlot(x, y)
          if plot and not plot:IsWater() and not plot:IsMountain() and farEnoughFromStarts(x, y, occupied, 4) then
            bestPlot, bestDistance = plot, distance
          end
        end
      end
    end
    if bestPlot then return bestPlot end
  end
  return nil
end


local function assignMinorTSL(occupied)
  for playerID = GameDefines.MAX_MAJOR_CIVS, GameDefines.MAX_CIV_PLAYERS - 1 do
    local player = Players[playerID]
    if player and player:IsEverAlive() and player:IsMinorCiv() then
      local minor = GameInfo.MinorCivilizations[player:GetMinorCivType()]
      local start = minor and MINOR_TSL[minor.Type]
      if start then
        local plot = chooseMinorPlot(start, occupied)
        if plot then
          player:SetStartingPlot(plot)
          occupied[#occupied + 1] = {{plot:GetX(), plot:GetY()}}
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
  local occupied = assignTSL()
  assignMinorTSL(occupied)
end
'''
    (ROOT / "Maps/HistoricalEurope.lua").write_text(script, encoding="utf-8")


def write_starts(starts):
    fields = ["civilization_type", "primary_x", "primary_y", "alternate_x", "alternate_y", "priority", "region", "anchor"]
    with (ROOT / "data/generated-major-starts.csv").open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=fields, lineterminator="\n")
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


def write_preview(plots, terrains, river_guides):
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
    river_points = [point for _, guide in river_guides for point in guide]
    axis.scatter([point[0] for point in river_points], [point[1] for point in river_points], s=3, c="#42bff5")
    axis.set(title="Historical Europe TSL — generated 120×80 topography", xlabel="X", ylabel="Y")
    axis.set_aspect("equal")
    figure.tight_layout()
    figure.savefig(ROOT / "docs/map-preview.png")
    plt.close(figure)


def main():
    source = json.loads((ROOT / "data/europe-countries.geojson").read_text(encoding="utf-8"))
    plots, terrains, map_features = build_grid(source["features"])
    improve_start_region(-7.9811, 31.6295, plots, terrains, map_features, 3)
    improve_start_region(19.0402, 47.4979, plots, terrains, map_features, 2)
    starts = load_starts(plots)
    minor_starts = load_minor_starts(plots)
    river_guides = build_river_guides(plots)
    write_lua(plots, terrains, map_features, starts, minor_starts, river_guides)
    write_starts(starts)
    write_starts_xml(starts)
    write_preview(plots, terrains, river_guides)
    land_count = sum(row.count("L") + row.count("H") + row.count("M") for row in plots)
    river_tiles = sum(len(guide) for _, guide in river_guides)
    print(f"Generated {WIDTH}x{HEIGHT} map with {land_count} land tiles and {len(river_guides)} guided rivers ({river_tiles} waypoints).")


if __name__ == "__main__":
    main()
