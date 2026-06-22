"""
ui.py — Terminal menu for the Vim Trainer.

Runs in a second terminal pane. Connects to Neovim via its socket,
lets the user pick an exercise, then drives the trainer while Neovim
is used in the adjacent pane.
"""

import os
import sys
import time

# ── ANSI colours ───────────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
WHITE  = "\033[97m"
BG_DARK = "\033[48;5;235m"
CLEAR  = "\033[2J\033[H"


def clr():
    print(CLEAR, end="")


def header():
    print(f"{BOLD}{CYAN}")
    print("  ╔══════════════════════════════════════╗")
    print("  ║        V I M  T R A I N E R          ║")
    print("  ╚══════════════════════════════════════╝")
    print(f"{RESET}")


def rule():
    print(f"{DIM}  {'─' * 42}{RESET}")


def show_exercises(exercises: list):
    print(f"  {BOLD}{WHITE}Choose an exercise:{RESET}\n")
    for i, ex in enumerate(exercises, 1):
        keys = "  ".join(
            f"{YELLOW}{k}{RESET}" for k in ex.get("allowed_keys", [])
        )
        print(f"  {CYAN}{i:>2}.{RESET} {BOLD}{ex['name']}{RESET}")
        print(f"      {DIM}{ex['description']}{RESET}")
        print(f"      keys: {keys}")
        print()


def show_stats(stats, exercise_name: str):
    rule()
    print(f"\n  {BOLD}{GREEN}✓  Exercise complete!{RESET}\n")
    print(f"  Exercise : {BOLD}{exercise_name}{RESET}")
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


def pick_exercise(exercises: list) -> dict:
    while True:
        try:
            raw = input(f"  {BOLD}Enter number (or q to quit):{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)

        if raw.lower() == "q":
            sys.exit(0)

        try:
            idx = int(raw) - 1
            if 0 <= idx < len(exercises):
                return exercises[idx]
        except ValueError:
            pass

        print(f"  {RED}Invalid choice, try again.{RESET}")


def wait_for_socket(socket_path: str, timeout: int = 30) -> bool:
    """Poll until the Neovim socket appears."""
    print(f"\n  {DIM}Waiting for Neovim socket at {socket_path} ...{RESET}")
    deadline = time.time() + timeout
    while time.time() < deadline:
        if os.path.exists(socket_path):
            return True
        time.sleep(0.2)
    return False


def run(socket_path: str):
    from exercises import EXERCISES
    from trainer import VimTrainer

    if not wait_for_socket(socket_path):
        print(f"\n  {RED}✗  Neovim socket not found at {socket_path}{RESET}")
        print(f"  Start Neovim with:\n")
        print(f"    {CYAN}NVIM_LISTEN_ADDRESS={socket_path} nvim{RESET}\n")
        sys.exit(1)

    trainer = VimTrainer(socket_path)
    print(f"  {GREEN}✓  Connected to Neovim{RESET}")
    time.sleep(0.5)

    try:
        while True:
            clr()
            header()
            show_exercises(EXERCISES)
            rule()

            exercise = pick_exercise(EXERCISES)

            clr()
            header()
            rule()
            print(f"\n  {BOLD}▶  {exercise['name']}{RESET}")
            print(f"  {DIM}{exercise['description']}{RESET}\n")
            print(f"  {YELLOW}Focus your Neovim pane and start moving!{RESET}")
            print(f"  {DIM}(The target is highlighted in yellow){RESET}\n")
            rule()

            stats = trainer.run_exercise(exercise)

            clr()
            header()
            show_stats(stats, exercise["name"])
            rule()

            try:
                again = input(
                    f"\n  {BOLD}Press Enter for another exercise, or q to quit:{RESET} "
                ).strip()
            except (EOFError, KeyboardInterrupt):
                break

            if again.lower() == "q":
                break

    finally:
        trainer.cleanup()
        clr()
        print(f"\n  {CYAN}Thanks for training! Keep practising. 🚀{RESET}\n")
