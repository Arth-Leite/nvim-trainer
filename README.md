# Vim Trainer

A terminal-based Vim drill trainer. Real Neovim, real muscle memory —
a companion process watches your cursor and checks that you hit each target.

All in a **single terminal** — no more two-pane setup.

```
┌──────────────────────────────────────────┐
│  Exercise: Basic hjkl Movement           │  ← instructions (read-only)
│  Navigate to each target using h j k l   │
│  Allowed keys: h  j  k  l                │
├──────────────────────────────────────────┤
│  function greet(name) {                  │
│    ▓ const message = "Hello, " + name;   │  ← yellow target
│    console.log(message);                 │
│    return message;                       │
│  }                                       │
└──────────────────────────────────────────┘
```

## Quick start

```bash
./run.sh
```

That's it — Neovim opens with `--clean` (no heavy config) and the trainer menu
appears inside a terminal buffer. Pick an exercise and a new tab opens with
instructions at the top and the exercise text below.

## Setup

### 1. Install dependency

```bash
pip install pynvim
# or with uv:
uv sync
```

### 2. Launch

```bash
./run.sh
```

The launcher starts Neovim with `--clean` and auto-runs the trainer inside a
terminal buffer — no separate windows or extra terminals needed.

## How it works

1. The trainer writes exercise text to a temp `.js` file and opens it in Neovim.
2. One character is highlighted in **yellow** — that's your target.
3. Navigate to it using the specified Vim motions (the trainer doesn't restrict
   you — you use real Vim).
4. When your cursor lands on the target, it flashes **green** and the next
   target appears.
5. After all targets are hit, you get a stats summary (total time, avg per
   target, best/worst).

## Adding your own exercises

Edit `exercises.py`. Each exercise is a dict:

```python
{
    "id": "my-exercise",
    "name": "My Custom Drill",
    "description": "What the user should do",
    "allowed_keys": ["w", "e", "b"],   # shown as a hint only
    "text": "your\nbuffer\ncontent\n",
    "start_pos": (0, 0),               # (line, col), 0-based
    "targets": [
        (0, 4),   # (line, col), 0-based
        (1, 2),
    ],
}
```

## Testing

```bash
uv run pytest tests/ -v
```

Each exercise is verified against its `answer` field using a headless Neovim per test. Answers must visit every target or produce the expected buffer state — see `tests/harness.py` for details.

## Project structure

```
vim-trainer/
├── run.sh       # single-command launcher
├── main.py      # entry point, CLI arg parsing
├── trainer.py   # Neovim connection, highlight logic, exercise runner
├── exercises.py # exercise catalogue
├── ui.py        # terminal menu + stats display
└── README.md
```
