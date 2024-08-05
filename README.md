# SAUCE 🍝: Synchronous and Asynchronous User-Customizable Environment for Multi-Agent LLM Interaction

## Background:

The system we are developing aims to facilitate the execution and replication of experiments in the fields of Social Psychology and Behavioral Economics, utilizing LLM (Large language model) as participant.

## Explanation:

Our goal is to create an advanced experimental system that enables researchers to conduct and reproduce experiments with ease, specifically focusing on the domains of Social Psychology and Behavioral Economics. By leveraging LLM, we aim to reproduce experiment result using those LLMs.

## Requirements

- python >= 3.9
- basic requirements are in `requirements.txt`
- async requirements are in `requirements_asynchronous.txt`

## Installation

```bash
pip install -r requirements.txt
pip install -r requirements_asynchronous.txt
```

## Basic Usage

Running the system using the CLI

```bash
python main.py PATH_TO_CONFIG_FILE
```

Here is all the CLI commands

```text
usage: SAUCE [-h] [-o OUTPUT] [--json | --no-json] [--output-json OUT_JSON] [-c | --console | --no-console] [--output-log OUT_LOG] [--batch-mode | --no-batch-mode | -bm]
             [-v | --verbose | --no-verbose]
             config

Synchronous and Asynchronous User-Customizable Environment for Multi-Agent LLM Interaction

positional arguments:
  config                what config to run

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Where to save the experiment output
  --json, --no-json     boolean field indicting rather saved or not to save a json version of the logs (default: False)
  --output-json OUT_JSON
                        File where to save the json form of the raw logs
  -c, --console, --no-console
                        Enable output to std output (default: True)
  --output-log OUT_LOG  Where to save the created log
  --batch-mode, --no-batch-mode, -bm
                        Change the running exp to use Batch mode person (default: False)
  -v, --verbose, --no-verbose

```

## Features:

Our system will focus on the following key features to enhance the experimentation process in the target domain:

1. Reproducibility and Execution: The system will enable easy reproduction and execution of experiments, ensuring that researchers can consistently replicate their studies and obtain reliable results.
2. Multi-Model Integration: To enhance the capabilities of the experimental system, we will incorporate multiple LLM models. This integration will allow for a broader range of language models, enabling more comprehensive and nuanced participant interactions.
3. Ease of Use: We prioritize simplicity and usability in our system's design. Researchers will benefit from an intuitive interface that simplifies experiment setup, configuration, and management. This approach reduces the learning curve and streamlines the overall research process, making it effortless for researchers to navigate and utilize the system effectively.

By focusing on these features, our LLM-based experimental system aims to provide researchers in the target domain with a robust, versatile, and user-friendly platform for conducting and reproducing experiments effectively and efficiently.

## Software Design:

In order to implement the desired features and functionalities of our LLM-based experimental system, careful software design is essential. The design encompasses various classes, methods, properties, and interactions that form the foundation of the system's architecture.

### Classes

- <u><b>Person:</b></u> An abstract class representing a participant utilizing LLM in the experiment. It encapsulates the common attributes and behaviors of participants.
- <u><b>Session Room:</b></u> Represents the physical or virtual space where the experiments take place. It serves as the environment where participants interact with each other.
- <u><b>Host:</b></u> An abstract representation of the experiment conductor who guides and manages the interactions between participants. It determines the rules and conditions of the experiment and controls the timing and sequencing of participant interactions.
- <u><b>EndType:</b></u> An abstract representation of the criteria or condition that determines the conclusion or termination of the experiment. It defines what constitutes the end of the experiment and triggers any necessary actions or data collection.
- <u><b>Experiment:</b></u> This class serves as a container for the experiment blueprint. It encapsulates the experimental design, instructions, stimuli, and any other relevant information needed for conducting the experiment.

### Considerations for Development: Additional Information to Keep in Mind

- In the bootstrap we will use the OpenAI model, but we need to design the system to handle any model (Bard, Lima, HugginFace Agents etc.)
- Keep it simple, and remember to keep parts of the system decoupled, and indpended from each other.
- Add batch running system (WIP)
- Session room with user interface (maybe chat? GUI?)
