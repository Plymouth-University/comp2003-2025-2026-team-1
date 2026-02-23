# Design Document

This is a document detailing our plans and ideas for our COMP2003 project, focusing on a level generation tool for [Co OPERATION: MultiTurn](https://store.steampowered.com/app/2097840/Co_OPERATION_MultiTurn/) by [Mind Feast Games](www.mindfeastgames.com/).

## Assignment Criteria

To create an AI-assisted tool in order to create new levels which will in turn be manually selected by the team to include them in a later update for the game.

## Use of AI
We have identified this as a potential pathway for this project:

- AI Chatbot directly used to generate levels using hand-made levels as training/input. Generated levels could then be vetted and curated in order to find the most 'fun' ([Ollama](https://ollama.com/) could be used for local LLMs, eliminating reliance on cloud-based services).

- We plan on using [Opencode](https://opencode.ai/) specifically as our primary tool for any AI features, as it provides multiple free online models (with local functionality too, see above) and allows for the creation of specialised agents which we can use for particular tasks. For this project, we may create a level generator agent with the context of how to generate YAML level files for the game. We could additionally use a script to validate the agent output to ensure it has no syntax errors and is able to be loaded in the game.

- All use of AI will be transparent with chatlogs and model context provided. Opencode configurations and agent prompts will also be included in the repository.

## Legal, Social, Ethical, Professional Impacts (LSEP)

### Legal Considerations

Our project must comply with relevant UK legal frameworks, particularly around intellectual property (IP), data usage, and software licensing. All level files and assets used for AI input will be restricted to material provided by Mind Feast Games or created by our team, ensuring no infringement of third-party copyrights.
Use of AI services such as Opencode and Ollama will be checked for licence compatibility, especially regarding commercial use, data retention, and model redistribution. Since the project involves generating game content, ownership of any generated levels will be attributed to Mind Feast Games, in line with agreements established for the project.
We will also comply with UK [GDPR](https://www.gov.uk/data-protection) principles by ensuring no personal data is used, processed, or stored during any stage of development. 

### Social Considerations

The integration of AI generation within a creative workflow can raise concerns about job displacement and perceived devaluation of human creative input. Our approach mitigates this by positioning AI purely as an assistive tool to support, rather than replace, human level designers.
The results of the tool will always undergo human review and curation, ensuring that any levels included in the game meet accessibility, fairness, and player-experience standards.
The time saved during these levels being generated has the intended effect of freeing up time for developers to focus on other activities within the game's development. This should allow for more rapid prototyping too and can allow for developers to flesh out different ideas from generated levels. The difficullty of a given level needs to be catered for and kept in mind due to the careful balancing implemented by the developers behind the original levels, we intend on accounting for this change and hopefully implementing something similar.
Transparency is important socially; therefore, documentation explaining how AI is used will be included in the final repository to promote responsible understanding of AI-augmented processes.

### Ethical Considerations

Plymouth’s ethical guidelines emphasise accountability, transparency, and responsible system behaviour. We will ensure that the AI tool operates within these principles by documenting prompts, model configurations, and all AI outputs used during development.
Since generative models can reproduce patterns or introduce unwanted bias (e.g., repetitive or unfair level layouts), we will implement validation and testing to detect and correct these issues. The creative aspect of the levels is a concern we will keep an eye on to ensure each generated level can feel as dynamic as the hand-crafted developer ones.
No harmful, offensive, or exploitative content will be generated, and all generated levels will be checked to ensure they promote fair gameplay and do not intentionally disadvantage or exclude players.

### Professional Considerations

This project follows accepted professional software engineering practices, as expected by Plymouth University’s computing programmes. This includes version control, maintainable code structure, thorough documentation of level creation, testing procedures, and consistent communication with the client (Mind Feast Games).
In line with professional conduct standards (e.g., [BCS Code of Conduct](https://www.bcs.org/membership-and-registrations/become-a-member/bcs-code-of-conduct)), the team commits to honesty, transparency, and clear reporting of AI use. All AI-assisted components will be traceable, and limitations of the system will be acknowledged.
By integrating responsible AI practices, we demonstrate professional awareness of emerging industry expectations and ensure the project aligns with both academic and real-world standards. Coming from to the previous contributions from students to the game Co OPERATION: MultiTurn, we will aim to provide an implementation of a similar calibre to these other implemented features. 
We intend to explain the automated level generation in a manner which should make sense to people familiar/unfamiliar with the game to ensure the methods are understood. 