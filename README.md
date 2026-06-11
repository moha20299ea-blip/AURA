<div align="center">

```
 █████╗ ██╗   ██╗██████╗  █████╗
██╔══██╗██║   ██║██╔══██╗██╔══██╗
███████║██║   ██║██████╔╝███████║
██╔══██║██║   ██║██╔══██╗██╔══██║
██║  ██║╚██████╔╝██║  ██║██║  ██║
╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝
```

# 🖐️ AURA — Air User, Real Actions 🎙️

### Control your **entire PC** with your hands and your voice. Zero keyboard. Zero mouse. Pure air. ✨

[![Python](https://img.shields.io/badge/python-3.10%20--%203.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078D6?logo=windows&logoColor=white)](#)
[![One File](https://img.shields.io/badge/source-ONE%20FILE-ff69b4)](aura.py)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](CONTRIBUTING.md)
[![Made with ❤️](https://img.shields.io/badge/made%20with-%E2%9D%A4%EF%B8%8F%20%2B%20%F0%9F%96%90%EF%B8%8F-red)](#)

**One Python file.** Your webcam becomes the mouse. Your microphone becomes the keyboard.

[Install](#-install-30-seconds) · [Gestures](#%EF%B8%8F-hand-gestures) · [Voice Commands](#%EF%B8%8F-voice-commands) · [Dictation](#-dictation--type-with-your-voice) · [Docs](docs/) · [Troubleshooting](docs/TROUBLESHOOTING.md)

</div>

---

## 🤯 What is this?

AURA turns any Windows PC into a **touchless machine**:

| 🖐️ Hands (webcam) | 🎙️ Voice (microphone) |
|---|---|
| Move the cursor with your index finger | Open any app: *"open chrome"* |
| Pinch to click, hold pinch to drag | Press any hotkey: *"press control shift escape"* |
| Two fingers to scroll | Full dictation, word-by-word **or letter-by-letter** |
| Swipe 3 fingers → switch virtual desktop | Spoken punctuation: *"comma"* → `,` *"dot"* → `.` |
| ✊ Fist → close app · 🤙 Pinky → minimize | Window control, volume, media, screenshots… |
| 👍👎 Thumbs → volume | 🧠 smart fuzzy matching — close enough = it works |
| ⌨️ **AIR KEYBOARD** — type on a floating keyboard with your fingers | 🌍 8 languages, switch LIVE: just say *"spanish"* |

### ✨ New in v2

- ⌨️ **Air Keyboard** — say *"keyboard"* (or press `K`): a keyboard floats on the camera. Hover a key with your index finger, **touch index+middle together** (or pinch) to press it. Shift, numbers, backspace, enter — all there.
- 🎚️ **EASY / NORMAL / PRO modes** — EASY only has cursor+click+scroll (nothing destructive, perfect to start). PRO unlocks fist-close and desktop swipes and reacts faster. Cycle with `M` or say *"pro mode"*.
- 🌍 **Live language switching** — say *"spanish"* / *"habla español"* or press `L` to cycle: English, Spanish, Catalan, French, German, Italian, Portuguese, Arabic.
- 🧠 **Smart command matching** — slightly-off phrases still hit the right command (fuzzy AI-ish matching, tune with `FUZZY_MATCH`).
- 🛡️ **Gesture stabilization** — a gesture must hold for several frames before firing. No more ghost-triggers from a twitchy hand.
- ⚡ **Zero-freeze engine** — the mouse now uses the native Windows API and every slow action runs on a worker thread. The camera never drops a frame while you click and drag.

All of it runs **locally** from a single file: [`aura.py`](aura.py). No accounts, no telemetry, no nonsense.

---

## ⚡ Install (30 seconds)

> **Requires Python 3.10 – 3.12** (mediapipe doesn't support 3.13+ yet) and Windows 10/11.

```bat
git clone https://github.com/moha20299ea-blip/AURA.git
cd AURA
install.bat
```

That's it. `install.bat` creates a virtual environment and installs everything.

**Manual install:**

```bash
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

**Verify everything works (no camera/mic needed):**

```bash
.venv\Scripts\python aura.py --self-test
```

---

## 🚀 Run

```bat
run.bat
```

or:

```bash
.venv\Scripts\python aura.py                # full experience
.venv\Scripts\python aura.py --mode easy    # chill preset (default: normal)
.venv\Scripts\python aura.py --mode pro     # unlock everything
.venv\Scripts\python aura.py --lang es-ES   # háblale en español
.venv\Scripts\python aura.py --no-camera    # voice only
.venv\Scripts\python aura.py --no-voice     # gestures only
.venv\Scripts\python aura.py --no-preview   # hide the camera window
.venv\Scripts\python aura.py --quiet        # AURA stops talking back
```

### ⌨️ Keys on the camera window

| Key | Action |
|---|---|
| `K` | air keyboard on/off |
| `M` | cycle EASY → NORMAL → PRO |
| `L` | cycle language |
| `P` | pause gestures |
| `Q` | quit |

### 🌐 Global hotkeys (work anywhere, anytime)

| Hotkey | Action |
|---|---|
| `Ctrl` `Alt` `G` | toggle gesture control |
| `Ctrl` `Alt` `V` | toggle voice control |
| `Ctrl` `Alt` `Q` | quit AURA |

---

## 🖐️ Hand gestures

Show **one hand** to the camera. The HUD shows what AURA sees in real time.

| Gesture | Action | Mode |
|---|---|---|
| ☝️ Index finger only | **Move cursor** (smoothed, buttery) | easy+ |
| 🤏 Pinch thumb + index | **Left click** — hold the pinch to **drag** | easy+ |
| ✌️ Index + middle | **Scroll** up / down | easy+ |
| 🖐️ Open palm, hold 1s | **Pause / resume** gesture control | easy+ |
| ⌨️ Air keyboard (`K` or say *"keyboard"*) | **Type with your fingers** | easy+ |
| 🤌 Pinch thumb + middle | **Right click** | normal+ |
| 🤙 Pinky only | **Minimize window** | normal+ |
| 👍 Thumbs up / 👎 down | **Volume** up / down | normal+ |
| ✊ Fist, hold 1.4s | **Close window** (Alt+F4) — HUD shows a countdown | pro |
| 🤟 Index + middle + ring, swipe ← → | **Switch virtual desktop** | pro |

Gestures are **stabilized**: a pose must hold for a few frames before it counts, so random hand shapes can't trigger anything by accident.

📖 Full details + tuning tips: [docs/GESTURES.md](docs/GESTURES.md)

---

## 🎙️ Voice commands

Just talk. No wake word needed. Examples:

```
"open chrome"            "open spotify"          "open task manager"
"close window"           "minimize"              "maximize"
"next desktop"           "new desktop"           "show desktop"
"switch app"             "snap left"             "snap right"
"volume up"              "mute"                  "next song"
"screenshot"             "lock pc"               "select all"
"copy"  "paste"  "cut"   "undo"                  "save"
"new tab"                "close tab"             "refresh"
"scroll down"            "click"                 "double click"
"search for hand tracking python"
"type hello world"
```

### 🎹 Press ANY hotkey by voice

Say **"press"** + the keys:

```
"press control c"                → Ctrl+C
"press windows e"                → Win+E (explorer)
"press alt tab"                  → Alt+Tab
"press control shift escape"     → Ctrl+Shift+Esc (task manager)
"press windows shift s"          → snipping tool
"press f5"                       → F5
```

🇪🇸 Spanish works too: *"abre chrome"*, *"cierra la ventana"*, *"sube el volumen"*, *"pulsa control c"*…

### 🌍 Switch language LIVE

Say the language name (or press `L` on the camera window):

```
"spanish" / "español"     "english"      "catalan" / "català"
"french"                  "german"       "italian"
"portuguese"              "arabic"
```

### 🎚️ Switch gesture mode by voice

```
"easy mode"      → only cursor, click, scroll, air keyboard (nothing scary)
"normal mode"    → + right click, minimize, volume
"pro mode"       → + fist-close, desktop swipes, faster reactions
```

📖 Every command: [docs/VOICE_COMMANDS.md](docs/VOICE_COMMANDS.md)

---

## ⌨️ Dictation — type with your voice

Click into any text box and say **"dictation mode"**:

> You say: `hello world comma this is aura dot amazing question mark`
> AURA types: `hello world, this is aura. amazing?`

Need to spell something weird (passwords, usernames, code)? Say **"letter mode"**:

> You say: `a u r a dot p y` → AURA types: `aura.py` *(letters glued together automatically — juntos 🤝)*

| You say | AURA types |
|---|---|
| `comma` / `coma` | `,` |
| `dot` / `period` / `punto` | `.` |
| `question mark` | `?` |
| `open interrogation` | `¿` |
| `exclamation` | `!` |
| `at sign` / `arroba` | `@` |
| `hashtag` | `#` |
| `underscore` | `_` |
| `new line` | ⏎ Enter |
| `space` / `espacio` | ␣ |
| `delete that` | deletes last word |
| `command mode` | back to commands |

NATO alphabet works in letter mode too: *"alpha uniform romeo alpha"* → `aura` 🎖️

---

## 🧠 How it works

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│   webcam    │ ──► │ MediaPipe Hands  │ ──► │  21 hand landmarks  │ ──► gestures → pyautogui
└─────────────┘     │  (Google AI)     │     │  @ ~30 fps          │
                    └──────────────────┘     └─────────────────────┘
┌─────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│ microphone  │ ──► │ SpeechRecognition│ ──► │ command parser /    │ ──► actions → keyboard
└─────────────┘     │  (Google STT)    │     │ dictation engine    │
                    └──────────────────┘     └─────────────────────┘
```

- **Gestures** run on the main thread (OpenCV window + HUD), **voice** runs on a background thread, and **every slow action** (hotkeys, typing, opening apps) runs on a third worker thread — nothing ever blocks the camera.
- The mouse talks **directly to the Windows API** (`SetCursorPos` / `mouse_event`) — instant, zero per-call overhead.
- Cursor movement is **exponentially smoothed** and scale-invariant (pinch detection is relative to your hand size, so it works near or far from the camera). Pinches use **hysteresis** (close at one threshold, open at another) so clicks never flicker.
- Gesture classification is **stabilized over multiple frames** — a pose has to persist before it becomes active.
- Every destructive action (✊ close window) is PRO-mode only and has a **hold timer + cooldown** so nothing fires by accident.
- Tweak everything in the `CONFIG` dict at the top of [`aura.py`](aura.py) — sensitivity, language, your own app aliases, hold times…

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| `pip install` fails on **mediapipe** | You're on Python 3.13+. Install 3.12: `winget install Python.Python.3.12` |
| **PyAudio** fails to build | `pip install PyAudio` ≥ 0.2.14 ships wheels — upgrade pip first |
| Voice doesn't respond | Speech uses Google's free API → needs **internet**. Check your mic in Windows settings |
| Cursor too jumpy / too slow | Tune `SMOOTHING` in `CONFIG` (lower = smoother) |
| Clicks fire too easily | Raise `PINCH_THRESHOLD` slightly |
| Camera is black | Try `python aura.py --camera 1` |

More fixes: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

---

## 🗺️ Roadmap

- [x] ⌨️ Air keyboard — type with your fingers *(v2)*
- [x] 🌍 Live multi-language switching *(v2)*
- [x] 🎚️ Easy / Normal / Pro modes *(v2)*
- [ ] 🌑 Offline speech recognition (Vosk / whisper.cpp)
- [ ] ✌️✌️ Two-hand gestures (zoom, rotate)
- [ ] 🧩 Custom gesture → action mapping from a JSON file
- [ ] 🐧 Linux support (great with [Anlight OS](https://github.com/moha20299ea-blip/anlight-os) 👀)
- [ ] 🎯 Eye-tracking assist mode
- [ ] 🗣️ Wake word ("hey aura")

---

## 🤝 Contributing

PRs welcome! Read [CONTRIBUTING.md](CONTRIBUTING.md), open an [issue](../../issues), or just fork it and go wild.

## 📄 License

[MIT](LICENSE) — do whatever you want, just keep the credit. 😎

---

<div align="center">

**If AURA blew your mind, drop a ⭐ — it's free and it makes my day.**

*Built with 🖐️ + 🎙️ + 🐍 by the Aegis Raid / Anlight OS crew.*

</div>
