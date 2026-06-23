# TODO — Features needing significant architecture changes

## Quickfix / Location lists (`:vimgrep`, `:cnext`, `:cprev`)

**Status:** Needs new infrastructure

**Why it's hard:**
- The trainer's `_load_text()` opens a single temp file per exercise
- Quickfix exercises need multiple files (3-4 minimum) with different content
- Need Neovim commands to populate the quickfix list:
  `:vimgrep /pattern/ path1.js path2.js path3.js`
- Or use `:set errorformat` + `:cgetfile` to build a custom list
- Exercises need to test: `:cnext`, `:cprev`, `:cfirst`, `:clast`, `:copen`, `:cclose`
- The test harness needs to verify which quickfix entry the cursor lands on

**Required changes:**
1. New `_load_texts()` or `_load_project()` in trainer.py that creates multiple temp files
2. Quickfix buffer setup in exercise schema (patterns to search for)
3. New target type or `check_mode` (e.g., `"check_mode": "quickfix"`)
4. Test harness updates to wait for quickfix navigation to settle
5. Extension of the exercise schema:
   ```python
   {
       "setup_commands": [
           "vimgrep /TODO/ file1.js file2.js file3.js",
           "copen"
       ],
       "files": {
           "file1.js": "// TODO: implement foo\nconst x = 1;",
           "file2.js": "// TODO: implement bar\nconst y = 2;",
           "file3.js": "// TODO: implement baz\nconst z = 3;",
       }
   }
   ```

## Scroll commands in headless tests (`Ctrl-D`/`Ctrl-U`/`Ctrl-F`/`Ctrl-B`)

**Status:** Needs investigation

**Why it's hard:**
- `Ctrl-D`/`Ctrl-U`/`Ctrl-F`/`Ctrl-B` use the `scroll` option and window height, which behave differently in headless mode vs interactive terminal
- The test harness feeds raw bytes (`\x04`, `\x15`, etc.) via `nvim.api.input()`, but these don't reliably produce the expected cursor movements in headless mode
- Current workaround: `scroll-basics` exercise uses `[count]j`/`[count]k` instead, which works in both environments

**Required changes:**
1. Investigate why `input()` with control bytes behaves differently in headless mode
2. Or add a headless-compatible wrapper that sends scroll keystrokes differently
3. Or use `nvim.command("normal! 2j")` instead of `input("\x04")` for controlled testing

## Viewport-only commands (`zz`/`zt`/`zb`, `Ctrl-E`/`Ctrl-Y`)

**Status:** Not testable with current cursor-mode

**Why it's hard:**
- `zz`: recenter screen (cursor line unchanged)
- `zt`: scroll to top (cursor line unchanged)
- `zb`: scroll to bottom (cursor line unchanged)
- `Ctrl-E`: scroll down 1 line (cursor unchanged)
- `Ctrl-Y`: scroll up 1 line (cursor unchanged)
- These don't change the cursor position, so cursor-mode exercises can't verify them
- Could use `H`/`M`/`L` after scroll to verify the new viewport position, but that requires knowing exact window height

**Possible approach:**
- Combine with `H`/`M`/`L`: e.g., scroll with `zz` then verify with `H` (cursor goes to first visible line)
- Requires predictable window height (`resize N`) and knowledge of cursor position

## Multi-buffer / tab exercises (`gt`/`gT`, `:bnext`/`:bprev`)

**Status:** Partially supported (window layout exists, tabs needed)

**Why it's hard:**
- The `_setup_tab_layout()` method exists but is untested
- Tab exercises need multiple buffers in multiple tabs
- The current exercise schema has `"layout": "tabs"` but no exercises use it yet
- Need to verify tab navigation works with `input()` in headless mode

## Folds (`zc`/`zo`/`zM`/`zR`/`zj`/`zk`)

**Status:** Partially supported

**Why it's hard:**
- Folds need `foldmethod=indent` and a buffer with sufficient indentation
- In headless mode, `zv` (open enough folds to view cursor) is needed for searches to work
- Cursor-mode exercises with `zj`/`zk` require predictable fold structure
- `checks` can't easily verify fold state (open/closed) — only cursor position or buffer content

## Change list (`g;`/`g,`)

**Status:** Not yet implemented

**Why it's hard:**
- `g;` jumps to the position of the last change, working backward through the change list
- `g,` jumps forward through the change list
- Requires making changes first, then navigating the change list
- The change list accumulates across editing operations, making it harder to predict exact positions
- Answer design needs careful sequencing: make change → navigate → use `g;` to go back → use `g,` to go forward
---
