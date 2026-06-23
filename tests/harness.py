import re
from typing import Any


_SPECIAL_KEY_RE = re.compile(r"(<[^>]+>)|(.)")

# Tokens that are always allowed in any exercise
_UNIVERSAL_TOKENS = set("0123456789")

# Commands that consume the next single token as a text argument
_SINGLE_ARG_PREFIXES = {"f", "F", "t", "T", "r"}

# Commands that consume all tokens until a terminator
_TEXT_UNTIL_TERMINATOR = {"/", "?", ":"}
_TERMINATORS = {"<CR>", "<Esc>"}

# Register-name prefixes (consume next token as register name)
_REGISTER_PREFIXES = {"q", '"'}

# Single-key commands that enter insert mode
_INSERT_TRIGGERS = {"i", "I", "a", "A", "o", "O", "s", "S", "C"}

# Operators that take a motion/text-object argument (c also enters insert mode)
_OPERATORS_WITH_MOTION = {"c", "d", "y"}


def validate_answer_tokens(exercise: dict[str, Any]) -> tuple[bool, str]:
    """Check that every keystroke in the answer is covered by allowed_keys.

    Understands Vim command structure:
      - f/F/t/T/r consume the next character as a text argument
      - / ? : consume all tokens until <CR> (search/command text)
      - i/a/o/O/s/S/C enter insert mode; everything until <Esc> is text
      - c/d/y are operators; c also enters insert mode after its motion
      - g followed by u/U is treated as a compound command
      - Digits (count prefixes) are always allowed.
    """
    allowed_keys = exercise["allowed_keys"]
    answer = exercise["answer"]

    # Build the set of individually-allowed tokens from the compound allowed_keys
    allowed_tokens = set(_UNIVERSAL_TOKENS)
    for key in allowed_keys:
        allowed_tokens.update(tokenise_answer(key))

    tokens = tokenise_answer(answer)
    i = 0
    while i < len(tokens):
        token = tokens[i]

        # ── Text commands  / ? :  (skip everything until terminator) ──
        if token in _TEXT_UNTIL_TERMINATOR:
            if token not in allowed_tokens:
                return False, f"'{token}' at position {i} not in allowed_keys"
            i += 1
            while i < len(tokens) and tokens[i] not in _TERMINATORS:
                i += 1
            if i < len(tokens):
                i += 1  # skip the terminator
            continue

        # ── Single-arg prefixes  f F t T r ──
        if token in _SINGLE_ARG_PREFIXES:
            if token not in allowed_tokens:
                return False, f"'{token}' at position {i} not in allowed_keys"
            i += 2  # skip prefix + its text argument
            continue

        # ── Register prefixes  q "  (consume next token as register name) ──
        if token in _REGISTER_PREFIXES:
            if token not in allowed_tokens:
                return False, f"'{token}' at position {i} not in allowed_keys"
            i += 2  # skip prefix + register name
            continue

        # ── Insert triggers  i I a A o O s S C ──
        if token in _INSERT_TRIGGERS:
            if token not in allowed_tokens:
                return False, f"'{token}' at position {i} not in allowed_keys"
            i += 1
            while i < len(tokens) and tokens[i] != "<Esc>":
                i += 1
            i += 1  # skip <Esc>
            continue

        # ── Operators with motion  c d y ──
        if token in _OPERATORS_WITH_MOTION:
            if token not in allowed_tokens:
                return False, f"'{token}' at position {i} not in allowed_keys"
            i += 1  # consume operator, now pointing at motion start
            if i < len(tokens):
                nxt = tokens[i]
                if nxt in {"i", "a"}:
                    i += 2  # text object: i( , i" , a( , etc.
                elif nxt == "g":
                    i += 2  # g-prefixed motion: gn, gU, gu, etc.
                else:
                    i += 1  # single-token motion: w, e, b, $, j, etc.
            if token == "c":
                # c enters insert mode after its motion
                while i < len(tokens) and tokens[i] != "<Esc>":
                    i += 1
                i += 1  # skip <Esc>
            continue

        # ── Compound: g always takes a second character ──
        if token == "g":
            if token not in allowed_tokens:
                return False, f"'g' at position {i} not in allowed_keys"
            i += 1
            if i < len(tokens):
                i += 1  # consume the second char (gu, gU, gn, etc.)
            continue

        # ── Regular token ──
        if token not in allowed_tokens:
            return False, f"'{token}' at position {i} not in allowed_keys"
        i += 1

    return True, "OK"


def tokenise_answer(answer: str) -> list[str]:
    """Split an answer string into individual Vim key tokens."""
    return [m.group() for m in _SPECIAL_KEY_RE.finditer(answer)]


