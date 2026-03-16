
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

Options:
- `--width N` or `-w N`: Width of the playable area (default: 9, columns a-i)
- `--height N` or `-h N`: Height of the playable area (default: 10, rows 1-9 and A)

The generator places p1 and p2 at the center of the playable area.

Example:
```bash
lua main.lua --width 12 --height 8
```

Output can be redirected to a file:
```bash
lua main.lua > my_new_level.yaml
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
