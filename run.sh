#!/bin/bash
set -e

SOCKET="/tmp/nvim-trainer.sock"
DIR="$(cd "$(dirname "$0")" && pwd)"

rm -f "$SOCKET"

nvim --clean --listen "$SOCKET" \
  -c "set number laststatus=2" \
  -c "cd $DIR" \
  -c "autocmd TermClose * ++nested qall!" \
  -c "terminal uv run python3 main.py --socket $SOCKET"
