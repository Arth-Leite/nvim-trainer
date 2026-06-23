"""
Exercise catalogue for vim-trainer.

Each exercise defines:
  - id          : unique slug
  - name        : display name
  - description : what the user should do
  - allowed_keys: hint shown in the UI (not enforced — real Vim is used)
  - text        : the buffer content loaded into Neovim
  - targets     : ordered list of (0-based line, 0-based col) the user must visit
  - start_pos   : where the cursor begins (line, col)  [0-based]
  - answer      : keystroke sequence to solve the exercise

Lines in `text` are 0-indexed in targets (matching Neovim's 0-based col /
1-based line — we store everything 0-based internally and convert when
talking to the Neovim API).
"""

EXERCISES = [

    # ── Basic hjkl ────────────────────────────────────────────────────────────
    {
        "id": "hjkl-basic",
        "name": "Basic hjkl Movement",
        "description": "Navigate to each highlighted target using ONLY h j k l.",
        "allowed_keys": ["h", "j", "k", "l"],
        "text": """\
function greet(name) {
  const message = "Hello, " + name;
  console.log(message);
  return message;
}

greet("World");
""",
        "start_pos": (0, 0),
        "targets": [
            (0, 15),  # 'n' in greet(name)
            (1, 18),  # '"' opening quote
            (2, 10),  # 'l' in log
            (6, 6),   # '"' in greet("World")
        ],
        "answer": "15lj3lj8h4j4h",
    },
    {
        "id": "hjkl-maze",
        "name": "hjkl Maze",
        "description": "Navigate a winding path through code using h j k l.",
        "allowed_keys": ["h", "j", "k", "l"],
        "text": """\
function maze() {
  let alpha = 1;
  let beta  = 2;
  let gamma = 3;
  let delta = 4;
  let epsilon = 5;
  return alpha + beta + gamma + delta + epsilon;
}
""",
        "start_pos": (0, 0),
        "targets": [
            (0, 9),   # 'm' in maze
            (1, 6),   # 'a' in alpha
            (2, 6),   # 'b' in beta
            (3, 6),   # 'g' in gamma
            (4, 6),   # 'd' in delta
            (5, 6),   # 'e' in epsilon
            (6, 2),   # 'r' in return
        ],
        "answer": "9lj3hjjjjj4h",
    },

    # ── Word motions ──────────────────────────────────────────────────────────
    {
        "id": "word-motions",
        "name": "Word Motions  w / e / b",
        "description": "Jump to each target using w, e, or b. No hjkl!",
        "allowed_keys": ["w", "e", "b", "W", "E", "B", "j"],
        "text": """\
const result = fetchData(apiUrl, options);
const filtered = result.filter(item => item.active);
const names = filtered.map(item => item.name);
""",
        "start_pos": (0, 0),
        "targets": [
            (0, 6),   # 'r' result
            (0, 15),  # 'f' fetchData
            (0, 25),  # 'a' apiUrl
            (1, 6),   # 'f' filtered
            (2, 23),  # 'm' map
        ],
        "answer": "wwwj0wj4w",
    },
    {
        "id": "word-motions-extended",
        "name": "Word Motions Extended",
        "description": "Navigate longer code using w, e, b and their capital variants.",
        "allowed_keys": ["w", "e", "b", "W", "E", "B", "j", "l"],
        "text": """\
const apiResponse = await fetchDataFromServer(userId, options);
const { data, status } = await response.json();
const isValid = data.length > 0 && data.every(item => item.active);
const filteredResults = data.filter(item => item.value >= threshold);
""",
        "start_pos": (0, 0),
        "targets": [
            (0, 6),    # 'a' apiResponse
            (0, 39),   # 'S' Server
            (1, 8),    # 'd' data
            (1, 40),   # 'j' json
            (2, 6),    # 'i' isValid
            (2, 40),   # 'e' every
            (3, 29),   # 'f' filter
            (3, 58),   # 't' threshold
        ],
        "answer": "wWWW14lj0ww8wj0w11wj05w29l",
    },

    # ── Line-end motions ──────────────────────────────────────────────────────
    {
        "id": "line-ends",
        "name": "Line End Motions  0 / $ / _",
        "description": "Reach the targets at the start/end of lines using 0, $, or _.",
        "allowed_keys": ["0", "$", "_", "j", "k"],
        "text": """\
  const x = computeValue(input);
    let y = x * 2 + offset;
const z = Math.sqrt(x * x + y * y);
""",
        "start_pos": (0, 6),
        "targets": [
            (0, 30),  # ')' end of line 0
            (0, 2),   # 'c' first non-blank line 0
            (1, 26),  # ';' end of line 1
            (1, 4),   # 'l' first non-blank line 1
            (2, 0),   # 'c' hard start line 2
        ],
        "answer": "$_j$_j0",
    },
    {
        "id": "line-ends-mastery",
        "name": "Line End Mastery",
        "description": "Master 0, $, and _ on deeply indented code.",
        "allowed_keys": ["0", "$", "_", "j", "k"],
        "text": """\
function process(items) {
    const total = items.reduce((sum, item) => {
        return sum + item.value;
    }, 0);
    return Math.round(total * 100) / 100;
}

process([1, 2, 3]);
""",
        "start_pos": (0, 9),
        "targets": [
            (0, 22),  # ')' end of line 0
            (1, 4),   # 'c' first non-blank line 1
            (2, 8),   # 'r' first non-blank line 2
            (3, 9),   # ';' end of line 3
            (4, 40),  # ';' end of line 4
            (5, 0),   # '}' hard start line 5
            (7, 0),   # 'p' hard start line 7
            (7, 18),  # ';' end of line 7
        ],
        "answer": "$j_j_j$j$j0jj$",
    },

    # ── f / F find ────────────────────────────────────────────────────────────
    {
        "id": "find-char",
        "name": "Find Character  f / F / ;",
        "description": "Use f{char} and F{char} to jump directly to the targets.",
        "allowed_keys": ["f", "F", ";", ",", "j"],
        "text": """\
import { useState, useEffect, useCallback } from 'react';
const [count, setCount] = useState(0);
useEffect(() => { setCount(c => c + 1); }, [count]);
""",
        "start_pos": (0, 0),
        "targets": [
            (0, 9),   # 'u' useState
            (0, 19),  # 'u' useEffect
            (0, 30),  # 'u' useCallback
            (1, 7),   # 'c' count
            (2, 18),  # 's' setCount
        ],
        "answer": "fu;;j0fcjfs",
    },
    {
        "id": "find-char-advanced",
        "name": "Find Character Advanced",
        "description": "Use f/F and ;/, to jump through many targets with different chars.",
        "allowed_keys": ["f", "F", ";", ",", "j", "l", "h"],
        "text": """\
import { useState, useEffect, useContext, useReducer } from 'react';
import axios from 'axios';
const App = () => {
    const [user, setUser] = useState(null);
    const [posts, setPosts] = useState([]);
    useEffect(() => { fetchData(); }, []);
    return <div>Hello World</div>;
};
""",
        "start_pos": (0, 0),
        "targets": [
            (0, 9),   # 'u' useState
            (0, 19),  # 'u' useEffect
            (0, 30),  # 'u' useContext
            (0, 42),  # 'u' useReducer
            (1, 7),   # 'a' axios
            (3, 17),  # 's' setUser
            (5, 22),  # 'f' fetchData
            (6, 12),  # 'd' div
        ],
        "answer": "fu;;;j0fa2jf,lfs2jffj10h",
    },

    # ── Search ────────────────────────────────────────────────────────────────
    {
        "id": "search",
        "name": "Search  / and n / N",
        "description": "Use /pattern to find targets and n / N to repeat.",
        "allowed_keys": ["/", "?", "n", "N", "*", "#"],
        "text": """\
function processOrder(order) {
  validateOrder(order);
  const total = calculateTotal(order.items);
  applyDiscount(order, total);
  saveOrder(order);
  return order;
}
""",
        "start_pos": (0, 0),
        "targets": [
            (1, 2),   # 'v' validateOrder
            (2, 16),  # 'c' calculateTotal
            (3, 2),   # 'a' applyDiscount
            (4, 2),   # 's' saveOrder
        ],
        "answer": "/validate<CR>/calculateTotal<CR>/apply<CR>/save<CR>",
    },
    {
        "id": "search-advanced",
        "name": "Search Deep",
        "description": "Use /pattern and n/N to navigate a longer file with repeated patterns.",
        "allowed_keys": ["/", "?", "n", "N", "*", "#"],
        "text": """\
class UserManager {
  constructor() { this.users = []; }
  addUser(user) { this.users.push(user); return user; }
  findUser(id) { return this.users.find(u => u.id === id); }
  removeUser(id) {
    const idx = this.users.findIndex(u => u.id === id);
    if (idx > -1) return this.users.splice(idx, 1)[0];
  }
  listUsers() { return [...this.users]; }
  countUsers() { return this.users.length; }
}

const manager = new UserManager();
manager.addUser({ id: 1, name: "Alice" });
manager.addUser({ id: 2, name: "Bob" });
manager.addUser({ id: 3, name: "Charlie" });
""",
        "start_pos": (0, 0),
        "targets": [
            (1, 2),   # 'c' constructor
            (2, 2),   # 'a' addUser
            (3, 2),   # 'f' findUser
            (4, 2),   # 'r' removeUser
            (9, 2),   # 'c' countUsers
            (13, 32), # 'A' Alice
            (14, 32), # 'B' Bob
            (15, 32), # 'C' Charlie
        ],
        "answer": "/constructor<CR>/addUser<CR>/findUser<CR>/removeUser<CR>/countUsers<CR>/Alice<CR>/Bob<CR>/Charlie<CR>",
    },

    # ── Delete operator ───────────────────────────────────────────────────────
    {
        "id": "delete-ops",
        "name": "Delete Operators  dw / dd / D / x",
        "description": "Navigate to the highlighted word and DELETE it. Use dw, dd, D, or x.",
        "allowed_keys": ["d", "w", "d", "d", "D", "x", "h", "j", "k", "l", "/"],
        "check_mode": "content",
        "text": """\
function start() {
  let ddeleteWord = "useless";
  const keepMe = "important";
  let extrasWord = "redundant";
  const deleteLines = "remove this line";
}
""",
        "start_pos": (0, 0),
        "targets": [
            (1, 6, 17),  # ddeleteWord
            (3, 6, 16),  # extrasWord
            (4, 8, 19),  # deleteLines
        ],
        "checks": [
            {"type": "delete", "text": "ddeleteWord"},
            {"type": "delete", "text": "extrasWord"},
            {"type": "delete", "text": "deleteLines"},
        ],
        "answer": "/ddeleteWord<CR>dw/extrasWord<CR>dw/deleteLines<CR>dw",
    },
    {
        "id": "delete-challenge",
        "name": "Delete Challenge",
        "description": "Navigate to each target and delete it with dw, diw, dd, D, or x.",
        "allowed_keys": ["d", "w", "i", "d", "D", "x", "h", "j", "k", "l", "/"],
        "check_mode": "content",
        "text": """\
function cleanup() {
  let tempVal = "garbage";
  const useful = "keep_me";
  let obsoleteVar = "trash";
  const important = "save_this";
  let uselessStuff = "junk";
}
""",
        "start_pos": (0, 0),
        "targets": [
            (1, 6, 13),  # tempVal
            (3, 6, 17),  # obsoleteVar
            (5, 6, 18),  # uselessStuff
        ],
        "checks": [
            {"type": "delete", "text": "tempVal"},
            {"type": "delete", "text": "obsoleteVar"},
            {"type": "delete", "text": "uselessStuff"},
        ],
        "answer": "/tempVal<CR>dw/obsoleteVar<CR>dw/uselessStuff<CR>dw",
    },

    # ── Change inside ─────────────────────────────────────────────────────────
    {
        "id": "change-inside",
        "name": "Change Inside  ci\" ci' ci( ci[ ci{",
        "description": "Use ci\", ci', ci(, ci[, or ci{ to replace each word with the one shown in the comment.",
        "allowed_keys": ["ci\"", "ci'", "ci(", "ci[", "ci{", "w", "b", "e", "/"],
        "text": """\
const s1 = "APPLE";    // → BANANA
const s2 = 'CHERRY';   // → DATE
const fn = (MANGO);    // → LEMON
const arr = [PEACH];   // → PLUM
const obj = {GRAPE};   // → BERRY
""",
        "start_pos": (0, 0),
        "check_mode": "content",
        "targets": [
            (0, 12, 17),  # APPLE — ci" + BANANA
            (1, 12, 18),  # CHERRY — ci' + DATE
            (2, 12, 17),  # MANGO — ci( + LEMON
            (3, 13, 18),  # PEACH — ci[ + PLUM
            (4, 13, 18),  # GRAPE — ci{ + BERRY
        ],
        "checks": [
            {"type": "state", "expected": "const s1 = \"BANANA\";    // → BANANA\nconst s2 = 'CHERRY';   // → DATE\nconst fn = (MANGO);    // → LEMON\nconst arr = [PEACH];   // → PLUM\nconst obj = {GRAPE};   // → BERRY"},
            {"type": "state", "expected": "const s1 = \"BANANA\";    // → BANANA\nconst s2 = 'DATE';   // → DATE\nconst fn = (MANGO);    // → LEMON\nconst arr = [PEACH];   // → PLUM\nconst obj = {GRAPE};   // → BERRY"},
            {"type": "state", "expected": "const s1 = \"BANANA\";    // → BANANA\nconst s2 = 'DATE';   // → DATE\nconst fn = (LEMON);    // → LEMON\nconst arr = [PEACH];   // → PLUM\nconst obj = {GRAPE};   // → BERRY"},
            {"type": "state", "expected": "const s1 = \"BANANA\";    // → BANANA\nconst s2 = 'DATE';   // → DATE\nconst fn = (LEMON);    // → LEMON\nconst arr = [PLUM];   // → PLUM\nconst obj = {GRAPE};   // → BERRY"},
            {"type": "state", "expected": "const s1 = \"BANANA\";    // → BANANA\nconst s2 = 'DATE';   // → DATE\nconst fn = (LEMON);    // → LEMON\nconst arr = [PLUM];   // → PLUM\nconst obj = {BERRY};   // → BERRY"},
        ],
        "answer": "/APPLE<CR>ci\"BANANA<Esc>/CHERRY<CR>ci'DATE<Esc>/MANGO<CR>ci(LEMON<Esc>/PEACH<CR>ci[PLUM<Esc>/GRAPE<CR>ci{BERRY<Esc>",
    },
    {
        "id": "change-inside-advanced",
        "name": "Change Inside Advanced  ci` ci[ ci{ ci\"",
        "description": "Use ci`, ci[, ci{, and ci\" to replace each word with the one shown in the comment.",
        "allowed_keys": ["ci`", "ci[", "ci{", "ci\"", "ci'", "w", "b", "f", "F", "/"],
        "text": """\
const url = `REMOVE_A`;       // → PLANET_A
const data = { key: "REMOVE_B" };  // → PLANET_B
const list = ["REMOVE_C"];    // → PLANET_C
""",
        "start_pos": (0, 0),
        "check_mode": "content",
        "targets": [
            (0, 13, 21),  # REMOVE_A — ci` + PLANET_A
            (1, 21, 29),  # REMOVE_B — ci{ + PLANET_B
            (2, 15, 23),  # REMOVE_C — ci[ + PLANET_C
        ],
        "checks": [
            {"type": "state", "expected": "const url = `PLANET_A`;       // → PLANET_A\nconst data = { key: \"REMOVE_B\" };  // → PLANET_B\nconst list = [\"REMOVE_C\"];    // → PLANET_C"},
            {"type": "state", "expected": "const url = `PLANET_A`;       // → PLANET_A\nconst data = {PLANET_B};  // → PLANET_B\nconst list = [\"REMOVE_C\"];    // → PLANET_C"},
            {"type": "state", "expected": "const url = `PLANET_A`;       // → PLANET_A\nconst data = {PLANET_B};  // → PLANET_B\nconst list = [PLANET_C];    // → PLANET_C"},
        ],
        "answer": "/REMOVE_A<CR>ci`PLANET_A<Esc>/REMOVE_B<CR>ci{PLANET_B<Esc>/REMOVE_C<CR>ci[PLANET_C<Esc>",
    },

    # ── Phase 2: Matching pairs ────────────────────────────────────────────────
    {
        "id": "matching-pairs",
        "name": "Matching Pairs  %",
        "description": "Use % to jump between matching brackets.",
        "allowed_keys": ["%", "f", "0", "j"],
        "text": """\
let x = (a + b);
let y = [1, 2, 3];
let z = { key: val };
""",
        "start_pos": (0, 0),
        "targets": [
            (0, 14),   # ) matching (
            (1, 16),   # ] matching [
            (2, 19),   # } matching {
        ],
        "answer": "f(%j0f[%j0f{%",
    },
    {
        "id": "scroll-basics",
        "name": "Numbered Jumps  [count]j / [count]k",
        "description": "Jump multiple lines at once using count-prefixed j and k.",
        "allowed_keys": ["j", "k", "1", "2", "3", "4", "5", "6", "7", "8", "9"],
        "text": """\
line 00
line 01
line 02
line 03
line 04
line 05
line 06
line 07
line 08
line 09
line 10
line 11
line 12
line 13
line 14
line 15
line 16
line 17
line 18
line 19
line 20
line 21
line 22
line 23
line 24
""",
        "start_pos": (0, 0),
        "targets": [
            (2, 0),    # 2j
            (4, 0),    # 2j 2j
            (6, 0),    # 2j 2j 2j
        ],
        "answer": "2j2j2j",
    },
    {
        "id": "scroll-screen",
        "name": "Screen Navigation  H / M / L",
        "description": "Jump to the top, middle, and bottom of the screen.",
        "allowed_keys": ["H", "M", "L"],
        "setup_commands": ["resize 10"],
        "text": """\
line 00
line 01
line 02
line 03
line 04
line 05
line 06
line 07
line 08
line 09
line 10
line 11
line 12
line 13
line 14
line 15
line 16
line 17
line 18
line 19
line 20
line 21
line 22
line 23
line 24
""",
        "start_pos": (0, 0),
        "targets": [
            (9, 0),   # L
            (0, 0),   # H
            (4, 0),   # M
        ],
        "answer": "LHM",
    },
    {
        "id": "jump-list",
        "name": "Jump List  Ctrl-O",
        "description": "Use Ctrl-O to jump back through the jump list to previous locations.",
        "allowed_keys": ["<C-o>", "G", "/"],
        "text": """\
start here
a
b
c
d
middle area
f
g
h
i
end here
""",
        "start_pos": (0, 0),
        "targets": [
            (10, 0),  # G
            (5, 0),   # /middle<CR>
            (10, 0),  # <C-o> back
            (0, 0),   # <C-o> back again
        ],
        "answer": "G/middle<CR><C-o><C-o>",
    },

    # ── Phase 3: Text objects ──────────────────────────────────────────────────
    {
        "id": "pair-objects",
        "name": "Pair Text Objects  di( / da( / ci(",
        "description": "Delete and change inside and around brackets.",
        "allowed_keys": ["d", "i", "(", "a", "c", "<Esc>", "f", "j", "l"],
        "check_mode": "content",
        "text": """\
foo(bar) baz
func(a, b, c) rest
data[key] value
""",
        "start_pos": (0, 0),
        "targets": [
            (0, 3, 8),
            (1, 4, 14),
            (2, 4, 11),
        ],
        "checks": [
            {"type": "state", "expected": "foo() baz\nfunc rest\ndata[KEY] value"},
        ],
        "answer": "f(di(jda(jlci[KEY<Esc>",
    },
    {
        "id": "replace-char",
        "name": "Replace Character  r / x",
        "description": "Use r to replace a character and x to delete a character.",
        "allowed_keys": ["r", "x", "f", "w"],
        "check_mode": "content",
        "text": """\
fix thes worrd.
""",
        "start_pos": (0, 0),
        "checks": [
            {"type": "state", "expected": "fix this word."},
        ],
        "answer": "feriwfrx",
    },
    {
        "id": "case-change",
        "name": "Case Changes  gu / gU",
        "description": "Lowercase with gu and uppercase with gU.",
        "allowed_keys": ["g", "U", "u", "w", "0", "j"],
        "check_mode": "content",
        "text": """\
make THIS lowercase
MAKE this UPPERCASE
""",
        "start_pos": (0, 0),
        "checks": [
            {"type": "state", "expected": "make this lowercase\nMAKE THIS UPPERCASE"},
        ],
        "answer": "wguwj0wgUw",
    },
    {
        "id": "visual-basic",
        "name": "Visual Mode  v / V",
        "description": "Use visual mode to select text, then delete or uppercase.",
        "allowed_keys": ["v", "V", "d", "U", "e", "j"],
        "check_mode": "content",
        "text": """\
delete me
keep me
""",
        "start_pos": (0, 0),
        "checks": [
            {"type": "state", "expected": " me\nKEEP ME"},
        ],
        "answer": "vedjVU",
    },
    {
        "id": "visual-block",
        "name": "Visual Block  Ctrl-V",
        "description": "Use Ctrl-V for block-wise visual selection.",
        "allowed_keys": ["<C-v>", "d", "j"],
        "check_mode": "content",
        "text": """\
abc
123
xyz
""",
        "start_pos": (0, 0),
        "checks": [
            {"type": "state", "expected": "bc\n23\nyz"},
        ],
        "answer": "<C-v>jjd",
    },
    {
        "id": "substitute",
        "name": "Substitute  :s",
        "description": "Use :s to substitute text patterns.",
        "allowed_keys": [":", "s", "/", "g", "%", "j"],
        "check_mode": "content",
        "text": """\
cat dog cat
dog cat dog
cat cat dog
""",
        "start_pos": (0, 0),
        "targets": [
            (0, 0, 0),
            (0, 0, 0),
            (0, 0, 0),
        ],
        "checks": [
            {"type": "state", "expected": "dog dog cat\ndog cat dog\ncat cat dog"},
            {"type": "state", "expected": "dog dog dog\ndog cat dog\ncat cat dog"},
            {"type": "state", "expected": "dog dog dog\ndog dog dog\ndog dog dog"},
        ],
        "answer": ":s/cat/dog<CR>j:s/cat/dog<CR>:%s/cat/dog/g<CR>",
    },
    {
        "id": "yank-put",
        "name": "Yank & Put  yy / yw / p",
        "description": "Yank (copy) and put (paste) entire lines.",
        "allowed_keys": ["y", "y", "p", "j"],
        "check_mode": "content",
        "text": """\
line one
line two
line three
""",
        "start_pos": (0, 0),
        "checks": [
            {"type": "state", "expected": "line one\nline one\nline two\nline three"},
        ],
        "answer": "yyp",
    },
    {
        "id": "registers",
        "name": "Named Registers  \"a y / \"a p",
        "description": "Yank to and paste from named registers.",
        "allowed_keys": ["\"", "a", "y", "p"],
        "check_mode": "content",
        "text": """\
first
second
third
""",
        "start_pos": (0, 0),
        "checks": [
            {"type": "state", "expected": "first\nfirst\nsecond\nthird"},
        ],
        "answer": "\"ayy\"ap",
    },

    # ── Phase 4: Multi-step ────────────────────────────────────────────────────
    {
        "id": "cgn-dot",
        "name": "cgn + Dot  cgn / .",
        "description": "Change all occurrences of a pattern using cgn and the dot repeat.",
        "allowed_keys": ["c", "g", "n", ".", "/"],
        "check_mode": "content",
        "text": """\
foo bar foo
foo bar foo
""",
        "start_pos": (0, 0),
        "checks": [
            {"type": "state", "expected": "baz bar baz\nbaz bar baz"},
        ],
        "answer": "/foo<CR>cgnbaz<Esc>n.n.n.",
    },
    {
        "id": "macros",
        "name": "Macros  q / @",
        "description": "Record and replay macros to automate repetitive edits.",
        "allowed_keys": ["q", "@", "a", "$", "j", "g"],
        "check_mode": "content",
        "text": """\
1. item
2. item
3. item
4. item
""",
        "start_pos": (0, 0),
        "checks": [
            {"type": "state", "expected": "1. ITEM\n2. ITEM\n3. ITEM\n4. ITEM"},
        ],
        "answer": "qa0gU$jq3@a",
    },
    {
        "id": "window-nav",
        "name": "Window Navigation  Ctrl-W",
        "description": "Navigate between windows using Ctrl-W h/j/k/l. Split windows with Ctrl-W v/s.",
        "allowed_keys": ["<C-w>", "h", "j", "k", "l", "v", "s", "c", "o"],
        "layout": "windows",
        "setup_commands": ["set scroll=2"],
        "text": """\
top-left
---
top-right
---
bottom
---
""",
        "start_pos": (0, 0),
        "targets": [
            (4, 0),   # <C-w>j → bottom window
            (0, 0),   # <C-w>k → top-left
        ],
        "answer": "<C-w>j<C-w>k",
    },
]

# Quick lookup by id
EXERCISE_MAP = {ex["id"]: ex for ex in EXERCISES}
