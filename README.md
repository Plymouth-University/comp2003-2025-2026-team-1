# COMP2003 Group 1 project

This repo contains our work on a generation tool for [Co OPERATION: MultiTurn](https://store.steampowered.com/app/2097840/Co_OPERATION_MultiTurn/) by [Mind Feast Games](www.mindfeastgames.com/).

Authors: @davtheconquerer, @merv300, @horsepie, @birdsky24

## Proposed folder structure (Might not reflect the current stage of development)

```
assets/                     # Contains images used in the repo (e.g. Trello screenshots)
docs/                       # Documentation
+-- report/                 # Contains our final report and build to pdf script
 +-- build.sh               # build the report.md into report.pdf
 +-- report.md              # our full report in markdown format
 +-- report.pdf             # our fully exported report in pdf format
+-- README.md               # Overview and outline of documentation
+-- designDocument.md       # Contains details on our final design plan
+-- meetingLog.md           # Records of our meetings (in Minutes)
+-- trelloScreenshots.md    # Screenshots of our Trello plan
levels/                     # Level and Package files
+-- finalpackage/           # All our individual made levels put together in one place
 +-- README.md              # Outlines how to use finalpackage folder
scripts/                    # Python and Lua scripts used in the project (like validating YAML files)
README.md                   # The file you're reading right now!
```

## Proposed tools used

| Tool/technology            | Purpose                  |
| -------------------------- | ------------------------ |
| Visual Studio Code         | IDE/Text editor          |
| Git                        | Version control          |
| Co Operation modding tools | Testing levels in-engine |
| YAML                       | Level format             |
| Python                     | For project scripts      |
| Lua                        | More project scripts     |
