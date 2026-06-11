# 🖐️ Gesture Reference

AURA tracks **21 landmarks** on one hand at ~30 fps using MediaPipe Hands. Show one hand inside the camera frame — the thin purple rectangle on the HUD is your **control area** (the zone that maps to your full screen).

## The gestures

| Gesture | How | Action | Notes |
|---|---|---|---|
| ☝️ **Cursor** | Only index finger up | Move mouse | Movement is smoothed (`SMOOTHING` in CONFIG) |
| 🤏 **Left click / drag** | Index up, pinch thumb→index tip | Click | Keep pinched to **drag**; release to drop |
| 🤌 **Right click** | Index+middle up, pinch thumb→middle tip | Right click | 0.45s cooldown between clicks |
| ✌️ **Scroll** | Index + middle up, move hand up/down | Scroll | Speed = `SCROLL_SPEED` |
| 🤟 **Desktop swipe** | Index + middle + ring up, swipe left/right fast | Ctrl+Win+←/→ | Must be a quick flick, not a slow drift |
| ✊ **Close window** | Full fist, hold **1.2s** | Alt+F4 | HUD shows live countdown — open your hand to cancel |
| 🤙 **Minimize** | Only pinky up | Win+Down | 1.2s cooldown |
| 👍 **Volume up** | Only thumb up, pointing up | Volume +4 | |
| 👎 **Volume down** | Only thumb up, pointing down | Volume −4 | |
| 🖐️ **Pause/Resume** | All 5 fingers, hold **1s** | Freezes all gestures | Same gesture resumes. Voice keeps working |

## Tuning (CONFIG dict at the top of `aura.py`)

| Key | Default | What it does |
|---|---|---|
| `CONTROL_MARGIN` | `0.18` | Border around the frame. **Smaller** = reach the whole screen with less hand travel |
| `SMOOTHING` | `0.35` | `0.05` = silky but laggy → `0.9` = instant but jittery |
| `PINCH_THRESHOLD` | `0.32` | Raise if clicks misfire, lower if clicks don't register |
| `CLICK_COOLDOWN` | `0.45` | Min seconds between clicks |
| `ACTION_COOLDOWN` | `1.20` | Min seconds between window/desktop actions |
| `FIST_HOLD_TIME` | `1.20` | How long to hold the fist before Alt+F4 |
| `SWIPE_SPEED` | `0.045` | Lower = easier desktop swipes |

## Pro tips 💡

- **Lighting matters.** Face a window or lamp; backlight kills tracking.
- Keep your hand **inside the purple rectangle** for full-screen cursor reach.
- Sit ~50–100 cm from the camera. Pinch detection is relative to hand size, so distance doesn't break clicks.
- If gestures act up, show an open palm 🖐️ for 1s to pause, fix your setup, palm again to resume.
- `Ctrl+Alt+G` instantly kills gesture control from anywhere.
