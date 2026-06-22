# Vim Trainer

A terminal-based Vim drill trainer. Real Neovim, real muscle memory —
a companion process watches your cursor and checks that you hit each target.

```
┌─────────────────────────────┐   ┌────────────────────────────┐
│  pane 1 — Neovim            │   │  pane 2 — Trainer UI       │
│                             │   │                            │
│  function greet(name) {     │   │  ╔══════════════════════╗  │
│  █ const message = "Hello"  │   │  ║   VIM TRAINER        ║  │
│  ▓▓▓▓▓▓▓▓ ← yellow target  │   │  ╚══════════════════════╝  │
│    console.log(message);    │   │                            │
│    return message;          │   │  [1/4] Target → L2:C6      │
│  }                          │   │  keys: w  e  b             │
│                             │   │  12s elapsed               │
└─────────────────────────────┘   └────────────────────────────┘
```

## Setup

### 1. Install dependency

```bash
pip install pynvim
```

### 2. Start Neovim with a known socket

```bash
NVIM_LISTEN_ADDRESS=/tmp/nvim.sock nvim
```

### 3. In a second pane, run the trainer

```bash
python3 main.py
# or specify a custom socket:
python3 main.py --socket /tmp/nvim.sock
```

### Quick tmux setup (copy-paste ready)

```bash
# Split into two panes
tmux new-session -s vim-trainer \; \
  send-keys 'NVIM_LISTEN_ADDRESS=/tmp/nvim.sock nvim' Enter \; \
  split-window -h \; \
  send-keys 'cd /path/to/vim-trainer && python3 main.py' Enter
```

## How it works

1. The trainer writes exercise text to a temp `.js` file and opens it in your Neovim.
2. One character is highlighted in **yellow** — that's your target.
3. Navigate to it using the specified Vim motions (the trainer doesn't restrict you — you use real Vim).
4. When your cursor lands on the target, it flashes **green** and the next target appears.
5. After all targets are hit, you get a stats summary (total time, avg per target, best/worst).

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

## Project structure

```
vim-trainer/
├── main.py       # entry point, CLI arg parsing
├── trainer.py    # Neovim connection, highlight logic, exercise runner
├── exercises.py  # exercise catalogue
├── ui.py         # terminal menu + stats display
└── README.md
```
