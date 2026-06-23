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


# ── Exercise-control exceptions ────────────────────────────────────────────────

class RestartExercise(Exception):
    """Raised when the user requests to restart the current exercise."""

class QuitToMenu(Exception):
    """Raised when the user requests to return to the exercise menu."""


class VimTrainer:
    """Wraps a live Neovim session and drives exercises."""

    def __init__(self, socket_path: str = "", nvim: Optional[pynvim.Nvim] = None):
        if nvim is not None:
            self.nvim = nvim
        else:
            self.socket_path = socket_path
            self.nvim = pynvim.attach("socket", path=socket_path)
        self.nvim.command("set laststatus=2")
        self.nvim.command("filetype on")
        self.nvim.command("syntax on")
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

    def _resolve_target(self, target):
        """Unpack target to (line, col_start, col_end). Supports 2 or 3 element tuples."""
        if len(target) == 3:
            return target[0], target[1], target[2]
        return target[0], target[1], target[1] + 1

    def _highlight_target(self, target, hl_group: str):
        """Highlight a target (single char or range)."""
        line0, col0, col1 = self._resolve_target(target)
        buf = self.nvim.current.buffer
        self.nvim.api.buf_add_highlight(
            buf, self._namespace, hl_group, line0, col0, col1
        )

    def _cursor_on_target(self, target) -> bool:
        """Check if the user's cursor is anywhere inside a target range."""
        line0, col0, col1 = self._resolve_target(target)
        cursor_line, cursor_col = self._get_cursor()
        return cursor_line == line0 and col0 <= cursor_col < col1

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

    # ── Tab layout ───────────────────────────────────────────────────────────

    def _setup_exercise_layout(self, exercise: dict):
        """Open a new tab with instructions at the top and exercise below."""
        layout = exercise.get("layout", "standard")
        if layout == "windows":
            self._setup_window_layout(exercise)
            return
        elif layout == "tabs":
            self._setup_tab_layout(exercise)
            return

        self.nvim.command("tabnew")
        time.sleep(0.05)
        self.nvim.command("new")
        time.sleep(0.05)

        buf = self.nvim.current.buffer
        keys = "  ".join(exercise.get("allowed_keys", []))
        lines = [
            f"  Exercise: {exercise['name']}",
            f"  {exercise['description']}",
            f"  Allowed keys: {keys}",
            f"  Commands:  :Restart  :Quit",
            "",
        ]
        buf[:] = lines
        buf.options["modifiable"] = False

        self.nvim.command("resize 6")
        self.nvim.command("wincmd j")
        self._setup_controls()
        time.sleep(0.05)

    def _setup_window_layout(self, exercise: dict):
        """Create a multi-window layout for window-navigation exercises."""
        self.nvim.command("tabnew")
        time.sleep(0.05)
        self.nvim.command("enew!")
        self.nvim.command("vsplit")
        time.sleep(0.05)
        self.nvim.command("wincmd l")
        self.nvim.command("enew!")
        self.nvim.command("split")
        time.sleep(0.05)
        self.nvim.command("enew!")
        self.nvim.command("wincmd h")
        self._setup_controls()

    def _setup_tab_layout(self, exercise: dict):
        """Create multiple tabs for tab-navigation exercises."""
        self.nvim.command("tabnew")
        time.sleep(0.05)
        self.nvim.command("tabnew")
        time.sleep(0.05)
        self.nvim.command("tabfirst")
        self._setup_controls()

    def _setup_controls(self):
        """Define nvim commands for controlling the exercise."""
        cmds = [
            'command! -buffer Restart let g:trainer_action = "restart"',
            'command! -buffer Quit let g:trainer_action = "quit"',
        ]
        for cmd in cmds:
            self.nvim.command(cmd)

    def _check_for_actions(self) -> str | None:
        """Check if the user triggered a control command in nvim."""
        try:
            action = self.nvim.eval('get(g:, "trainer_action", "")')
            if action:
                self.nvim.command("unlet! g:trainer_action")
                return action
        except Exception:
            pass
        return None

    def _teardown_exercise_layout(self):
        """Close the exercise tab and return to the terminal-buffer tab."""
        self.nvim.command("tabclose")
        self.nvim.command("startinsert")

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
        # Store in a Vim variable and reference via %{} to bypass &statusline's special < > syntax
        safe = msg.replace("'", "''")
        self.nvim.command(f"let g:trainer_status='{safe}'")
        self.nvim.command("set statusline=%{g:trainer_status}")

    def _echo(self, msg: str, hl: str = "Normal"):
        """Flash a message at the bottom of the Neovim screen."""
        safe = msg.replace("'", "\\'").replace('"', '\\"')
        self.nvim.command(f'echohl {hl} | echo "{safe}" | echohl None')

    # ── Exercise runner ────────────────────────────────────────────────────────

    def run_exercise(self, exercise: dict, on_complete=None):
        targets = exercise["targets"]
        stats = SessionStats(targets_total=len(targets))
        checks = exercise.get("checks", [])
        check_mode = exercise.get("check_mode", "cursor")

        self._setup_exercise_layout(exercise)
        try:
            self._load_text(exercise["text"])
            self._set_cursor(*exercise["start_pos"])
            self.nvim.command("normal! \x1b")

            # Run any exercise-specific setup commands
            for cmd in exercise.get("setup_commands", []):
                self.nvim.command(cmd)
            # Navigation-only exercises get a read-only buffer
            if exercise.get("check_mode", "cursor") != "content":
                self.nvim.current.buffer.options["modifiable"] = False

            self._stop_event.clear()
            self._show_header(exercise, stats)

            target_idx = 0
            target_start = time.time()
            verify_mode = check_mode == "content"
            verify_start = time.time() if verify_mode else 0.0

            self._clear_highlights()
            self._highlight_target(targets[target_idx], HL_TARGET)
            self._update_status(exercise, stats, target_idx)

            try:
                while not self._stop_event.is_set():
                    action = self._check_for_actions()
                    if action == "restart":
                        raise RestartExercise()
                    if action == "quit":
                        raise QuitToMenu()

                    # ── Verify mode ─────────────────────────────────────────────
                    if verify_mode:
                        check = checks[target_idx]
                        buf = self.nvim.current.buffer
                        content = "\n".join(buf[:])
                        check_type = check.get("type", "delete")

                        passed = False
                        if check_type == "state":
                            passed = content == check["expected"]
                            if not passed:
                                self.nvim.vars["debug_actual"] = content[:600]
                                self.nvim.vars["debug_expected"] = check["expected"][:600]
                                self.nvim.vars["debug_actual_len"] = len(content)
                                self.nvim.vars["debug_expected_len"] = len(check["expected"])
                                self.nvim.vars["debug_actual_lines"] = len(buf[:])
                        elif check_type == "change":
                            passed = check["text"] in content
                        else:
                            passed = check["text"] not in content

                        if passed:
                            verify_mode = False
                            elapsed = time.time() - target_start
                            stats.times.append(elapsed)
                            stats.targets_hit += 1

                            self._clear_highlights()
                            self._highlight_target(targets[target_idx], HL_DONE)
                            if check_type == "state":
                                msg = "Correct"
                            else:
                                msg = "Changed" if check_type == "change" else "Deleted"
                            self._echo(
                                f"  ✓  {msg}  ({elapsed:.2f}s)  ",
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

                            self._clear_highlights()
                            self._highlight_target(targets[target_idx], HL_TARGET)
                            self._update_status(exercise, stats, target_idx)
                            target_start = time.time()
                            if check_mode == "content":
                                verify_mode = True
                                verify_start = time.time()
                        elif time.time() - verify_start > 15.0:
                            self._echo(
                                "  ⚠  Timed out — keep trying!  ",
                                "WarningMsg",
                            )
                            verify_start = time.time()

                        time.sleep(POLL_INTERVAL)
                        continue

                    # ── Navigation mode ───────────────────────────────────────
                    if self._cursor_on_target(targets[target_idx]):
                        elapsed = time.time() - target_start

                        if target_idx < len(checks) and checks[target_idx] is not None:
                            check_type = checks[target_idx].get("type", "delete")
                            action = "Change it!" if check_type == "change" else "Delete it!"
                            if check_type == "state":
                                action = "Fix it!"
                            self._clear_highlights()
                            self._highlight_target(targets[target_idx], HL_DONE)
                            self._echo(
                                f"  ✓  Now {action}  ",
                                "DiagnosticOk",
                            )
                            self._set_statusline(
                                f"  [{stats.targets_hit}/{len(targets)}]  "
                                f"{action}  │  {stats.elapsed:.0f}s"
                            )
                            time.sleep(0.25)
                            self._clear_highlights()
                            self._highlight_target(targets[target_idx], HL_TARGET)
                            verify_mode = True
                            verify_start = time.time()
                            time.sleep(POLL_INTERVAL)
                            continue

                        stats.times.append(elapsed)
                        stats.targets_hit += 1

                        self._clear_highlights()
                        self._highlight_target(targets[target_idx], HL_DONE)
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

                        self._clear_highlights()
                        self._highlight_target(targets[target_idx], HL_TARGET)
                        self._update_status(exercise, stats, target_idx)
                        target_start = time.time()

                    time.sleep(POLL_INTERVAL)

            except KeyboardInterrupt:
                self._echo("  Session interrupted. ", "WarningMsg")
            except RestartExercise:
                raise
            except QuitToMenu:
                raise

            return stats
        finally:
            self._clear_highlights()
            if stats.targets_hit > 0:
                time.sleep(1)
            self._teardown_exercise_layout()

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
        line0, col0, col1 = self._resolve_target(exercise["targets"][idx])
        label = f"L{line0 + 1}:C{col0 + 1}"
        if col1 > col0 + 1:
            label += f"-{col1}"
        msg = (
            f"  [{stats.targets_hit}/{total}]  "
            f"Target → {label}  "
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
