# Vim Trainer

Terminal-based Vim drill trainer.

## Quick start

```bash
uv sync
./run.sh
```

Launches Neovim (`--clean`) with a terminal buffer running the trainer menu.

## Exercises

Edit `exercises.py`. Schema:

```python
{
    "id": "my-exercise",
    "name": "My Custom Drill",
    "category": "Movement",
    "description": "What the user should do",
    "allowed_keys": ["w", "e", "b"],
    "check_mode": "cursor",          # "cursor" or "content"
    "text": "your\nbuffer\ncontent\n",
    "start_pos": (0, 0),             # (line, col) 0-based
    "targets": [
        (0, 4),                      # (line, col) or (line, col_start, col_end)
    ],
    "checks": [],                    # content-mode verification items
    "answer": "wej0",                # keystrokes for test validation
}
```

## Tests

```bash
uv run pytest tests/ -v
```

Each exercise's `answer` is fed to a headless Neovim — cursor position or buffer content is verified against the exercise targets.

## Project structure

```
├── main.py       # entry point
├── trainer.py    # Neovim connection, exercise runner
├── exercises.py  # exercise catalogue
├── ui.py         # terminal menu
├── run.sh        # launcher
└── tests/
    ├── conftest.py
    ├── harness.py
    └── test_exercises.py
```
