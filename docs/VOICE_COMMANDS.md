# 🎙️ Voice Command Reference

No wake word. AURA listens continuously (toggle with `Ctrl+Alt+V`). Default language is English — **switch live** by just saying the language name: *"spanish"*, *"español"*, *"english"*, *"catalan"*, *"french"*, *"german"*, *"italian"*, *"portuguese"*, *"arabic"* (or press `L` on the camera window).

🧠 **v2 smart matching:** you don't need the exact phrase — *"closed the window please"* still hits `close window` (fuzzy matching, tune `FUZZY_MATCH` in CONFIG).

⌨️ Say **"keyboard"** / **"teclado"** to open the air keyboard, **"hide keyboard"** to close it.
🎚️ Say **"easy mode"**, **"normal mode"** or **"pro mode"** to change the gesture preset.

## Modes

| Say | Mode | What happens |
|---|---|---|
| *(default)* | **COMMAND** | Everything you say is a command |
| `dictation mode` / `word mode` | **DICTATION** | AURA types what you say, word by word |
| `letter mode` / `letter by letter` | **LETTER** | AURA types letters glued together |
| `command mode` / `stop dictation` | **COMMAND** | Back to commands |

The current mode is always visible on the camera HUD.

## COMMAND mode

### Apps
- `open chrome` · `open notepad` · `open calculator` · `open spotify` · `open discord` · `open steam` · `open word` · `open excel` · `open code` · `open terminal` · `open settings` · `open task manager` … (full alias list in `CONFIG["APPS"]` — add your own!)
- Unknown apps fall through to Windows: `open obs` runs `start obs`.
- `search for <anything>` → Google it in your browser
- `type <anything>` → one-shot typing without leaving command mode

### Windows & desktops
| Command | Action |
|---|---|
| `close window` | Alt+F4 |
| `minimize` / `maximize` | Win+↓ / Win+↑ |
| `snap left` / `snap right` | Win+← / Win+→ |
| `switch app` | Alt+Tab |
| `show desktop` | Win+D |
| `next desktop` / `previous desktop` | Ctrl+Win+→ / ← |
| `new desktop` / `close desktop` | Ctrl+Win+D / F4 |
| `task view` | Win+Tab |
| `task manager` | Ctrl+Shift+Esc |
| `lock pc` | locks the session |

### System & media
`volume up` · `volume down` · `mute` · `play` / `pause` · `next song` · `previous song` · `screenshot` (saved to Pictures)

### Editing & browser
`copy` · `paste` · `cut` · `undo` · `redo` · `select all` · `save` · `new tab` · `close tab` · `refresh` · `full screen` · `go back` · `go forward` · `scroll up` · `scroll down` · `click` · `right click` · `double click` · `enter` · `escape`

### 🎹 The hotkey parser — press ANYTHING
Say **`press`** followed by any key names:

```
press control c              press windows e
press alt f4                 press control shift escape
press windows shift s        press control alt delete
press f11                    press tab
```

Recognized keys: `control/ctrl` `shift` `alt` `windows/win` `enter` `tab` `escape` `space` `delete` `backspace` `up/down/left/right` `home` `end` `f1`–`f12` and every letter/number.

## DICTATION mode (word by word)

Speak naturally; punctuation is spoken:

> *"hey bro comma the project is done dot did you see it question mark"*
> → `hey bro, the project is done. did you see it?`

| Spoken | Typed | Spoken | Typed |
|---|---|---|---|
| `comma` / `coma` | `,` | `at sign` / `arroba` | `@` |
| `dot` / `period` / `punto` | `.` | `hashtag` | `#` |
| `question mark` | `?` | `underscore` | `_` |
| `open interrogation` | `¿` | `dash` | `-` |
| `exclamation` | `!` | `quote` | `"` |
| `colon` | `:` | `slash` | `/` |
| `semicolon` | `;` | `asterisk` | `*` |

Controls: `new line` (Enter) · `delete that` (deletes last word) · `delete letter` (backspace) · `press enter` · `press tab`

## LETTER mode (letters glued — *juntos*)

Every letter you say is typed **with no spaces**:

> *"a u r a dot p y"* → `aura.py`
> *"alpha uniform romeo alpha"* → `aura` (NATO works too)
> *"r y a n underscore one five"* → `ryan_15`

- `space` inserts a real space
- All punctuation words work inline
- Plain letters, NATO alphabet (`alpha bravo charlie…`), Spanish letter names (`ele, eme, eñe…`) and digits (`one two three` / `uno dos tres`) are all recognized