def _resolve_special(token: str) -> str:
    """Map a special-key token to the actual key Neovim expects."""
    mapping = {
        "<CR>": "\n",
        "<Esc>": "\x1b",
        "<Tab>": "\t",
        "<BS>": "\x7f",
        # Chord keys (control + letter)
        "<C-a>": "\x01", "<C-b>": "\x02", "<C-c>": "\x03",
        "<C-d>": "\x04", "<C-e>": "\x05", "<C-f>": "\x06",
        "<C-g>": "\x07", "<C-h>": "\x08", "<C-i>": "\x09",
        "<C-j>": "\x0a", "<C-k>": "\x0b", "<C-l>": "\x0c",
        "<C-m>": "\x0d", "<C-n>": "\x0e", "<C-o>": "\x0f",
        "<C-p>": "\x10", "<C-q>": "\x11", "<C-r>": "\x12",
        "<C-s>": "\x13", "<C-t>": "\x14", "<C-u>": "\x15",
        "<C-v>": "\x16", "<C-w>": "\x17", "<C-x>": "\x18",
        "<C-y>": "\x19", "<C-z>": "\x1a",
    }
    # Normalise case for chord keys (C-d == C-D)
    if token.startswith("<C-") and token.endswith(">"):
        lower = "<C-" + token[3:-1].lower() + ">"
        return mapping.get(lower, token)
    return mapping.get(token, token)


class ExerciseHarness:
    """Drives a headless Neovim instance and verifies exercise answers."""

    def __init__(self, nvim):
        self.nvim = nvim

    def load_exercise(self, ex):
        """Set up Neovim with the exercise buffer."""
        nvim = self.nvim
        nvim.command("enew!")
        lines = ex["text"].split("\n")
        while lines and lines[-1] == "":
            lines.pop()
        nvim.api.buf_set_lines(0, 0, -1, True, lines)
        self._set_cursor(ex["start_pos"])
        # Setup layout if specified
        layout = ex.get("layout", "standard")
        if layout == "windows":
            self._setup_window_layout()
        elif layout == "tabs":
            self._setup_tab_layout()
        # Run any exercise-specific setup commands
        for cmd in ex.get("setup_commands", []):
            nvim.command(cmd)
        # Navigation-only exercises get a read-only buffer
        if ex.get("check_mode", "cursor") != "content":
            nvim.current.buffer.options["modifiable"] = False
        nvim.command("set hlsearch")
        nvim.api.get_mode()

    def _setup_window_layout(self):
        """Create a multi-window layout for window-navigation exercises."""
        nvim = self.nvim
        nvim.command("tabnew")
        nvim.command("vsplit")
        nvim.command("wincmd l")
        nvim.command("split")
        nvim.command("wincmd h")

    def _setup_tab_layout(self):
        """Create multiple tabs for tab-navigation exercises."""
        nvim = self.nvim
        nvim.command("tabnew")
        nvim.command("tabnew")

    def play_and_verify(self, ex):
        """Feed the answer and verify the final state."""
        raw = self._build_raw_keys(ex["answer"])
        n_consumed = self.nvim.api.input(raw)
        assert n_consumed == len(raw), (
            f"Only {n_consumed}/{len(raw)} answer bytes were consumed"
        )

        check_mode = ex.get("check_mode", "cursor")
        if check_mode == "cursor":
            self._verify_cursor_final(ex)
        elif check_mode == "content":
            self._verify_content_final(ex)

    def _build_raw_keys(self, answer: str) -> str:
        """Convert an answer string (with <CR> <Esc> etc.) to raw keys."""
        tokens = tokenise_answer(answer)
        return "".join(_resolve_special(t) for t in tokens)

    def _verify_cursor_final(self, ex):
        """Check cursor ended at the last target."""
        targets = [t for t in ex["targets"] if len(t) == 2]
        expected = targets[-1]
        row, col = self.nvim.api.win_get_cursor(0)
        row -= 1
        assert row == expected[0] and col == expected[1], (
            f"Final cursor ({row},{col}) != expected last target "
            f"({expected[0]},{expected[1]})"
        )

    def _verify_content_final(self, ex):
        """Check the final buffer state matches the last state check."""
        checks = ex.get("checks", [])
        if not checks:
            return
        last = checks[-1]
        buf = self.nvim.api.buf_get_lines(0, 0, -1, True)
        text = "\n".join(buf)
        if last["type"] == "delete":
            assert last["text"] not in text, (
                f"'{last['text']}' should have been deleted\n{text}"
            )
        elif last["type"] == "state":
            assert text == last["expected"], (
                f"Final buffer mismatch.\n"
                f"Expected:\n{last['expected']}\n"
                f"Got:\n{text}"
            )

    def _set_cursor(self, pos):
        row, col = pos
        self.nvim.api.win_set_cursor(0, (row + 1, col))
