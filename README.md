# Aging SynBio Scout

An AI research engine for generating iGEM synthetic biology project ideas focused on aging biology.

## Quick Start

### Installation
1. Clone the repository.
2. Create a virtual environment: `python3 -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Set up your `.env` file (see `.env.example`).

### Running the Pipeline

#### Full Pipeline
Run the full research pipeline on recent papers:
```bash
python3 main.py --mode full --limit 5
```

#### Validation Modes
Use these lightweight commands for partial checks and faster debugging:

**1. Smoke Test**
Quick health check: load model, retrieve 1 paper, run literature + hypothesis generation.
```bash
python3 main.py --mode smoke --limit 1 --skip-notion
```

**2. Test Circuit Generation**
Validate only the circuit generation stage with a sample input.
```bash
python3 main.py --mode test-circuit --skip-notion
```

**3. Test Idea Payload**
Validate Idea_DB payload creation and Notion mapping. Prints the payload instead of saving if `--skip-notion` is set.
```bash
python3 main.py --mode test-idea --limit 1 --skip-notion
```

## CLI Arguments

- `--mode`: Execution mode (`full`, `smoke`, `test-circuit`, `test-idea`). Default is `full`.
- `--limit`: Limit the number of papers to process.
- `--skip-notion`: Skip saving results to Notion. Useful for dry runs.
- `--source`: (Optional) Specific paper source to use.
- `--paper-title`: (Optional) Specific paper title to analyze.
