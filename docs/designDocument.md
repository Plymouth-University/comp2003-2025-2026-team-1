# Design Document

This is a document detailing our plans and ideas for our COMP2003 project, focusing on a level generation tool for [Co OPERATION: MultiTurn](https://store.steampowered.com/app/2097840/Co_OPERATION_MultiTurn/) by [Mind Feast Games](www.mindfeastgames.com/).

## Assignment Criteria

To create an AI-assisted tool in order to create new levels which will in turn be manually selected by the team to include them in a later update for the game.

## Use of AI
We have identfied two potential pathways for this project: 

- AI Chatbot directly used to generate levels using hand-made levels as training/input. Generated levels could then be vetted and curated in order to find the most 'fun' ([Ollama](https://ollama.com/) could be used for local LLMs, eliminating reliance on cloud-based services).

- We plan on using [Opencode](https://opencode.ai/) specifically as our primary tool for any AI features, as it provides multiple free online models (with local functionality too, see above) and allows for the creation of specialised agents which we can use for particular tasks. For this project, we may create a level generator agent with the context of how to generate YAML level files for the game. We could additionally use a script to validate the agent output to ensure it has no syntax errors and is able to be loaded in the game.

- All use of AI will be transparent with chatlogs and model context provided. Opencode configurations and agent prompts will also be included in the repository.