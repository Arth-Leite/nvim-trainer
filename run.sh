#!/bin/bash
set -e

SOCKET="/tmp/nvim-trainer.sock"
DIR="$(cd "$(dirname "$0")" && pwd)"

rm -f "$SOCKET"

nvim --clean --listen "$SOCKET" \
  -c "set number laststatus=2 background=dark nocursorcolumn" \
  -c "set cursorline cursorlineopt=number" \
  -c "filetype on | syntax on" \
  -c "colorscheme habamax" \
  -c "cd $DIR" \
  -c "autocmd TermClose * ++nested qall!" \
  -c "terminal uv run python3 main.py --socket $SOCKET"
