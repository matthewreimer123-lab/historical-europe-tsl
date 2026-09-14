-- Historical Europe TSL experimental initializer.
--
-- Important: SetStartingPlot alone may occur too late when loaded as an
-- InGameUIAddin. The first playable milestone will determine whether unit
-- relocation is sufficient or whether the assignment must move into the map
-- generation phase. Keeping this logic isolated makes that change inexpensive.

local MAP_WIDTH = 120
local MAP_HEIGHT = 80
local initialized = false

local function getStart(civilizationType)
  for row in DB.Query([[
    SELECT PrimaryX, PrimaryY, AlternateX, AlternateY, Priority
    FROM HistoricalEuropeCivilizationStarts
    WHERE CivilizationType = ?
  ]], civilizationType) do
    return row
  end
  return nil
end

local function validPlot(x, y)
  if x == nil or y == nil then
    return nil
  end
  if x < 0 or x >= MAP_WIDTH or y < 0 or y >= MAP_HEIGHT then
    return nil
  end
  local plot = Map.GetPlot(x, y)
  if plot and not plot:IsWater() and not plot:IsMountain() then
    return plot
  end
  return nil
end

local function plotKey(plot)
  return tostring(plot:GetX()) .. ":" .. tostring(plot:GetY())
end

local function assignStartingPlots()
  if initialized then
    return
  end
  initialized = true

  local assignments = {}
  for playerID = 0, GameDefines.MAX_MAJOR_CIVS - 1 do
    local player = Players[playerID]
    if player and player:IsEverAlive() then
      local civInfo = GameInfo.Civilizations[player:GetCivilizationType()]
      local start = civInfo and getStart(civInfo.Type) or nil
      if start then
        table.insert(assignments, {
          player = player,
          primary = validPlot(start.PrimaryX, start.PrimaryY),
          alternate = validPlot(start.AlternateX, start.AlternateY),
          priority = start.Priority or 100
        })
      end
    end
  end

  table.sort(assignments, function(a, b)
    return a.priority < b.priority
  end)

  local occupied = {}
  for _, assignment in ipairs(assignments) do
    local plot = assignment.primary
    if plot and occupied[plotKey(plot)] then
      plot = assignment.alternate
    end
    if plot and not occupied[plotKey(plot)] then
      assignment.player:SetStartingPlot(plot)
      occupied[plotKey(plot)] = true
    end
  end
end

-- This hook is deliberately the smallest possible prototype. We will verify
-- timing in Civ V before adding unit movement, city-states, or vicinity checks.
Events.SequenceGameInitComplete.Add(assignStartingPlots)
