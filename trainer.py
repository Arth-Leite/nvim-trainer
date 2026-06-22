"""
trainer.py — Core logic for the Vim Trainer.

Connects to a running Neovim instance via its socket, loads exercise text,
highlights targets one at a time, and checks when the user's cursor lands
on each target.
"""

import os
import time
import tempfile
import threading
from dataclasses import dataclass, field
from typing import Optional

import pynvim

# ── Highlight group names ──────────────────────────────────────────────────────
HL_TARGET   = "VimTrainerTarget"    # where the user needs to go
HL_DONE     = "VimTrainerDone"      # briefly shown on success
HL_STATUS   = "VimTrainerStatus"    # status line colour

POLL_INTERVAL = 0.05  # seconds between cursor checks


# ── State ──────────────────────────────────────────────────────────────────────
@dataclass
class SessionStats:
    targets_hit: int = 0
    targets_total: int = 0
    start_time: float = field(default_factory=time.time)
    times: list = field(default_factory=list)  # seconds per target

    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time

    @property
    def avg_time(self) -> Optional[float]:
        return sum(self.times) / len(self.times) if self.times else None


class VimTrainer:
    """Wraps a live Neovim session and drives exercises."""

    def __init__(self, socket_path: str):
        self.socket_path = socket_path
        self.nvim: pynvim.Nvim = pynvim.attach("socket", path=socket_path)
        self._setup_highlights()
        self._namespace = self.nvim.api.create_namespace("vim_trainer")
        self._tmp_file: Optional[str] = None
        self._stop_event = threading.Event()

    # ── Setup ──────────────────────────────────────────────────────────────────

    def _setup_highlights(self):
        """Define custom highlight groups (safe to call multiple times)."""
        cmds = [
            # bright yellow bg + black fg for the target
            f"highlight {HL_TARGET} guibg=#FFD700 guifg=#000000 "
            f"ctermbg=226 ctermfg=0",
            # green flash on success
            f"highlight {HL_DONE} guibg=#00FF87 guifg=#000000 "
            f"ctermbg=48 ctermfg=0",
        ]
        for cmd in cmds:
            self.nvim.command(cmd)

    def _clear_highlights(self):
        buf = self.nvim.current.buffer
        self.nvim.api.buf_clear_namespace(buf, self._namespace, 0, -1)

    def _highlight_cell(self, line0: int, col0: int, hl_group: str):
        """Highlight a single character at (line0, col0) — both 0-based."""
        buf = self.nvim.current.buffer
        self.nvim.api.buf_add_highlight(
            buf, self._namespace, hl_group, line0, col0, col0 + 1
        )

    # ── File management ────────────────────────────────────────────────────────

    def _load_text(self, text: str) -> str:
        """Write text to a temp file and open it in Neovim."""
        if self._tmp_file and os.path.exists(self._tmp_file):
            os.unlink(self._tmp_file)

        fd, path = tempfile.mkstemp(suffix=".js", prefix="vim_trainer_")
        with os.fdopen(fd, "w") as f:
            f.write(text)
        self._tmp_file = path

        self.nvim.command(f"edit {path}")
        # Give Neovim a moment to load the buffer
        time.sleep(0.05)
        return path

    def _set_cursor(self, line0: int, col0: int):
        """Move Neovim cursor to (line0, col0) — converts to 1-based line."""
        self.nvim.current.window.cursor = (line0 + 1, col0)

    def _get_cursor(self):
        """Return current cursor as (line0, col0)."""
        line1, col = self.nvim.current.window.cursor
        return (line1 - 1, col)

    # ── Status line ────────────────────────────────────────────────────────────

    def _set_statusline(self, msg: str):
        """Show a message in Neovim's statusline."""
        # Escape single quotes
        safe = msg.replace("'", "''")
        self.nvim.command(f"let &statusline='{safe}'")

    def _echo(self, msg: str, hl: str = "Normal"):
        """Flash a message at the bottom of the Neovim screen."""
        safe = msg.replace("'", "\\'").replace('"', '\\"')
        self.nvim.command(f'echohl {hl} | echo "{safe}" | echohl None')

    # ── Exercise runner ────────────────────────────────────────────────────────

    def run_exercise(self, exercise: dict, on_complete=None):
        """
        Load an exercise and poll until all targets are hit.

        exercise: dict from exercises.EXERCISES
        on_complete: optional callback(stats: SessionStats)
        """
        targets = exercise["targets"]
        stats = SessionStats(targets_total=len(targets))
        checks = exercise.get("checks", [])

        self._load_text(exercise["text"])
        self._set_cursor(*exercise["start_pos"])

        # Enter normal mode cleanly
        self.nvim.command("normal! \x1b")

        self._stop_event.clear()

        self._show_header(exercise, stats)

        target_idx = 0
        target_start = time.time()
        verify_mode = False
        verify_start = 0.0

        # Highlight first target
        self._clear_highlights()
        line0, col0 = targets[target_idx]
        self._highlight_cell(line0, col0, HL_TARGET)
        self._update_status(exercise, stats, target_idx)

        try:
            while not self._stop_event.is_set():
                # ── Verify mode: wait for the user to delete the target text ──
                if verify_mode:
                    check = checks[target_idx]
                    buf = self.nvim.current.buffer
                    content = "\n".join(buf[:])

                    if check["text"] not in content:
                        verify_mode = False
                        elapsed = time.time() - target_start
                        stats.times.append(elapsed)
                        stats.targets_hit += 1

                        self._clear_highlights()
                        self._highlight_cell(line0, col0, HL_DONE)
                        self._echo(
                            f"  ✓  Deleted  ({elapsed:.2f}s)  ",
                            "DiagnosticOk",
                        )
                        time.sleep(0.25)

                        target_idx += 1
                        if target_idx >= len(targets):
                            self._clear_highlights()
                            self._show_complete(exercise, stats)
                            if on_complete:
                                on_complete(stats)
                            return stats

                        line0, col0 = targets[target_idx]
                        self._clear_highlights()
                        self._highlight_cell(line0, col0, HL_TARGET)
                        self._update_status(exercise, stats, target_idx)
                        target_start = time.time()
                    elif time.time() - verify_start > 15.0:
                        self._echo(
                            "  ⚠  Timed out — keep trying!  ",
                            "WarningMsg",
                        )
                        verify_start = time.time()

                    time.sleep(POLL_INTERVAL)
                    continue

                # ── Navigation mode: wait for cursor on target ────────────────
                cursor = self._get_cursor()

                if cursor == (line0, col0):
                    elapsed = time.time() - target_start

                    if target_idx < len(checks) and checks[target_idx] is not None:
                        # Enter verify mode — user must delete the text
                        self._clear_highlights()
                        self._highlight_cell(line0, col0, HL_DONE)
                        self._echo(
                            f"  ✓  Now delete the target!  ",
                            "DiagnosticOk",
                        )
                        self._set_statusline(
                            f"  [{stats.targets_hit}/{len(targets)}]  "
                            f"Delete it!  │  {stats.elapsed:.0f}s"
                        )
                        time.sleep(0.25)
                        self._clear_highlights()
                        self._highlight_cell(line0, col0, HL_TARGET)
                        verify_mode = True
                        verify_start = time.time()
                        time.sleep(POLL_INTERVAL)
                        continue

                    # ✅ Normal target hit (no verification needed)
                    stats.times.append(elapsed)
                    stats.targets_hit += 1

                    self._clear_highlights()
                    self._highlight_cell(line0, col0, HL_DONE)
                    self._echo(
                        f"  ✓  Target {target_idx + 1}/{len(targets)} hit "
                        f"in {elapsed:.2f}s  ",
                        "DiagnosticOk",
                    )
                    time.sleep(0.25)

                    target_idx += 1

                    if target_idx >= len(targets):
                        self._clear_highlights()
                        self._show_complete(exercise, stats)
                        if on_complete:
                            on_complete(stats)
                        return stats

                    line0, col0 = targets[target_idx]
                    self._clear_highlights()
                    self._highlight_cell(line0, col0, HL_TARGET)
                    self._update_status(exercise, stats, target_idx)
                    target_start = time.time()

                time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            self._echo("  Session interrupted. ", "WarningMsg")

        return stats

    def stop(self):
        self._stop_event.set()

    # ── UI helpers ─────────────────────────────────────────────────────────────

    def _show_header(self, exercise: dict, stats: SessionStats):
        self._echo(
            f"  ▶  {exercise['name']}  —  {exercise['description']}  ",
            "DiagnosticInfo",
        )

    def _update_status(self, exercise: dict, stats: SessionStats, idx: int):
        total = len(exercise["targets"])
        keys  = "  ".join(exercise.get("allowed_keys", []))
        line0, col0 = exercise["targets"][idx]
        msg = (
            f"  [{stats.targets_hit}/{total}]  "
            f"Target → L{line0 + 1}:C{col0 + 1}  "
            f"│  keys: {keys}  "
            f"│  {stats.elapsed:.0f}s elapsed  "
        )
        self._set_statusline(msg)

    def _show_complete(self, exercise: dict, stats: SessionStats):
        avg = f"{stats.avg_time:.2f}s" if stats.avg_time else "—"
        total = f"{stats.elapsed:.1f}s"
        self._echo(
            f"  🎉  Done! {stats.targets_hit} targets  │  "
            f"total {total}  │  avg {avg}/target  ",
            "DiagnosticOk",
        )
        self._set_statusline(
            f"  ✓ {exercise['name']} complete — "
            f"{stats.targets_hit} targets in {total}  "
        )

    def cleanup(self):
        """Remove highlights and temp file."""
        try:
            self._clear_highlights()
        except Exception:
            pass
        if self._tmp_file and os.path.exists(self._tmp_file):
            os.unlink(self._tmp_file)
            self._tmp_file = None
