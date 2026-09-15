# Map specification v0.1

## Canvas

| Property | Value |
|---|---:|
| Width | 96 hexes |
| Height | 60 hexes |
| Wrap X | No |
| Wrap Y | No |
| Intended ruleset | Civilization V: Brave New World |
| Major civilizations | 12-20 initially; test up to 22 |
| City-states | 20-30 after major starts are stable |

Coordinates use Civ V's lower-left origin: X increases eastward and Y increases northward.

## Geographic scope

- West: Atlantic approaches, Ireland, Portugal, and Morocco; Iceland is excluded.
- North: Scandinavia below the far-Arctic fringe.
- East: European Russia and the eastern Black Sea coast; the Caspian is excluded.
- South: the northern Maghreb, Sicily, Greece, Crete, Cyprus, and central Anatolia.

The map is deliberately not a uniform geographic projection.

## Distortion policy

1. Britain, France, the Low Countries, Germany, northern Italy, Greece, and the Balkans receive extra tiles.
2. The Mediterranean must be wide enough for naval movement but not consume the map.
3. European Russia is deliberately compressed and ends east of Moscow.
4. Mountain chains constrain movement without becoming solid, impassable walls.
5. Important straits remain strategically meaningful: Gibraltar, Dover, Danish straits, Bosporus, and Dardanelles.

## Regional city capacity targets

| Region | Target viable city sites |
|---|---:|
| British Isles | 7-9 |
| France | 8-10 |
| Iberia | 7-9 |
| Italy | 6-8 |
| Germany and Low Countries | 10-12 |
| Scandinavia | 6-8 |
| Poland and Baltics | 7-9 |
| Balkans | 8-10 |
| Ukraine | 7-9 |
| European Russia | 7-10 |
| Anatolia | 7-9 |
| North African coast | 7-10 |

## Construction passes

### Pass 1: strategic silhouette

- Coastlines, major islands, and inland seas.
- Alps, Pyrenees, Carpathians, Balkans, Scandinavian mountains, Caucasus, and Urals.
- Major river corridors only.
- No resources, ruins, or scenario players.

### Pass 2: settlement geometry

- Validate each TSL anchor on land.
- Measure separation between competing major starts.
- Mark intended city-site clusters.
- Adjust coastlines and regional scale before decorative terrain work.

### Pass 3: terrain and climate

- Mediterranean dry belt, Atlantic temperate belt, continental east, boreal north.
- Forest, marsh, floodplain, tundra, and hill placement.
- Navigable and strategically useful river crossings.

### Pass 4: resources and city-states

- Strategic resources distributed for playability first and geographic flavour second.
- Luxury regions that promote trade and competition.
- City-states placed after major-civilization collision tests.

## Acceptance tests for v0.1

- England and France spawn on their intended plots through normal mod setup.
- Neither civilization is pre-assigned in WorldBuilder.
- The map loads with the pacing mod disabled.
- The map loads with at least one unrelated XML-only mod enabled.
- Restarting with the same selected civilizations produces the same starts.
