# 🛠️ Troubleshooting

## Install problems

### ❌ `pip install mediapipe` fails / "No matching distribution"
You're on Python **3.13+** (or 3.9-). MediaPipe only ships wheels for **3.10–3.12**.

```bat
winget install Python.Python.3.12
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### ❌ PyAudio fails to build
Old pip tries to compile it. PyAudio ≥ 0.2.14 ships Windows wheels:

```bat
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\pip install PyAudio
```

### ❌ numpy 2.x conflicts
MediaPipe wants numpy 1.x — that's why `requirements.txt` pins `numpy<2`. If you broke it: `pip install "numpy<2" --force-reinstall`.

### ✅ Verify the whole install
```bat
.venv\Scripts\python aura.py --self-test
```

## Camera problems

| Symptom | Fix |
|---|---|
| "no camera found" | Another app is using it (Teams/OBS/browser tab). Close it. |
| Black image | Wrong device → `python aura.py --camera 1` (or 2…) |
| Windows blocks it | Settings → Privacy → Camera → allow desktop apps |
| Low FPS | Lower `FRAME_WIDTH/HEIGHT` in CONFIG, close heavy apps |
| Hand not detected | More light on your hand, plain background helps |

## Voice problems

| Symptom | Fix |
|---|---|
| Never hears anything | Check default mic: Settings → System → Sound → Input |
| "speech service error" | Google STT needs **internet** |
| Random words trigger stuff | `Ctrl+Alt+V` to mute AURA while talking to humans 😄 |
| Hears music/TTS as commands | Use `--quiet` to disable AURA's spoken feedback |
| Wrong language | `python aura.py --lang es-ES` (or `ca-ES`, `fr-FR`…) |
| Slow to react | Normal: it waits for you to stop speaking (max `PHRASE_TIME_LIMIT` = 6s) |

## Gesture problems

| Symptom | Fix |
|---|---|
| Cursor jittery | Lower `SMOOTHING` (e.g. `0.2`) |
| Cursor laggy | Raise `SMOOTHING` (e.g. `0.5`) |
| Can't reach screen edges | Lower `CONTROL_MARGIN` (e.g. `0.12`) |
| Ghost clicks | Raise `PINCH_THRESHOLD` (e.g. `0.38`) |
| Clicks don't register | Lower `PINCH_THRESHOLD` (e.g. `0.26`) |
| Accidental Alt+F4 | Raise `FIST_HOLD_TIME` (e.g. `2.0`) |
| Desktop swipe won't trigger | Lower `SWIPE_SPEED`, flick faster |

## School / locked-down PCs 🏫

- AURA needs **zero admin rights** — everything installs per-user.
- If `winget` is blocked, grab the Python 3.12 installer from python.org and tick *"Install for me only"*.
- If the `keyboard` global hotkeys are blocked by policy, AURA still runs — you just lose Ctrl+Alt+G/V/Q (quit with `q` on the camera window).

Still stuck? [Open an issue](../../../issues) with the full error message. 🙏
