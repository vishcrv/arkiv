# Arkiv — stage 01 · CLI

First stage of Arkiv: a personal book collection manager driven entirely from the terminal.

Two entry points, one data layer:

- `main.py` — argparse CLI, scripting-friendly (`python main.py list-books`, `python main.py add-book ...`).
- `cli.py` — interactive menu loop for readers who'd rather browse than type flags.

Both share `store/db.py`, which reads and writes a single `data.json` on local disk. No database, no server, no dependencies beyond the standard library.

## Architecture

[`docs/diagrams/architecture.html`](docs/diagrams/architecture.html)

Terminal → Python CLI → JSON store → `data.json` on disk. That's the whole stack at this stage.

## Running it

```bash
python main.py help            # list commands
python main.py list-books      # example
python cli.py                  # interactive menu
```

## Next stages

Arkiv grew from here into a React frontend, then a Salesforce backend, then MySQL. See the `frontend`, `saleforce`, and `main` branches for each step.
