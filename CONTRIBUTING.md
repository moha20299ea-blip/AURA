# Contributing to AURA 🖐️

Yo! PRs are very welcome. The whole app is **one file on purpose** — keep it that way.

## Ground rules

1. **One file.** All runtime code lives in `aura.py`. Docs go in `docs/`.
2. **No new heavy dependencies** without an issue discussion first.
3. **Windows first** — Linux/macOS support is on the roadmap, PRs welcome but don't break Windows.
4. Every new gesture/voice command must be added to the docs tables (`docs/GESTURES.md` / `docs/VOICE_COMMANDS.md`).
5. Run the self-test before pushing: `python aura.py --self-test`.

## Easy first contributions 🌱

- Add app aliases to `CONFIG["APPS"]`
- Add your language's punctuation/letter words to `PUNCTUATION` / `LETTERS`
- New voice commands in `VoiceEngine._command`
- New gestures in `GestureEngine._process_hand` (mind the cooldowns!)
- Better HUD

## Workflow

```bash
git clone https://github.com/Anlight-OS/AURA.git
cd AURA && install.bat
# hack hack hack
.venv\Scripts\python aura.py --self-test
```

Open a PR with a clear title and a short demo description (GIFs = instant approval energy ⚡).
