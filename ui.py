"""
ui.py — Terminal menu for the Vim Trainer (vim-hero style).
"""
import os
import sys
import time
import shutil

# ── 256‑colour ANSI palette ─────────────────────────────────────────────────────
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"

RED     = "\033[38;5;196m"
GREEN   = "\033[38;5;82m"
YELLOW  = "\033[38;5;226m"
BLUE    = "\033[38;5;75m"
MAGENTA = "\033[38;5;201m"
CYAN    = "\033[38;5;51m"
WHITE   = "\033[38;5;255m"
ORANGE  = "\033[38;5;214m"
PINK    = "\033[38;5;212m"

BG_DARK   = "\033[48;5;235m"
BG_TEAL   = "\033[48;5;30m"
BG_PURPLE = "\033[48;5;92m"
BG_GREEN  = "\033[48;5;65m"
BG_ORANGE = "\033[48;5;130m"
BG_GRAY   = "\033[48;5;240m"

CLEAR = "\033[2J\033[H"

# ── Exercise categories (start, end — end exclusive) ────────────────────────────
CATEGORIES = [
    ("Movement",          0,  6, BG_TEAL),
    ("Find & Search",     6, 10, BG_PURPLE),
    ("Delete & Change",  10, 14, BG_ORANGE),
    ("Pairs & Jumps",    14, 18, BG_TEAL),
    ("Text Objects",     18, 21, BG_PURPLE),
    ("Visual & Cmds",    21, 26, BG_ORANGE),
    ("Advanced",         26, 29, BG_GRAY),
]


def clr():
    print(CLEAR, end="")


def header():
    print(f"  {BOLD}{BG_TEAL}{WHITE}  ╭──────────────────────────────╮  {RESET}")
    print(f"  {BOLD}{BG_TEAL}{WHITE}  │     V I M   T R A I N E R     │  {RESET}")
    print(f"  {BOLD}{BG_TEAL}{WHITE}  ╰──────────────────────────────╯  {RESET}")


def _menu_prompt():
    print(f"  {BOLD}Pick a lesson{RESET}  {DIM}(number, or q to quit){RESET}: ", end="")


def show_exercises_categorized(exercises):
    for cat_name, start, end, bg in CATEGORIES:
        print(f"\n  {BOLD}{bg}{WHITE}  {cat_name}{RESET}")
        for i in range(start, end):
            ex = exercises[i]
            num = i + 1
            keys = "  ".join(ex.get("allowed_keys", [])[:5])
            print(f"    {GREEN}{num:>2}{RESET}  {ex['name']:<32}  {YELLOW}{keys}{RESET}")


def show_stats(stats, exercise_name: str):
    print(f"  {'─' * 42}")
    print(f"\n  {BOLD}{GREEN}✓  Exercise complete!{RESET}\n")
    print(f"  Lesson   : {BOLD}{exercise_name}{RESET}")
    print(f"  Targets  : {GREEN}{stats.targets_hit}{RESET} / {stats.targets_total}")
    print(f"  Total    : {YELLOW}{stats.elapsed:.1f}s{RESET}")
    if stats.avg_time:
        print(f"  Avg/tgt  : {YELLOW}{stats.avg_time:.2f}s{RESET}")
    if stats.times:
        best = min(stats.times)
        worst = max(stats.times)
        print(f"  Best     : {GREEN}{best:.2f}s{RESET}")
        print(f"  Worst    : {RED}{worst:.2f}s{RESET}")
    print()


def wait_for_socket(socket_path: str, timeout: int = 30) -> bool:
    print(f"\n  {DIM}Waiting for Neovim socket at {socket_path} ...{RESET}")
    deadline = time.time() + timeout
    while time.time() < deadline:
        if os.path.exists(socket_path):
            return True
        time.sleep(0.2)
    return False


def run(socket_path: str):
    from exercises import EXERCISES
    from trainer import VimTrainer, RestartExercise, QuitToMenu

    if not wait_for_socket(socket_path):
        print(f"\n  {RED}✗  Neovim socket not found at {socket_path}{RESET}")
        print(f"  Run the launcher:\n")
        print(f"    {CYAN}./run.sh{RESET}\n")
        sys.exit(1)

    trainer = VimTrainer(socket_path)
    print(f"  {GREEN}✓  Connected to Neovim{RESET}")
    time.sleep(0.3)

    try:
        while True:
            # ── Render menu ─────────────────────────────────────────────────────
            h = shutil.get_terminal_size().lines
            clr()
            header()                         # lines 1‑3
            sys.stdout.write(f"\033[5;{h}r") # scroll region: lines 5+
            sys.stdout.write("\033[5;1H")    # cursor → line 5
            show_exercises_categorized(EXERCISES)
            sys.stdout.write(f"\033[1;{h}r") # reset scroll region
            sys.stdout.write("\033[4;1H")    # cursor → line 4 (prompt)
            _menu_prompt()
            sys.stdout.flush()

            # ── Read choice ─────────────────────────────────────────────────
            try:
                raw = sys.stdin.readline().strip()
            except (EOFError, KeyboardInterrupt):
                break

            if raw.lower() == "q":
                break

            try:
                idx = int(raw) - 1
                if not (0 <= idx < len(EXERCISES)):
                    continue
            except ValueError:
                continue

            exercise = EXERCISES[idx]

            # ── Exercise splash ─────────────────────────────────────────────
            clr()
            header()
            print(f"  {'─' * 42}")
            print(f"\n  {BOLD}▶  {exercise['name']}{RESET}")
            print(f"  {DIM}{exercise['description']}{RESET}\n")
            print(f"  {YELLOW}A new tab opened with the exercise — start moving!{RESET}")
            print(f"  {DIM}(The target is highlighted in yellow){RESET}\n")
            print(f"  {'─' * 42}")

            while True:
                try:
                    stats = trainer.run_exercise(exercise)
                    break
                except RestartExercise:
                    continue
                except QuitToMenu:
                    stats = None
                    break

            if stats is None:
                continue

            # ── Stats ───────────────────────────────────────────────────────
            clr()
            header()
            show_stats(stats, exercise["name"])
            print(f"  {'─' * 42}")

            try:
                again = input(
                    f"\n  {BOLD}Press Enter for another lesson, or q to quit:{RESET} "
                ).strip()
            except (EOFError, KeyboardInterrupt):
                break

            if again.lower() == "q":
                break

    finally:
        trainer.cleanup()
        clr()
        print(f"\n  {CYAN}Thanks for training! Keep practising.{RESET}\n")
