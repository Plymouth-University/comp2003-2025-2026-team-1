---
name: level-gen
description: Generate, analyse, and clean YAML level files for Co OPERATION: MultiTurn. Use when creating new levels, analysing level structure, or formatting level files.
---

# Level Generation Skills

## Scripts

### Generate — `scripts/harry/generate/`
Creates a blank level YAML with configurable grid dimensions.

```bash
cd scripts/harry/generate && lua main.lua --width 9 --height 10 > ../../levels/my_level.yaml
```

- Default: 9×10 grid (columns a–i, rows 1–9+A) with p1/p2 centered, north/west walls pre-placed
- Max dimensions: 34×34
- Output to stdout — always redirect to a `.yaml` file
- Places only p1, p2, and wall objects — foundations (`f`) must be added manually to every playable cell

### Analyse — `scripts/harry/analyse/`
Reports statistics about an existing level YAML (object counts, grid size, patients, etc).

```bash
cd scripts/harry/analyse && lua main.lua ../../levels/FinalPackage/Levels/Level_1_players_2.yaml
```

- Defaults to `Level_1_players_2.yaml` if no path given
- Requires `lyaml` Lua module installed

### Clean — `scripts/dav/delete_blank.py`
Removes empty grid objects and updates the grid string.

```bash
cd scripts/dav && python delete_blank.py
```

- Prompts for input/output paths interactively
- Always run after manual edits to remove stale empty entries

## Level YAML Structure

```yaml
include: [LevelsShared.yaml]
fileProperties:
  creatorName: ...
sceneName: OriginalWorld
cameraSettings: ...
grid: |                           # 2D grid of cell refs (e.g. a1, __)
gridObjects:                      # Objects at each cell: key: [obj, ...]
objectDefinitions:                # Level-specific overrides
sounds:
globalData:                       # Patient definitions (pt1, pt2, ...)
```

**Grid conventions:**
- Playable area sits in the middle section; header/footer are decorative border
- Cells use column-row notation: columns a–i, rows 1–9 then A, B, C... (e.g. `a1`, `g5`, `dA`)
- `__` = empty cell, `gm` = grid marker (top-left only)
- Blank lines separate header / playable area / footer sections

**gridObjects:**
- Every playable cell with objects needs a foundation first: `f5: [f, p1]`
- Common objects: `f` (foundation), `p1`–`p4` (players), `wall_*`, `lightbulb_*`, `b_[nesw]` (beds), `pillcab_closed_*`, `syringecab_*`, `applecab_*`
- Patients use nested syntax: `[f, { id: patient, data: { id: pt1 } }]`
- Named variants exist: `patient_edBanger`, `patient_chris`, `patient_childOliviaAndAvo` (+ `_alt1`, `_alt2`)

**globalData patients:**
- Starting patients appear immediately: `pt1: { health: 8, need: pill }`
- Spawning patients: `pt3: { health: 8, appearOnTurn: 4, need: syringe, character: grace }`
- Need types: `pill`, `syringe`, `apple`

## Reference Files

- `levels/FinalPackage/Levels/LevelsShared.yaml` — all shared object definitions (walls, patients, beds, pavement, backgrounds). Consult this for valid object names.
- `levels/FinalPackage/Levels/` — completed levels (1–6, 2/3/4 player variants) for patterns
- `levels/Step by Step making of Level 2/` — 11 YAML files (Step1–Step11) showing incremental level construction from blank to finished. Best learning resource.
- `levels/FinalPackage/package.yaml` — level package manifest. New levels must be registered here to appear in-game.

## Workflow

1. **Generate** a blank level with appropriate dimensions
2. **Reference** step-by-step examples or completed levels for patterns
3. **Edit** the grid and gridObjects — place walls, foundations (every cell), players, patients, items
4. **Define patients** in globalData with health, need, and optional `appearOnTurn`
5. **Register** the level in `package.yaml` (copy an existing entry, increment level number)
6. **Analyse** to verify structure and counts
7. **Clean** to remove empty entries before committing
