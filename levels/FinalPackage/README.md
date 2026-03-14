# How to add levels to this package

## First copy the entire `finalpackage/` folder

The first step is to copy the entire **up to date** `finalpackage/` folder into your game's `PlayerPackages` folder. normally located under `SteamLibrary\steamapps\common\Co OPERATION MultiTurn\Co OPERATION_Data\StreamingAssets\PlayerPackages`

## Make sure you add your ownership to your level

Make sure to add your name in `creatorName:` like below example

```yaml
fileProperties:
  creatorName: OscarK
```

## Renaming your levels

first you will need to rename your levels to match the order of current levels in under `finalpackage/Levels`. For example, if you're working on `Level_1_players_2.yaml` and it is ready to be added to `finalpackage/`, you need to rename it to `Level_$level_players_2.yaml` where `$level` is the next available level number.

## Updating package.yaml

if the latest level added is

```yaml
  - levelId: level3
    levelName: Level 3
    unlockedByDefault: false
    minCuresToProgress: 1
    levelCutscene: "" # not yet used
    levelFiles:
      - { playerCount: 2, fileName: "Level_3_players_2" }
      - { playerCount: 3, fileName: "Level_3_players_3" }
      - { playerCount: 4, fileName: "Level_3_players_4" }
```

you will need to copy this and edit the values to this

```yaml
  - levelId: level4
    levelName: Level 4
    unlockedByDefault: false
    minCuresToProgress: 1
    levelCutscene: "" # not yet used
    levelFiles:
      - { playerCount: 2, fileName: "Level_4_players_2" }
      - { playerCount: 3, fileName: "Level_4_players_3" }
      - { playerCount: 4, fileName: "Level_4_players_4" }
```

## Finally upload the updated files to github

**MAKE SURE TO COMMUNICATE THIS IN THE DISCORD**

contact David if you need help