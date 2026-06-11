#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║       █████╗ ██╗   ██╗██████╗  █████╗                                     ║
║      ██╔══██╗██║   ██║██╔══██╗██╔══██╗                                    ║
║      ███████║██║   ██║██████╔╝███████║                                    ║
║      ██╔══██║██║   ██║██╔══██╗██╔══██║                                    ║
║      ██║  ██║╚██████╔╝██║  ██║██║  ██║                                    ║
║      ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝                                    ║
║                                                                           ║
║      A U R A  —  Air User, Real Actions                                   ║
║      Control your entire PC with your HANDS and your VOICE.               ║
║      Zero keyboard. Zero mouse. Pure air.                                 ║
║                                                                           ║
║      https://github.com/Anlight-OS/AURA                                   ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

ONE FILE. That's it. Run it and your webcam becomes a mouse and your
microphone becomes a keyboard.

    python aura.py                  # full experience (camera + voice)
    python aura.py --no-camera      # voice only
    python aura.py --no-voice       # gestures only
    python aura.py --lang es-ES     # speak Spanish to it
    python aura.py --no-preview     # hide the camera window
    python aura.py --self-test      # verify install, no camera/mic needed

GLOBAL HOTKEYS (always work):
    Ctrl+Alt+G   toggle gesture control
    Ctrl+Alt+V   toggle voice control
    Ctrl+Alt+Q   quit AURA
