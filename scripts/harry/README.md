
# Level Analysis and Generation Tools by Harry

## Overview
This directory contains Lua scripts for analysing and generating YAML level files for the game.

## Scripts

### Analyse
Analyses an existing level YAML file and reports statistics about its contents.

```bash
cd scripts/harry/analyse
lua main.lua <path_to_level_yaml>
```

If no path is provided, defaults to `../levels/OscarLevels/First Level Recreated/Level_1_players_2.yaml`

Example:
```bash
lua main.lua ../../levels/Step\ by\ Step\ making\ of\ Level\ 2/Level_2_players_4_Step1.yaml
```

### Generate
Generates a blank level YAML file ready for editing with configurable grid dimensions.

```bash
cd scripts/harry/generate
lua main.lua [--width N] [--height N]
```

## Shared Modules
The `shared/` directory contains common Lua modules used by both scripts:
- `grid.lua` - Grid dimension and cell counting utilities
- `objects.lua` - Object counting and reference utilities
- `patients.lua` - Patient data parsing utilities

## File Descriptions

| File/Directory        | Purpose                   |
|-----------------------|---------------------------|
| `analyse/main.lua`    | Level analyser script     |
| `generate/main.lua`   | Level generator script    |
| `shared/grid.lua`     | Grid utility functions    |
| `shared/objects.lua`  | Object utility functions  |
| `shared/patients.lua` | Patient utility functions |
