import re


_SPECIAL_KEY_RE = re.compile(r"(<[^>]+>)|(.)")


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
    }
    return mapping.get(token, token)


class TestHarness:
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
        nvim.command("set hlsearch")
        nvim.api.get_mode()

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
