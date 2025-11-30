# COMP2003 Group 1 project
This repo contains our work on a generation tool for [Co OPERATION: MultiTurn](https://store.steampowered.com/app/2097840/Co_OPERATION_MultiTurn/) by [Mind Feast Games](www.mindfeastgames.com/).

Authors: @davtheconquerer, @merv300, @horsepie, @birdsky24

## Proposed folder structure (Might not reflect the current stage of development)
```
assets/                 # Contains images used in the repo (e.g. Trello screenshot)
docs/                   # Documentation
+-- README.md           # Overview and outline of documentation
+-- meetingLogs.md      # Records of our meetings (in Minutes)
+-- designDocument.md   # Contains details on our final design plan
levels/                 # Level files
+-- README.md           # Details on individual level files
+-- generated/          # Output directory for algorithmically generated levels
+-- final/              # Curated level files we have tested which match our requirements
scripts/                # Python scripts used in the project (like validating YAML files)
logs/                   # Chat logs and decleration of any AI usage
AGENTS.md               # inital prompt provided to OpenCode agent
```

## Proposed tools used
| Tool/technology            | Purpose                  |
|----------------------------|--------------------------|
| Visual Studio Code         | IDE/Text editor          |
| OpenCode                   | AI coding agent          |
| Ollama                     | Local LLM platform       |
| Git                        | Version control          |
| Co Operation modding tools | Testing levels in-engine |
| YAML                       | Level format             |
| Python                     | For project scripts      |

---

[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/xGnTrW1S)
[![Open in Codespaces](https://classroom.github.com/assets/launch-codespace-2972f46106e565e64193e422d61a12cf1da4916b45550586e14ef0a7c637dd04.svg)](https://classroom.github.com/open-in-codespaces?assignment_repo_id=21437715)