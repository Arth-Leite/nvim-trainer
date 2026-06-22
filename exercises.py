"""
Exercise catalogue for vim-trainer.

Each exercise defines:
  - id          : unique slug
  - name        : display name
  - description : what the user should do
  - allowed_keys: hint shown in the UI (not enforced — real Vim is used)
  - text        : the buffer content loaded into Neovim
  - targets     : ordered list of (0-based line, 0-based col) the user must visit
  - start_pos   : where the cursor begins (line, col)  [0-based]

Lines in `text` are 0-indexed in targets (matching Neovim's 0-based col /
1-based line — we store everything 0-based internally and convert when
talking to the Neovim API).
"""

EXERCISES = [

    # ── Basic hjkl ────────────────────────────────────────────────────────────
    {
        "id": "hjkl-basic",
        "name": "Basic hjkl Movement",
        "description": "Navigate to each highlighted target using ONLY h j k l.",
        "allowed_keys": ["h", "j", "k", "l"],
        "text": """\
function greet(name) {
  const message = "Hello, " + name;
  console.log(message);
  return message;
}

greet("World");
""",
        "start_pos": (0, 0),
        "targets": [
            (0, 9),   # 'n' in greet(name)
            (1, 16),  # '"' opening quote
            (2, 10),  # 'l' in log
            (6, 6),   # '"' in greet("World")
        ],
    },

    # ── Word motions ──────────────────────────────────────────────────────────
    {
        "id": "word-motions",
        "name": "Word Motions  w / e / b",
        "description": "Jump to each target using w, e, or b. No hjkl!",
        "allowed_keys": ["w", "e", "b", "W", "E", "B"],
        "text": """\
const result = fetchData(apiUrl, options);
const filtered = result.filter(item => item.active);
const names = filtered.map(item => item.name);
""",
        "start_pos": (0, 0),
        "targets": [
            (0, 6),   # 'r' result
            (0, 15),  # 'f' fetchData
            (0, 25),  # 'a' apiUrl
            (1, 6),   # 'f' filtered
            (2, 16),  # 'm' map
        ],
    },

    # ── Line-end motions ──────────────────────────────────────────────────────
    {
        "id": "line-ends",
        "name": "Line End Motions  0 / $ / _",
        "description": "Reach the targets at the start/end of lines using 0, $, or _.",
        "allowed_keys": ["0", "$", "_", "j", "k"],
        "text": """\
  const x = computeValue(input);
    let y = x * 2 + offset;
const z = Math.sqrt(x * x + y * y);
""",
        "start_pos": (0, 6),
        "targets": [
            (0, 30),  # ')' end of line 0
            (0, 2),   # 'c' first non-blank line 0
            (1, 26),  # ';' end of line 1
            (1, 4),   # 'l' first non-blank line 1
            (2, 0),   # 'c' hard start line 2
        ],
    },

    # ── f / F find ────────────────────────────────────────────────────────────
    {
        "id": "find-char",
        "name": "Find Character  f / F / ;",
        "description": "Use f{char} and F{char} to jump directly to the targets.",
        "allowed_keys": ["f", "F", ";", ","],
        "text": """\
import { useState, useEffect, useCallback } from 'react';
const [count, setCount] = useState(0);
useEffect(() => { setCount(c => c + 1); }, [count]);
""",
        "start_pos": (0, 0),
        "targets": [
            (0, 9),   # 'u' useState
            (0, 19),  # 'u' useEffect
            (0, 31),  # 'u' useCallback
            (1, 7),   # 'c' count
            (2, 19),  # 's' setCount
        ],
    },

    # ── Search ────────────────────────────────────────────────────────────────
    {
        "id": "search",
        "name": "Search  / and n / N",
        "description": "Use /pattern to find targets and n / N to repeat.",
        "allowed_keys": ["/", "?", "n", "N", "*", "#"],
        "text": """\
function processOrder(order) {
  validateOrder(order);
  const total = calculateTotal(order.items);
  applyDiscount(order, total);
  saveOrder(order);
  return order;
}
""",
        "start_pos": (0, 0),
        "targets": [
            (1, 2),   # 'v' validateOrder
            (2, 14),  # 'c' calculateTotal
            (3, 2),   # 'a' applyDiscount
            (4, 2),   # 's' saveOrder
        ],
    },

    # ── Delete operator ───────────────────────────────────────────────────────
    {
        "id": "delete-ops",
        "name": "Delete Operators  dw / dd / D / x",
        "description": "Navigate to the highlighted word and DELETE it. Use dw, dd, D, or x.",
        "allowed_keys": ["d", "w", "d", "d", "D", "x", "h", "j", "k", "l"],
        "text": """\
function start() {
  let ddeleteWord = "useless";
  const keepMe = "important";
  let extrasWord = "redundant";
  const deleteLines = "remove this line";
}
""",
        "start_pos": (0, 0),
        "targets": [
            (1, 6),   # 'd' in 'ddeleteWord' — delete with dw
            (3, 11),   # 's' in 'extrasWord' — delete with dw
            (4, 18),   # 's' in 'deleteLines' — delete with dd (last, so no line-shift issues)
        ],
        # Optional per-target checks. When present, the trainer waits for the
        # given text to leave the buffer before advancing (instead of advancing
        # as soon as the cursor lands on the target).
        "checks": [
            {"type": "delete", "text": "ddeleteWord"},
            {"type": "delete", "text": "extrasWord"},
            {"type": "delete", "text": "deleteLines"},
        ],
    },
]

# Quick lookup by id
EXERCISE_MAP = {ex["id"]: ex for ex in EXERCISES}
