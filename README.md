# COMP2003 Group 1 project

This repo contains our work on a generation tool for [Co OPERATION: MultiTurn](https://store.steampowered.com/app/2097840/Co_OPERATION_MultiTurn/) by [Mind Feast Games](www.mindfeastgames.com/).

Authors: @davtheconquerer, @merv300, @horsepie, @birdsky24

## Proposed folder structure (Might not reflect the current stage of development)

```
assets/                     # Contains images used in the repo (e.g. Trello screenshots)
docs/                       # Documentation
+-- README.md               # Overview and outline of documentation
+-- designDocument.md       # Contains details on our final design plan
+-- meetingLog.md           # Records of our meetings (in Minutes)
+-- trelloScreenshots.md    # Screenshots of our Trello plan
levels/                     # Level files
+-- README.md               # Details on individual level files
+-- generated/              # Output directory for algorithmically generated levels
+-- final/                  # Curated level files we have tested which match our requirements
scripts/                    # Python scripts used in the project (like validating YAML files)
logs/                       # Chat logs and decleration of any AI usage
AGENTS.md                   # Inital prompt provided to OpenCode agent
README.md                   # The file you're reading right now!
```

## Proposed tools used

| Tool/technology            | Purpose                  |
| -------------------------- | ------------------------ |
| Visual Studio Code         | IDE/Text editor          |
| OpenCode                   | AI coding agent          |
| Ollama                     | Local LLM platform       |
| Git                        | Version control          |
| Co Operation modding tools | Testing levels in-engine |
| YAML                       | Level format             |
| Python                     | For project scripts      |
