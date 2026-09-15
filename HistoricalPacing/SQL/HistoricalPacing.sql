-- Historical Development Pacing v1
-- All changes apply equally to human and AI players and stack with the
-- selected vanilla game speed.

-- Research requires 50% more time; policies require 25% more time.
-- Units and buildings require 25% less production; projects require 15% less.
-- Tile improvements complete 20% faster.
UPDATE GameSpeeds
SET ResearchPercent    = CAST((ResearchPercent * 3 + 1) / 2 AS INTEGER),
    CulturePercent     = CAST((CulturePercent * 5 + 3) / 4 AS INTEGER),
    TrainPercent       = MAX(1, CAST((TrainPercent * 3 + 3) / 4 AS INTEGER)),
    ConstructPercent   = MAX(1, CAST((ConstructPercent * 3 + 3) / 4 AS INTEGER)),
    CreatePercent      = MAX(1, CAST((CreatePercent * 17 + 19) / 20 AS INTEGER)),
    ImprovementPercent = MAX(1, CAST((ImprovementPercent * 4 + 4) / 5 AS INTEGER));

-- Settlers receive a further 20% reduction. Combined with TrainPercent,
-- their effective production requirement is approximately 60% of vanilla.
UPDATE Units
SET Cost = MAX(1, CAST((Cost * 4 + 4) / 5 AS INTEGER))
WHERE Class = 'UNITCLASS_SETTLER'
  AND Cost > 0;

-- Founding additional cities adds 20% less science and policy overhead.
UPDATE Worlds
SET NumCitiesPolicyCostMod = MAX(1, CAST((NumCitiesPolicyCostMod * 4 + 4) / 5 AS INTEGER)),
    NumCitiesTechCostMod   = MAX(1, CAST((NumCitiesTechCostMod * 4 + 4) / 5 AS INTEGER));

-- Reduce the flat happiness cost of each founded city from 3 to 2.
-- Population unhappiness and occupied-city penalties remain unchanged.
UPDATE Defines
SET Value = 2
WHERE Name = 'UNHAPPINESS_PER_CITY';

-- Add 50% more turns while keeping approximately the same historical end
-- date by shortening the number of months represented by each turn.
UPDATE GameSpeed_Turns
SET TurnsPerIncrement = MAX(1, CAST((TurnsPerIncrement * 3 + 1) / 2 AS INTEGER)),
    MonthIncrement    = MAX(1, CAST((MonthIncrement * 2 + 1) / 3 AS INTEGER));
