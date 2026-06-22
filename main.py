#!/usr/bin/env python3
"""
vim-trainer — entry point.

Usage:
    python3 main.py [--socket /tmp/nvim.sock]

Make sure Neovim is running first:
    NVIM_LISTEN_ADDRESS=/tmp/nvim.sock nvim
"""

import argparse
import sys
import os

# Allow running from any directory
sys.path.insert(0, os.path.dirname(__file__))


def main():
    parser = argparse.ArgumentParser(description="Vim Trainer")
    parser.add_argument(
        "--socket",
        default=os.environ.get("NVIM_LISTEN_ADDRESS", "/tmp/nvim.sock"),
        help="Path to Neovim's socket (default: /tmp/nvim.sock)",
    )
    args = parser.parse_args()

    from ui import run
    run(args.socket)


if __name__ == "__main__":
    main()