"""

from __future__ import annotations

import argparse
import math
import os
import queue
import re
import subprocess
import sys
import threading
import time
import webbrowser

# ════════════════════════════════════════════════════════════════════════════
#  CONFIG — tweak everything here
# ════════════════════════════════════════════════════════════════════════════

CONFIG = {
    # ── camera / gestures ──────────────────────────────────────────────────
    "CAMERA_INDEX": 0,          # which webcam (0 = default)
    "FRAME_WIDTH": 960,         # camera capture size
    "FRAME_HEIGHT": 540,
    "CONTROL_MARGIN": 0.18,     # dead border around frame (0-0.4). Smaller = bigger reach
    "SMOOTHING": 0.35,          # cursor smoothing 0.05 (silky/laggy) → 0.9 (raw/jittery)
    "PINCH_THRESHOLD": 0.32,    # pinch sensitivity (relative to hand size)
    "CLICK_COOLDOWN": 0.45,     # seconds between clicks
    "ACTION_COOLDOWN": 1.20,    # seconds between big actions (close/minimize/desktop)
    "FIST_HOLD_TIME": 1.20,     # hold a fist this long to close the window
    "PALM_HOLD_TIME": 1.00,     # hold open palm this long to pause/resume
    "SWIPE_SPEED": 0.045,       # how fast 3 fingers must move to count as a swipe
    "SCROLL_SPEED": 30,         # scroll intensity
    "DETECTION_CONFIDENCE": 0.72,
    "TRACKING_CONFIDENCE": 0.60,

    # ── voice ──────────────────────────────────────────────────────────────
    "LANGUAGE": "en-US",        # "en-US", "es-ES", "ca-ES", ...
    "ENERGY_THRESHOLD": 300,    # mic sensitivity (auto-adjusts on start)
    "PHRASE_TIME_LIMIT": 6,     # max seconds per spoken phrase
    "VOICE_FEEDBACK": True,     # AURA talks back (pyttsx3)
    "BEEP_FEEDBACK": True,      # short beep when a command is understood

    # ── apps you can open by voice: "open <name>" ─────────────────────────
    "APPS": {
        "chrome":       "chrome",
        "google":       "chrome",
        "edge":         "msedge",
        "firefox":      "firefox",
        "notepad":      "notepad",
        "bloc de notas": "notepad",
        "calculator":   "calc",
        "calculadora":  "calc",
        "explorer":     "explorer",
        "files":        "explorer",
        "archivos":     "explorer",
        "paint":        "mspaint",
        "word":         "winword",
        "excel":        "excel",
        "powerpoint":   "powerpnt",
        "spotify":      "spotify",
        "discord":      "discord",
        "steam":        "steam",
        "terminal":     "wt",
        "cmd":          "cmd",
        "powershell":   "powershell",
        "code":         "code",
        "vs code":      "code",
        "settings":     "ms-settings:",
        "task manager": "taskmgr",
        "snipping tool": "snippingtool",
        "camera":       "microsoft.windows.camera:",
    },
}

# ════════════════════════════════════════════════════════════════════════════
#  DEPENDENCY CHECK — friendly errors instead of ugly tracebacks
# ════════════════════════════════════════════════════════════════════════════

def _need(package: str, pip_name: str):
    print(f"\n  [AURA] Missing dependency: {package}")
    print(f"  [AURA] Fix it with:  pip install {pip_name}")
    print(f"  [AURA] Or just run:  pip install -r requirements.txt\n")
    sys.exit(1)

try:
    import numpy as np
except ImportError:
    _need("numpy", '"numpy<2"')

try:
    import cv2
except ImportError:
    _need("opencv-python", "opencv-python")

try:
    import mediapipe as mp
except ImportError:
    _need("mediapipe", "mediapipe")

try:
    import pyautogui
except ImportError:
    _need("pyautogui", "pyautogui")

try:
    import speech_recognition as sr
except ImportError:
    _need("SpeechRecognition", "SpeechRecognition")

try:
    import keyboard as kb
except ImportError:
    _need("keyboard", "keyboard")

try:
    import pyttsx3
except ImportError:
    _need("pyttsx3", "pyttsx3")

if os.name == "nt":
    import winsound

pyautogui.FAILSAFE = False   # your hand IS the failsafe
pyautogui.PAUSE = 0.0

SCREEN_W, SCREEN_H = pyautogui.size()


# ════════════════════════════════════════════════════════════════════════════
#  FEEDBACK — beeps + text-to-speech (non-blocking)
# ════════════════════════════════════════════════════════════════════════════

class Voice:
    """Background text-to-speech so AURA can talk without freezing."""

    def __init__(self):
        self.q: "queue.Queue[str]" = queue.Queue()
        self.enabled = CONFIG["VOICE_FEEDBACK"]
        t = threading.Thread(target=self._worker, daemon=True, name="aura-tts")
        t.start()

    def _worker(self):
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 185)
        except Exception:
            self.enabled = False
            return
        while True:
            text = self.q.get()
            if not self.enabled:
                continue
            try:
                engine.say(text)
                engine.runAndWait()
            except Exception:
                pass

    def say(self, text: str):
        if self.enabled and self.q.qsize() < 3:
            self.q.put(text)


VOICE = Voice()


def beep(ok: bool = True):
    if CONFIG["BEEP_FEEDBACK"] and os.name == "nt":
        try:
            winsound.Beep(1200 if ok else 400, 90)
        except Exception:
            pass


def log(msg: str):
    print(f"  [AURA] {msg}")


# ════════════════════════════════════════════════════════════════════════════
#  ACTIONS — everything AURA can do to your PC
# ════════════════════════════════════════════════════════════════════════════

class Actions:
    """All the muscle: windows, apps, desktops, typing, hotkeys."""

    last_command = "—"   # shown on the HUD

    # words → keyboard keys, for "press control alt delete" style commands
    KEYWORDS = {
        "control": "ctrl", "ctrl": "ctrl", "shift": "shift", "alt": "alt",
        "windows": "win", "win": "win", "super": "win", "command": "win",
        "enter": "enter", "intro": "enter", "return": "enter",
        "tab": "tab", "tabulador": "tab",
        "escape": "esc", "esc": "esc",
        "space": "space", "espacio": "space",
        "delete": "delete", "suprimir": "delete",
        "backspace": "backspace", "borrar": "backspace",
        "up": "up", "down": "down", "left": "left", "right": "right",
        "arriba": "up", "abajo": "down", "izquierda": "left", "derecha": "right",
        "home": "home", "end": "end",
        "page": "page", "next": "pagedown", "prior": "pageup",
        "print": "printscreen",
        **{f"f{i}": f"f{i}" for i in range(1, 13)},
        **{c: c for c in "abcdefghijklmnopqrstuvwxyz0123456789"},
    }

    @classmethod
    def _did(cls, what: str, say: str | None = None):
        cls.last_command = what
        log(what)
        beep(True)
        if say:
            VOICE.say(say)

    # ── apps ───────────────────────────────────────────────────────────────
    @classmethod
    def open_app(cls, name: str) -> bool:
        name = name.strip().lower()
        target = CONFIG["APPS"].get(name)
        if target is None:
            # try the longest alias contained in what was heard
            for alias in sorted(CONFIG["APPS"], key=len, reverse=True):
                if alias in name:
                    target = CONFIG["APPS"][alias]
                    name = alias
                    break
        try:
            if target:
                if target.endswith(":"):
                    os.startfile(target)            # ms-settings: style URIs
                else:
                    subprocess.Popen(f'start "" "{target}"', shell=True)
            else:
                # unknown app: let Windows figure it out
                subprocess.Popen(f'start "" "{name}"', shell=True)
            cls._did(f"open {name}", f"Opening {name}")
            return True
        except Exception as e:
            log(f"could not open {name}: {e}")
            beep(False)
            return False

    @classmethod
    def web_search(cls, query: str):
        webbrowser.open(f"https://www.google.com/search?q={query.replace(' ', '+')}")
        cls._did(f"search: {query}", "Searching")

    # ── window management ──────────────────────────────────────────────────
    @classmethod
    def close_window(cls):
        pyautogui.hotkey("alt", "f4")
        cls._did("close window", "Closed")

    @classmethod
    def minimize_window(cls):
        pyautogui.hotkey("win", "down")
        cls._did("minimize window")

    @classmethod
    def maximize_window(cls):
        pyautogui.hotkey("win", "up")
        cls._did("maximize window")

    @classmethod
    def snap(cls, side: str):
        pyautogui.hotkey("win", side)
        cls._did(f"snap {side}")

    @classmethod
    def alt_tab(cls):
        pyautogui.hotkey("alt", "tab")
        cls._did("switch app")

    @classmethod
    def show_desktop(cls):
        pyautogui.hotkey("win", "d")
        cls._did("show desktop")

    # ── virtual desktops ───────────────────────────────────────────────────
    @classmethod
    def desktop(cls, direction: str):
        if direction == "new":
            pyautogui.hotkey("ctrl", "win", "d")
            cls._did("new desktop", "New desktop")
        elif direction == "close":
            pyautogui.hotkey("ctrl", "win", "f4")
            cls._did("close desktop")
        else:
            pyautogui.hotkey("ctrl", "win", direction)
            cls._did(f"desktop {direction}")

    # ── media / system ─────────────────────────────────────────────────────
    @classmethod
    def volume(cls, what: str, times: int = 4):
        key = {"up": "volumeup", "down": "volumedown", "mute": "volumemute"}[what]
        for _ in range(1 if what == "mute" else times):
            pyautogui.press(key)
        cls._did(f"volume {what}")

    @classmethod
    def media(cls, what: str):
        key = {"play": "playpause", "pause": "playpause",
               "next": "nexttrack", "previous": "prevtrack"}[what]
        pyautogui.press(key)
        cls._did(f"media {what}")

    @classmethod
    def screenshot(cls):
        folder = os.path.join(os.path.expanduser("~"), "Pictures")
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"AURA_{int(time.time())}.png")
        pyautogui.screenshot(path)
        cls._did(f"screenshot → {path}", "Screenshot saved")

    @classmethod
    def lock_pc(cls):
        cls._did("locking PC", "Locking")
        subprocess.Popen("rundll32.exe user32.dll,LockWorkStation", shell=True)

    # ── typing ─────────────────────────────────────────────────────────────
    @classmethod
    def type_text(cls, text: str):
        if text:
            kb.write(text)          # kb.write handles unicode (¿ á ñ ...)
            cls.last_command = f"typed: {text[:32]}"

    @classmethod
    def press_combo(cls, words: list[str]) -> bool:
        """ "press control shift escape" → Ctrl+Shift+Esc """
        keys = [cls.KEYWORDS[w] for w in words if w in cls.KEYWORDS]
        if not keys:
            return False
        if len(keys) == 1:
            pyautogui.press(keys[0])
        else:
            pyautogui.hotkey(*keys)
        cls._did("press " + "+".join(keys))
        return True


# ════════════════════════════════════════════════════════════════════════════
#  VOICE ENGINE — speech → commands & dictation
# ════════════════════════════════════════════════════════════════════════════

# spoken word → punctuation/symbol (English + Spanish, because why not)
PUNCTUATION = {
    "comma": ",", "coma": ",",
    "dot": ".", "period": ".", "point": ".", "punto": ".",
    "question mark": "?", "question": "?", "interrogation": "?",
    "interrogación": "?", "interrogacion": "?",
    "open question": "¿", "open interrogation": "¿", "abrir interrogación": "¿",
    "exclamation mark": "!", "exclamation": "!", "exclamación": "!", "exclamacion": "!",
    "open exclamation": "¡",
    "colon": ":", "dos puntos": ":",
    "semicolon": ";", "punto y coma": ";",
    "dash": "-", "hyphen": "-", "guión": "-", "guion": "-",
    "underscore": "_",
    "quote": '"', "quotes": '"', "comillas": '"',
    "apostrophe": "'",
    "open parenthesis": "(", "close parenthesis": ")",
    "open bracket": "[", "close bracket": "]",
    "open brace": "{", "close brace": "}",
    "at sign": "@", "at symbol": "@", "arroba": "@",
    "hashtag": "#", "hash": "#", "almohadilla": "#",
    "dollar": "$", "percent": "%", "ampersand": "&",
    "asterisk": "*", "asterisco": "*",
    "plus": "+", "minus": "-", "equals": "=", "igual": "=",
    "slash": "/", "backslash": "\\",
    "greater than": ">", "less than": "<",
    "ellipsis": "...",
    "smiley": ":)",
}

# letter-by-letter mode: plain letters + NATO alphabet + Spanish names
LETTERS = {
    **{c: c for c in "abcdefghijklmnopqrstuvwxyz0123456789"},
    "alpha": "a", "bravo": "b", "charlie": "c", "delta": "d", "echo": "e",
    "foxtrot": "f", "golf": "g", "hotel": "h", "india": "i", "juliet": "j",
    "kilo": "k", "lima": "l", "mike": "m", "november": "n", "oscar": "o",
    "papa": "p", "quebec": "q", "romeo": "r", "sierra": "s", "tango": "t",
    "uniform": "u", "victor": "v", "whiskey": "w", "xray": "x", "x-ray": "x",
    "yankee": "y", "zulu": "z",
    "be": "b", "bee": "b", "see": "c", "ce": "c", "de": "d", "dee": "d",
    "efe": "f", "ge": "g", "ache": "h", "hache": "h", "jay": "j", "jota": "j",
    "kay": "k", "ka": "k", "ele": "l", "el": "l", "eme": "m", "em": "m",
    "ene": "n", "en": "n", "eñe": "ñ", "pe": "p", "pee": "p", "cu": "q",
    "are": "r", "erre": "r", "ese": "s", "te": "t", "tea": "t", "tee": "t",
    "uve": "v", "vee": "v", "why": "y", "zeta": "z", "zed": "z", "zee": "z",
    "double you": "w", "doble uve": "w",
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "cero": "0", "uno": "1", "dos": "2", "tres": "3", "cuatro": "4",
    "cinco": "5", "seis": "6", "siete": "7", "ocho": "8", "nueve": "9",
}

MODE_COMMAND, MODE_WORD, MODE_LETTER = "COMMAND", "DICTATION", "LETTER"


class VoiceEngine(threading.Thread):
    """Listens forever in the background. Three personalities:

    COMMAND  → "open chrome", "close window", "press control c", ...
    DICTATION→ types what you say, word by word, spoken punctuation included
    LETTER   → spell letter by letter, letters glued together automatically
    """

    def __init__(self):
        super().__init__(daemon=True, name="aura-voice")
        self.enabled = True
        self.running = True
        self.mode = MODE_COMMAND
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = CONFIG["ENERGY_THRESHOLD"]
        self.recognizer.dynamic_energy_threshold = True
        self.last_heard = "—"

    # ── main loop ──────────────────────────────────────────────────────────
    def run(self):
        try:
            mic = sr.Microphone()
        except Exception as e:
            log(f"no microphone found ({e}) — voice control disabled")
            self.enabled = False
            return

        with mic as source:
            log("calibrating microphone (1s of silence please)...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
        log(f"voice online — language {CONFIG['LANGUAGE']} — say something!")
        VOICE.say("Aura voice online")

        while self.running:
            if not self.enabled:
                time.sleep(0.25)
                continue
            try:
                with mic as source:
                    audio = self.recognizer.listen(
                        source, timeout=4,
                        phrase_time_limit=CONFIG["PHRASE_TIME_LIMIT"])
            except sr.WaitTimeoutError:
                continue
            except Exception:
                time.sleep(0.5)
                continue
            try:
                text = self.recognizer.recognize_google(
                    audio, language=CONFIG["LANGUAGE"]).lower().strip()
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                log(f"speech service error: {e} (need internet)")
                time.sleep(1.0)
                continue
            if text:
                self.last_heard = text
                log(f'heard: "{text}"  [{self.mode}]')
                try:
                    self.handle(text)
                except Exception as e:
                    log(f"command error: {e}")

    # ── dispatch ───────────────────────────────────────────────────────────
    def handle(self, text: str):
        if self._mode_switch(text):
            return
        if self.mode == MODE_WORD:
            self._dictate_words(text)
        elif self.mode == MODE_LETTER:
            self._dictate_letters(text)
        else:
            self._command(text)

    def _mode_switch(self, text: str) -> bool:
        t = text.replace("-", " ")
        if any(p in t for p in ("letter mode", "letter by letter", "spell mode",
                                "modo letras", "letra por letra")):
            self.mode = MODE_LETTER
            Actions._did("mode → LETTER", "Letter mode")
            return True
        if any(p in t for p in ("dictation mode", "word mode", "typing mode",
                                "start dictation", "modo dictado", "modo palabras")):
            self.mode = MODE_WORD
            Actions._did("mode → DICTATION", "Dictation mode")
            return True
        if any(p in t for p in ("command mode", "stop dictation", "stop typing",
                                "exit mode", "modo comandos", "para el dictado")):
            self.mode = MODE_COMMAND
            Actions._did("mode → COMMAND", "Command mode")
            return True
        return False

    # ── COMMAND mode ───────────────────────────────────────────────────────
    def _command(self, text: str):
        words = text.split()

        # "press <keys>" / "pulsa <keys>" — raw hotkeys
        if words[0] in ("press", "pulsa", "presiona", "hold") and len(words) > 1:
            if Actions.press_combo(words[1:]):
                return

        # "open <app>" / "abre <app>" / "launch <app>"
        for trigger in ("open ", "launch ", "start ", "abre ", "abrir "):
            if text.startswith(trigger):
                Actions.open_app(text[len(trigger):])
                return

        # "search for cats" / "busca gatos"
        for trigger in ("search for ", "search ", "google ", "busca ", "buscar "):
            if text.startswith(trigger) and len(text) > len(trigger):
                Actions.web_search(text[len(trigger):])
                return

        # "type hello world" — quick one-shot typing without switching modes
        for trigger in ("type ", "write ", "escribe "):
            if text.startswith(trigger):
                Actions.type_text(text[len(trigger):])
                return

        COMMANDS = {
            ("close window", "close app", "close this", "cierra la ventana",
             "cierra esto"): Actions.close_window,
            ("minimize", "minimise", "minimiza"): Actions.minimize_window,
            ("maximize", "maximise", "maximiza"): Actions.maximize_window,
            ("snap left",): lambda: Actions.snap("left"),
            ("snap right",): lambda: Actions.snap("right"),
            ("switch app", "switch window", "alt tab", "cambia de app"):
                Actions.alt_tab,
            ("show desktop", "muestra el escritorio"): Actions.show_desktop,
            ("next desktop", "desktop right", "siguiente escritorio"):
                lambda: Actions.desktop("right"),
            ("previous desktop", "desktop left", "escritorio anterior"):
                lambda: Actions.desktop("left"),
            ("new desktop", "nuevo escritorio"): lambda: Actions.desktop("new"),
            ("close desktop", "cierra el escritorio"): lambda: Actions.desktop("close"),
            ("volume up", "louder", "sube el volumen"): lambda: Actions.volume("up"),
            ("volume down", "quieter", "baja el volumen"): lambda: Actions.volume("down"),
            ("mute", "silencio"): lambda: Actions.volume("mute"),
            ("play", "pause", "reproduce", "pausa"): lambda: Actions.media("play"),
            ("next song", "next track", "siguiente canción"): lambda: Actions.media("next"),
            ("previous song", "previous track", "canción anterior"):
                lambda: Actions.media("previous"),
            ("screenshot", "take a screenshot", "captura de pantalla"):
                Actions.screenshot,
            ("lock the computer", "lock pc", "bloquea el ordenador"): Actions.lock_pc,
            ("scroll up", "sube"): lambda: pyautogui.scroll(400),
            ("scroll down", "baja"): lambda: pyautogui.scroll(-400),
            ("click", "left click", "haz clic"): pyautogui.click,
            ("right click", "clic derecho"): pyautogui.rightClick,
            ("double click", "doble clic"): pyautogui.doubleClick,
            ("copy", "copia"): lambda: pyautogui.hotkey("ctrl", "c"),
            ("paste", "pega"): lambda: pyautogui.hotkey("ctrl", "v"),
            ("cut", "corta"): lambda: pyautogui.hotkey("ctrl", "x"),
            ("undo", "deshacer"): lambda: pyautogui.hotkey("ctrl", "z"),
            ("redo", "rehacer"): lambda: pyautogui.hotkey("ctrl", "y"),
            ("select all", "selecciona todo"): lambda: pyautogui.hotkey("ctrl", "a"),
            ("save", "guarda"): lambda: pyautogui.hotkey("ctrl", "s"),
            ("new tab", "nueva pestaña"): lambda: pyautogui.hotkey("ctrl", "t"),
            ("close tab", "cierra la pestaña"): lambda: pyautogui.hotkey("ctrl", "w"),
            ("refresh", "reload", "recarga"): lambda: pyautogui.press("f5"),
            ("full screen", "pantalla completa"): lambda: pyautogui.press("f11"),
            ("go back", "atrás"): lambda: pyautogui.hotkey("alt", "left"),
            ("go forward", "adelante"): lambda: pyautogui.hotkey("alt", "right"),
            ("enter", "intro"): lambda: pyautogui.press("enter"),
            ("escape",): lambda: pyautogui.press("esc"),
            ("task manager", "administrador de tareas"):
                lambda: pyautogui.hotkey("ctrl", "shift", "esc"),
            ("task view", "vista de tareas"): lambda: pyautogui.hotkey("win", "tab"),
        }
        for phrases, action in COMMANDS.items():
            if any(p in text for p in phrases):
                action()
                Actions.last_command = phrases[0]
                beep(True)
                return

        log(f'unknown command: "{text}" (say "dictation mode" to type instead)')

    # ── DICTATION mode (word by word) ──────────────────────────────────────
    def _dictate_words(self, text: str):
        if self._dictation_controls(text):
            return
        out, pending_space = "", False
        for token in text.split():
            symbol = PUNCTUATION.get(token)
            if symbol:
                out += symbol           # punctuation glues to previous word
                pending_space = True
            else:
                if pending_space or out:
                    out += " "
                out += token
                pending_space = False
        Actions.type_text(out + " ")

    # ── LETTER mode (letters glued together) ───────────────────────────────
    def _dictate_letters(self, text: str):
        if self._dictation_controls(text):
            return
        out = ""
        tokens = text.replace("-", " ").split()
        i = 0
        while i < len(tokens):
            two = " ".join(tokens[i:i + 2])
            if two in PUNCTUATION:           # "question mark" = 2 tokens
                out += PUNCTUATION[two]
                i += 2
                continue
            tok = tokens[i]
            if tok in LETTERS:
                out += LETTERS[tok]
            elif tok in PUNCTUATION:
                out += PUNCTUATION[tok]
            elif tok in ("space", "espacio"):
                out += " "
            elif len(tok) > 1 and tok.isalpha():
                out += tok[0]                # "f" heard as "ef" → first letter
            i += 1
        Actions.type_text(out)

    def _dictation_controls(self, text: str) -> bool:
        t = text.strip()
        if t in ("new line", "next line", "nueva línea", "nueva linea"):
            pyautogui.press("enter")
            return True
        if t in ("space", "espacio") and self.mode == MODE_WORD:
            pyautogui.press("space")
            return True
        if t in ("delete that", "delete word", "borra eso"):
            pyautogui.hotkey("ctrl", "backspace")
            return True
        if t in ("delete letter", "backspace", "borra letra"):
            pyautogui.press("backspace")
            return True
        if t in ("press enter", "pulsa intro"):
            pyautogui.press("enter")
            return True
        if t in ("press tab", "pulsa tab"):
            pyautogui.press("tab")
            return True
        return False


# ════════════════════════════════════════════════════════════════════════════
#  GESTURE ENGINE — hand → mouse + actions
# ════════════════════════════════════════════════════════════════════════════

# MediaPipe hand landmark indices
WRIST, THUMB_TIP, THUMB_IP = 0, 4, 3
INDEX_TIP, INDEX_PIP, INDEX_MCP = 8, 6, 5
MIDDLE_TIP, MIDDLE_PIP, MIDDLE_MCP = 12, 10, 9
RING_TIP, RING_PIP = 16, 14
PINKY_TIP, PINKY_PIP = 20, 18


class GestureEngine:
    """Webcam loop. One hand = full mouse + window control.

    ☝️  index only        → move cursor
    🤏  thumb+index pinch → left click (pinch & hold = drag)
    🤌  thumb+middle pinch→ right click
    ✌️  index+middle      → scroll up/down
    🤟  index+middle+ring → swipe ←/→ to switch virtual desktop
    ✊  fist (hold)       → close window (Alt+F4) — HUD shows countdown
    🖐️  open palm (hold)  → pause / resume gesture control
    🤙  pinky only        → minimize window
    👍  thumbs up         → volume up        👎 thumbs down → volume down
    """

    def __init__(self, show_preview: bool = True):
        self.enabled = True
        self.running = True
        self.paused = False
        self.show_preview = show_preview
        self.gesture_name = "—"

        self.prev_x, self.prev_y = SCREEN_W / 2, SCREEN_H / 2
        self.last_click = 0.0
        self.last_action = 0.0
        self.fist_since = 0.0
        self.palm_since = 0.0
        self.dragging = False
        self.scroll_anchor = None
        self.swipe_anchor = None     # (x, time)
        self.prev_frame_time = 0.0

        self.hands = mp.solutions.hands.Hands(
            max_num_hands=1,
            model_complexity=0,      # 0 = fastest
            min_detection_confidence=CONFIG["DETECTION_CONFIDENCE"],
            min_tracking_confidence=CONFIG["TRACKING_CONFIDENCE"],
        )
        self.drawer = mp.solutions.drawing_utils
        self.styles = mp.solutions.drawing_styles

    # ── finger state helpers ───────────────────────────────────────────────
    @staticmethod
    def _dist(a, b) -> float:
        return math.hypot(a.x - b.x, a.y - b.y)

    def _fingers_up(self, lm) -> list[bool]:
        """[thumb, index, middle, ring, pinky] — True = extended."""
        hand_size = self._dist(lm[WRIST], lm[MIDDLE_MCP]) + 1e-6
        thumb = self._dist(lm[THUMB_TIP], lm[PINKY_PIP]) / hand_size > 0.9
        fingers = [thumb]
        for tip, pip in ((INDEX_TIP, INDEX_PIP), (MIDDLE_TIP, MIDDLE_PIP),
                         (RING_TIP, RING_PIP), (PINKY_TIP, PINKY_PIP)):
            fingers.append(lm[tip].y < lm[pip].y)
        return fingers

    def _pinch(self, lm, finger_tip: int) -> bool:
        hand_size = self._dist(lm[WRIST], lm[MIDDLE_MCP]) + 1e-6
        return self._dist(lm[THUMB_TIP], lm[finger_tip]) / hand_size < CONFIG["PINCH_THRESHOLD"]

    # ── gesture logic ──────────────────────────────────────────────────────
    def _process_hand(self, lm, now: float):
        fingers = self._fingers_up(lm)
        thumb, index, middle, ring, pinky = fingers
        n_up = sum(fingers)
        cooldown_ok = now - self.last_action > CONFIG["ACTION_COOLDOWN"]

        # ── open palm: pause / resume ──────────────────────────────────────
        if n_up == 5:
            self.gesture_name = "open palm 🖐️"
            if self.palm_since == 0.0:
                self.palm_since = now
            elif now - self.palm_since > CONFIG["PALM_HOLD_TIME"] and cooldown_ok:
                self.paused = not self.paused
                self.last_action = now
                self.palm_since = 0.0
                Actions._did("gestures PAUSED" if self.paused else "gestures RESUMED",
                             "Paused" if self.paused else "Resumed")
            self._end_drag()
            self.fist_since = 0.0
            return
        self.palm_since = 0.0

        if self.paused:
            self.gesture_name = "paused (palm to resume)"
            return

        # ── fist: hold to close window ─────────────────────────────────────
        if n_up == 0:
            held = now - self.fist_since if self.fist_since else 0.0
            remaining = CONFIG["FIST_HOLD_TIME"] - held
            self.gesture_name = f"fist ✊ close in {max(remaining, 0):.1f}s"
            if self.fist_since == 0.0:
                self.fist_since = now
            elif held > CONFIG["FIST_HOLD_TIME"] and cooldown_ok:
                Actions.close_window()
                self.last_action = now
                self.fist_since = 0.0
            self._end_drag()
            return
        self.fist_since = 0.0

        # ── thumbs up / down: volume ───────────────────────────────────────
        if thumb and n_up == 1:
            if lm[THUMB_TIP].y < lm[WRIST].y - 0.05:
                self.gesture_name = "thumbs up 👍"
                if cooldown_ok:
                    Actions.volume("up")
                    self.last_action = now
            elif lm[THUMB_TIP].y > lm[WRIST].y + 0.05:
                self.gesture_name = "thumbs down 👎"
                if cooldown_ok:
                    Actions.volume("down")
                    self.last_action = now
            return

        # ── pinky only: minimize ───────────────────────────────────────────
        if pinky and not index and not middle and not ring:
            self.gesture_name = "pinky 🤙 minimize"
            if cooldown_ok:
                Actions.minimize_window()
                self.last_action = now
            return

        # ── three fingers: swipe to switch desktop ─────────────────────────
        if index and middle and ring and not pinky:
            self.gesture_name = "three fingers 🤟 swipe ←/→"
            x = lm[INDEX_TIP].x
            if self.swipe_anchor is None:
                self.swipe_anchor = (x, now)
            else:
                x0, t0 = self.swipe_anchor
                dt = now - t0
                if dt > 0.05:
                    speed = (x - x0) / dt        # frame is mirrored already
                    if abs(speed) > CONFIG["SWIPE_SPEED"] * 10 and cooldown_ok:
                        Actions.desktop("right" if speed > 0 else "left")
                        self.last_action = now
                        self.swipe_anchor = None
                    else:
                        self.swipe_anchor = (x, now)
            return
        self.swipe_anchor = None

        # ── two fingers: scroll ────────────────────────────────────────────
        if index and middle and not ring and not pinky and not self._pinch(lm, INDEX_TIP):
            self.gesture_name = "scroll ✌️"
            y = lm[INDEX_TIP].y
            if self.scroll_anchor is None:
                self.scroll_anchor = y
            else:
                delta = self.scroll_anchor - y
                if abs(delta) > 0.012:
                    pyautogui.scroll(int(delta * 100) * CONFIG["SCROLL_SPEED"])
                    self.scroll_anchor = y
            self._end_drag()
            return
        self.scroll_anchor = None

        # ── index (+thumb): cursor + clicks ────────────────────────────────
        if index and not middle and not ring and not pinky:
            self._move_cursor(lm)
            if self._pinch(lm, INDEX_TIP):
                self.gesture_name = "pinch 🤏 click/drag"
                if not self.dragging and now - self.last_click > CONFIG["CLICK_COOLDOWN"]:
                    pyautogui.mouseDown()
                    self.dragging = True
                    self.last_click = now
                    Actions.last_command = "click / drag"
                    beep(True)
            else:
                self.gesture_name = "cursor ☝️"
                self._end_drag()
            return

        # ── middle-finger pinch: right click ───────────────────────────────
        if index and middle and self._pinch(lm, MIDDLE_TIP):
            self.gesture_name = "right click 🤌"
            if now - self.last_click > CONFIG["CLICK_COOLDOWN"]:
                pyautogui.rightClick()
                self.last_click = now
                Actions.last_command = "right click"
                beep(True)
            return

        self.gesture_name = "—"
        self._end_drag()

    def _move_cursor(self, lm):
        m = CONFIG["CONTROL_MARGIN"]
        x = np.interp(lm[INDEX_TIP].x, (m, 1 - m), (0, SCREEN_W))
        y = np.interp(lm[INDEX_TIP].y, (m, 1 - m), (0, SCREEN_H))
        s = CONFIG["SMOOTHING"]
        self.prev_x += (x - self.prev_x) * s
        self.prev_y += (y - self.prev_y) * s
        pyautogui.moveTo(int(self.prev_x), int(self.prev_y))

    def _end_drag(self):
        if self.dragging:
            pyautogui.mouseUp()
            self.dragging = False

    # ── HUD ────────────────────────────────────────────────────────────────
    def _draw_hud(self, frame, voice: "VoiceEngine | None", fps: float):
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (0, 0), (w, 78), (20, 16, 12), -1)
        cv2.putText(frame, "A U R A", (16, 32),
                    cv2.FONT_HERSHEY_DUPLEX, 0.9, (80, 220, 255), 2)
        status = "PAUSED" if self.paused else ("ON" if self.enabled else "OFF")
        cv2.putText(frame, f"gestures: {status}   fps: {fps:.0f}", (16, 62),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 180, 180), 1)
        cv2.putText(frame, f"gesture: {self.gesture_name}", (260, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.62, (120, 255, 120), 2)
        mode = voice.mode if voice and voice.enabled else "voice off"
        cv2.putText(frame, f"voice: {mode}", (260, 62),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 200, 90), 1)
        cv2.rectangle(frame, (0, h - 34), (w, h), (20, 16, 12), -1)
        cv2.putText(frame, f"last: {Actions.last_command}", (16, h - 11),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 255), 1)
        # control area border
        m = CONFIG["CONTROL_MARGIN"]
        cv2.rectangle(frame, (int(w * m), int(h * m)),
                      (int(w * (1 - m)), int(h * (1 - m))), (60, 60, 90), 1)

    # ── main loop ──────────────────────────────────────────────────────────
    def run(self, voice: "VoiceEngine | None" = None):
        cap = cv2.VideoCapture(CONFIG["CAMERA_INDEX"], cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, CONFIG["FRAME_WIDTH"])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CONFIG["FRAME_HEIGHT"])
        if not cap.isOpened():
            log("no camera found — gesture control disabled (voice still works)")
            self.enabled = False
            while self.running:        # keep main thread alive for voice
                time.sleep(0.5)
            return

        log("camera online — show me your hand!")
        VOICE.say("Aura gestures online")

        while self.running:
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.05)
                continue
            frame = cv2.flip(frame, 1)               # mirror = natural control
            now = time.time()

            if self.enabled:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                results = self.hands.process(rgb)
                if results.multi_hand_landmarks:
                    hand = results.multi_hand_landmarks[0]
                    try:
                        self._process_hand(hand.landmark, now)
                    except Exception as e:
                        log(f"gesture error: {e}")
                    if self.show_preview:
                        self.drawer.draw_landmarks(
                            frame, hand, mp.solutions.hands.HAND_CONNECTIONS,
                            self.styles.get_default_hand_landmarks_style(),
                            self.styles.get_default_hand_connections_style())
                else:
                    self.gesture_name = "no hand"
                    self.fist_since = self.palm_since = 0.0
                    self.swipe_anchor = self.scroll_anchor = None
                    self._end_drag()

            if self.show_preview:
                fps = 1.0 / max(now - self.prev_frame_time, 1e-6)
                self.prev_frame_time = now
                self._draw_hud(frame, voice, fps)
                cv2.imshow("AURA — q to quit", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    self.running = False
            else:
                time.sleep(0.001)

        cap.release()
        cv2.destroyAllWindows()


# ════════════════════════════════════════════════════════════════════════════
#  SELF-TEST — verify the install without camera or mic
# ════════════════════════════════════════════════════════════════════════════

def self_test() -> int:
    print()
    log("running self-test (no camera/mic needed)...")
    checks = []
    checks.append(("numpy", np.__version__))
    checks.append(("opencv", cv2.__version__))
    checks.append(("mediapipe", mp.__version__))
    hands = mp.solutions.hands.Hands(max_num_hands=1, model_complexity=0)
    hands.close()
    checks.append(("mediapipe Hands model", "loads OK"))
    checks.append(("pyautogui", f"screen {SCREEN_W}x{SCREEN_H}"))
    checks.append(("SpeechRecognition", sr.__version__))
    r = sr.Recognizer()
    checks.append(("Recognizer", "builds OK"))
    checks.append(("keyboard", "imported OK"))
    try:
        engine = pyttsx3.init()
        del engine
        checks.append(("pyttsx3 TTS", "init OK"))
    except Exception as e:
        checks.append(("pyttsx3 TTS", f"warning: {e}"))
    ge = GestureEngine.__new__(GestureEngine)  # check class builds
    checks.append(("GestureEngine", "class OK"))
    ve = VoiceEngine()
    checks.append(("VoiceEngine", "builds OK"))
    print()
    for name, info in checks:
        print(f"   ✓  {name:<24} {info}")
    print()
    log("self-test PASSED — you're ready: python aura.py")
    return 0


# ════════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════════

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="aura", description="AURA — control your PC with hands & voice")
    parser.add_argument("--no-camera", action="store_true", help="disable gestures")
    parser.add_argument("--no-voice", action="store_true", help="disable voice")
    parser.add_argument("--no-preview", action="store_true", help="hide camera window")
    parser.add_argument("--lang", default=None, help="speech language, e.g. es-ES")
    parser.add_argument("--camera", type=int, default=None, help="camera index")
    parser.add_argument("--quiet", action="store_true", help="no TTS voice feedback")
    parser.add_argument("--self-test", action="store_true", help="verify install & exit")
    args = parser.parse_args()

    if args.lang:
        CONFIG["LANGUAGE"] = args.lang
    if args.camera is not None:
        CONFIG["CAMERA_INDEX"] = args.camera
    if args.quiet:
        CONFIG["VOICE_FEEDBACK"] = False
        VOICE.enabled = False

    if args.self_test:
        return self_test()

    print(__doc__.split("ONE FILE")[0])
    log(f"screen: {SCREEN_W}x{SCREEN_H}   language: {CONFIG['LANGUAGE']}")
    log("hotkeys: Ctrl+Alt+G gestures · Ctrl+Alt+V voice · Ctrl+Alt+Q quit")

    voice = None
    if not args.no_voice:
        voice = VoiceEngine()
        voice.start()

    gestures = GestureEngine(show_preview=not args.no_preview)
    if args.no_camera:
        gestures.enabled = False

    # global hotkeys
    def toggle_gestures():
        gestures.enabled = not gestures.enabled
        Actions._did(f"gestures {'ON' if gestures.enabled else 'OFF'}")

    def toggle_voice():
        if voice:
            voice.enabled = not voice.enabled
            Actions._did(f"voice {'ON' if voice.enabled else 'OFF'}")

    def quit_aura():
        log("bye! 👋")
        gestures.running = False
        if voice:
            voice.running = False
        os._exit(0)

    try:
        kb.add_hotkey("ctrl+alt+g", toggle_gestures)
        kb.add_hotkey("ctrl+alt+v", toggle_voice)
        kb.add_hotkey("ctrl+alt+q", quit_aura)
    except Exception as e:
        log(f"global hotkeys unavailable: {e}")

    try:
        if args.no_camera:
            log("camera disabled — voice-only mode. Ctrl+Alt+Q to quit.")
            while voice and voice.running:
                time.sleep(0.5)
        else:
            gestures.run(voice)      # blocks until 'q' or quit hotkey
    except KeyboardInterrupt:
        pass
    finally:
        if voice:
            voice.running = False
    log("bye! 👋")
    return 0


if __name__ == "__main__":
    sys.exit(main())
