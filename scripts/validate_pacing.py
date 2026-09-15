#!/usr/bin/env python3
"""Validate Historical Pacing SQL against a minimal Civ V-shaped database."""

from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "HistoricalPacing/SQL/HistoricalPacing.sql").read_text(encoding="utf-8")

database = sqlite3.connect(":memory:")
database.executescript(
    """
    CREATE TABLE GameSpeeds (
      Type TEXT, ResearchPercent INTEGER, CulturePercent INTEGER,
      TrainPercent INTEGER, ConstructPercent INTEGER, CreatePercent INTEGER,
      ImprovementPercent INTEGER
    );
    CREATE TABLE Units (Type TEXT, Class TEXT, Cost INTEGER);
    CREATE TABLE Worlds (
      Type TEXT, NumCitiesPolicyCostMod INTEGER, NumCitiesTechCostMod INTEGER
    );
    CREATE TABLE Defines (Name TEXT, Value INTEGER);
    CREATE TABLE GameSpeed_Turns (
      GameSpeedType TEXT, TurnsPerIncrement INTEGER, MonthIncrement INTEGER
    );

    INSERT INTO GameSpeeds VALUES ('GAMESPEED_STANDARD', 100, 100, 100, 100, 100, 100);
    INSERT INTO Units VALUES ('UNIT_SETTLER', 'UNITCLASS_SETTLER', 100);
    INSERT INTO Units VALUES ('UNIT_WARRIOR', 'UNITCLASS_WARRIOR', 40);
    INSERT INTO Worlds VALUES ('WORLDSIZE_STANDARD', 10, 5);
    INSERT INTO Defines VALUES ('UNHAPPINESS_PER_CITY', 3);
    INSERT INTO GameSpeed_Turns VALUES ('GAMESPEED_STANDARD', 100, 120);
    """
)
database.executescript(SQL)

speed = database.execute("SELECT * FROM GameSpeeds").fetchone()
assert speed[1:] == (225, 125, 75, 75, 85, 80), speed
assert database.execute("SELECT Cost FROM Units WHERE Type='UNIT_SETTLER'").fetchone()[0] == 60
assert database.execute("SELECT Cost FROM Units WHERE Type='UNIT_WARRIOR'").fetchone()[0] == 40
assert database.execute("SELECT NumCitiesPolicyCostMod, NumCitiesTechCostMod FROM Worlds").fetchone() == (8, 4)
assert database.execute("SELECT Value FROM Defines").fetchone()[0] == 1
assert database.execute("SELECT TurnsPerIncrement, MonthIncrement FROM GameSpeed_Turns").fetchone() == (225, 53)

print("Historical Pacing SQL validation passed.")
