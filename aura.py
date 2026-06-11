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
║      A U R A  v2  —  Air User, Real Actions                               ║
║      Control your entire PC with your HANDS and your VOICE.               ║
║      Zero keyboard. Zero mouse. Pure air.                                 ║
║                                                                           ║
║      https://github.com/moha20299ea-blip/AURA                             ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

ONE FILE. Run it: your webcam becomes a mouse, your mic becomes a keyboard,
and there's a floating AIR KEYBOARD you type on with your fingers. ⌨️✨

    python aura.py                  # full experience (camera + voice)
    python aura.py --mode pro       # unlock every gesture
    python aura.py --lang es-ES     # háblale en español
    python aura.py --no-camera      # voice only
    python aura.py --no-voice       # gestures only
    python aura.py --no-preview     # hide the camera window
    python aura.py --self-test      # verify install, no camera/mic needed

KEYS ON THE CAMERA WINDOW:
    K  air keyboard on/off      M  cycle easy/normal/pro mode
    L  cycle language           P  pause gestures        Q  quit

GLOBAL HOTKEYS (work anywhere):
    Ctrl+Alt+G  toggle gestures   Ctrl+Alt+V  toggle voice   Ctrl+Alt+Q  quit
"""

from __future__ import annotations

import argparse
import ctypes
import difflib
import math
import os
import queue
import subprocess
import sys
import threading
import time
import webbrowser
from collections import deque

# Windows consoles default to cp1252, which chokes on the banner/✓/emojis
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ════════════════════════════════════════════════════════════════════════════
#  CONFIG — tweak everything here (modes below override some of these live)
# ════════════════════════════════════════════════════════════════════════════

CONFIG = {
    # ── camera / gestures ──────────────────────────────────────────────────
    "CAMERA_INDEX": 0,
    "FRAME_WIDTH": 960,
    "FRAME_HEIGHT": 540,
    "CONTROL_MARGIN": 0.18,     # dead border around frame. Smaller = bigger reach
    "SMOOTHING": 0.35,          # cursor smoothing 0.05 (silky) → 0.9 (raw)
    "PINCH_ON": 0.30,           # pinch closes below this (relative to hand size)
    "PINCH_OFF": 0.42,          # ...and opens above this (hysteresis = no flicker)
    "CLICK_COOLDOWN": 0.45,
    "ACTION_COOLDOWN": 1.20,    # seconds between big actions
    "STABLE_FRAMES": 5,         # frames a gesture must hold before it counts
    "FIST_HOLD_TIME": 1.40,
    "PALM_HOLD_TIME": 1.00,
    "SWIPE_SPEED": 0.45,        # 3-finger swipe speed (screen-widths / second)
    "SCROLL_STEP": 0.012,       # finger travel per scroll tick
    "DETECTION_CONFIDENCE": 0.75,
    "TRACKING_CONFIDENCE": 0.65,

    # ── voice ──────────────────────────────────────────────────────────────
    "LANGUAGE": "en-US",
    "ENERGY_THRESHOLD": 300,
    "PHRASE_TIME_LIMIT": 6,
    "VOICE_FEEDBACK": True,
    "BEEP_FEEDBACK": True,
    "FUZZY_MATCH": 0.74,        # smart command matching 0=off 1=strict

    # ── mode: EASY / NORMAL / PRO ──────────────────────────────────────────
    "MODE": "NORMAL",

    # ── apps you can open by voice: "open <name>" ─────────────────────────
    "APPS": {
        "chrome": "chrome", "google": "chrome", "edge": "msedge",
        "firefox": "firefox", "notepad": "notepad", "bloc de notas": "notepad",
        "calculator": "calc", "calculadora": "calc",
        "explorer": "explorer", "files": "explorer", "archivos": "explorer",
        "paint": "mspaint", "word": "winword", "excel": "excel",
        "powerpoint": "powerpnt", "spotify": "spotify", "discord": "discord",
        "steam": "steam", "terminal": "wt", "cmd": "cmd",
        "powershell": "powershell", "code": "code", "vs code": "code",
        "settings": "ms-settings:", "task manager": "taskmgr",
        "snipping tool": "snippingtool", "camera": "microsoft.windows.camera:",
    },
}

# Modes = presets. EASY has only the chill gestures (nothing destructive),
# PRO unlocks everything and reacts faster.
MODES = {
    "EASY": {
        "gestures": {"cursor", "click", "scroll", "palm", "keyboard"},
        "STABLE_FRAMES": 7, "CLICK_COOLDOWN": 0.60, "ACTION_COOLDOWN": 1.8,
        "SMOOTHING": 0.25,
    },
    "NORMAL": {
        "gestures": {"cursor", "click", "rightclick", "scroll", "palm",
                     "keyboard", "pinky", "thumbs"},
        "STABLE_FRAMES": 5, "CLICK_COOLDOWN": 0.45, "ACTION_COOLDOWN": 1.2,
        "SMOOTHING": 0.35,
    },
    "PRO": {
        "gestures": {"cursor", "click", "rightclick", "scroll", "palm",
                     "keyboard", "pinky", "thumbs", "fist", "swipe"},
        "STABLE_FRAMES": 4, "CLICK_COOLDOWN": 0.35, "ACTION_COOLDOWN": 0.9,
        "SMOOTHING": 0.45,
    },
}

# Languages you can switch to LIVE (voice: "spanish" / "habla español", key: L)
LANGS = {
    "english": "en-US", "inglés": "en-US", "ingles": "en-US",
    "spanish": "es-ES", "español": "es-ES", "espanol": "es-ES",
    "catalan": "ca-ES", "català": "ca-ES", "catalán": "ca-ES",
    "french": "fr-FR", "francés": "fr-FR", "frances": "fr-FR",
    "german": "de-DE", "alemán": "de-DE", "aleman": "de-DE",
    "italian": "it-IT", "italiano": "it-IT",
    "portuguese": "pt-PT", "portugués": "pt-PT", "portugues": "pt-PT",
    "arabic": "ar-SA", "árabe": "ar-SA", "arabe": "ar-SA",
}
LANG_CYCLE = ["en-US", "es-ES", "ca-ES", "fr-FR", "de-DE", "it-IT", "pt-PT", "ar-SA"]


def apply_mode(name: str):
    name = name.upper()
    if name not in MODES:
        return
    CONFIG["MODE"] = name
    for key, val in MODES[name].items():
        if key != "gestures":
            CONFIG[key] = val


apply_mode(CONFIG["MODE"])


def allowed(gesture: str) -> bool:
    return gesture in MODES[CONFIG["MODE"]]["gestures"]


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
    _need("numpy", "numpy")

try:
    import cv2
except ImportError:
    _need("opencv-python", "opencv-python")

try:
    import mediapipe as mp
except ImportError:
    _need("mediapipe", "mediapipe==0.10.14")

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
    try:
        ctypes.windll.user32.SetProcessDPIAware()   # real pixels, no DPI lies
    except Exception:
        pass

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.0

SCREEN_W, SCREEN_H = pyautogui.size()


# ════════════════════════════════════════════════════════════════════════════
#  NATIVE MOUSE — direct Windows API. Instant. This is what killed the
#  v1 freeze: pyautogui calls inside the camera loop blocked frames.
# ════════════════════════════════════════════════════════════════════════════

class Mouse:
    _u32 = ctypes.windll.user32 if os.name == "nt" else None
    LEFTDOWN, LEFTUP = 0x0002, 0x0004
    RIGHTDOWN, RIGHTUP = 0x0008, 0x0010
    WHEEL = 0x0800

    @classmethod
    def move(cls, x: float, y: float):
        if cls._u32:
            cls._u32.SetCursorPos(int(x), int(y))
        else:
            pyautogui.moveTo(int(x), int(y))

    @classmethod
    def _event(cls, flag: int, data: int = 0):
        if cls._u32:
            cls._u32.mouse_event(flag, 0, 0, data, 0)

    @classmethod
    def down(cls):
        cls._event(cls.LEFTDOWN) if cls._u32 else pyautogui.mouseDown()

    @classmethod
    def up(cls):
        cls._event(cls.LEFTUP) if cls._u32 else pyautogui.mouseUp()

    @classmethod
    def right_click(cls):
        if cls._u32:
            cls._event(cls.RIGHTDOWN)
            cls._event(cls.RIGHTUP)
        else:
            pyautogui.rightClick()

    @classmethod
    def scroll(cls, ticks: int):
        if cls._u32:
            cls._event(cls.WHEEL, ticks * 120)
        else:
            pyautogui.scroll(ticks * 120)


# ════════════════════════════════════════════════════════════════════════════
#  WORKER — every slow action (hotkeys, typing, opening apps) runs here,
#  NEVER in the camera loop. Camera stays at full FPS no matter what.
# ════════════════════════════════════════════════════════════════════════════

class Worker(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True, name="aura-worker")
        self.q: "queue.Queue" = queue.Queue()
        self.start()

    def run(self):
        while True:
            fn = self.q.get()
            try:
                fn()
            except Exception as e:
                log(f"action error: {e}")


WORKER = Worker()


def do(fn):
    """Queue an action so the camera never waits for it."""
    if WORKER.q.qsize() < 16:
        WORKER.q.put(fn)


# ════════════════════════════════════════════════════════════════════════════
#  FEEDBACK — beeps + text-to-speech (non-blocking)
# ════════════════════════════════════════════════════════════════════════════

class TTS:
    def __init__(self):
        self.q: "queue.Queue[str]" = queue.Queue()
        self.enabled = CONFIG["VOICE_FEEDBACK"]
        threading.Thread(target=self._worker, daemon=True, name="aura-tts").start()

    def _worker(self):
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 190)
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
        if self.enabled and self.q.qsize() < 2:
            self.q.put(text)


VOICE = TTS()


def beep(ok: bool = True):
    if CONFIG["BEEP_FEEDBACK"] and os.name == "nt":
        try:
            winsound.Beep(1200 if ok else 400, 70)
        except Exception:
            pass


def log(msg: str):
    print(f"  [AURA] {msg}")


# ════════════════════════════════════════════════════════════════════════════
#  ACTIONS — everything AURA can do to your PC
# ════════════════════════════════════════════════════════════════════════════

class Actions:
    last_command = "—"

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
        "home": "home", "end": "end", "print": "printscreen",
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
            for alias in sorted(CONFIG["APPS"], key=len, reverse=True):
                if alias in name:
                    target, name = CONFIG["APPS"][alias], alias
                    break
        try:
            if target:
                if target.endswith(":"):
                    os.startfile(target)
                else:
                    subprocess.Popen(f'start "" "{target}"', shell=True)
            else:
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
            kb.write(text)              # kb.write handles unicode (¿ á ñ ...)
            cls.last_command = f"typed: {text[:32]}"

    @classmethod
    def press_combo(cls, words: list[str]) -> bool:
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
#  VOICE ENGINE — speech → commands & dictation (with smart fuzzy matching)
# ════════════════════════════════════════════════════════════════════════════

PUNCTUATION = {
    "comma": ",", "coma": ",",
    "dot": ".", "period": ".", "point": ".", "punto": ".",
    "question mark": "?", "question": "?", "interrogation": "?",
    "interrogación": "?", "interrogacion": "?",
    "open question": "¿", "open interrogation": "¿", "abrir interrogación": "¿",
    "exclamation mark": "!", "exclamation": "!", "exclamación": "!",
    "exclamacion": "!", "open exclamation": "¡",
    "colon": ":", "dos puntos": ":",
    "semicolon": ";", "punto y coma": ";",
    "dash": "-", "hyphen": "-", "guión": "-", "guion": "-",
    "underscore": "_",
    "quote": '"', "quotes": '"', "comillas": '"', "apostrophe": "'",
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
    "ellipsis": "...", "smiley": ":)",
}

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
    """Listens forever in the background.

    COMMAND  → "open chrome", "press control c", "spanish", "pro mode"...
    DICTATION→ types what you say, spoken punctuation included
    LETTER   → spell letter by letter, letters glued together
    """

    def __init__(self, gestures: "GestureEngine | None" = None):
        super().__init__(daemon=True, name="aura-voice")
        self.enabled = True
        self.running = True
        self.mode = MODE_COMMAND
        self.gestures = gestures
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = CONFIG["ENERGY_THRESHOLD"]
        self.recognizer.dynamic_energy_threshold = True
        self.last_heard = "—"
        self._commands = self._build_commands()
        self._all_phrases = [p for phrases in self._commands for p in phrases]

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
        log(f"voice online — language {CONFIG['LANGUAGE']}")
        VOICE.say("Aura online")

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

    # ── live settings: language + difficulty mode + air keyboard ──────────
    def _settings(self, text: str) -> bool:
        t = text.strip()
        # language: "spanish" / "speak spanish" / "habla español" / "idioma español"
        probe = t
        for prefix in ("speak ", "language ", "habla ", "idioma ", "parla "):
            if probe.startswith(prefix):
                probe = probe[len(prefix):]
        if probe in LANGS:
            CONFIG["LANGUAGE"] = LANGS[probe]
            Actions._did(f"language → {CONFIG['LANGUAGE']}", probe)
            return True
        # difficulty: "easy mode" / "modo fácil" ...
        for word, m in (("easy", "EASY"), ("fácil", "EASY"), ("facil", "EASY"),
                        ("normal", "NORMAL"),
                        ("pro", "PRO"), ("expert", "PRO"), ("experto", "PRO")):
            if t in (f"{word} mode", f"modo {word}", word + " gestures"):
                apply_mode(m)
                Actions._did(f"gesture mode → {m}", f"{m} mode")
                return True
        # air keyboard
        if t in ("keyboard", "air keyboard", "show keyboard", "open keyboard",
                 "teclado", "abre el teclado", "muestra el teclado"):
            if self.gestures:
                self.gestures.toggle_osk(True)
            return True
        if t in ("hide keyboard", "close keyboard", "cierra el teclado",
                 "esconde el teclado"):
            if self.gestures:
                self.gestures.toggle_osk(False)
            return True
        return False

    # ── COMMAND mode ───────────────────────────────────────────────────────
    def _build_commands(self) -> dict:
        return {
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
            ("scroll up", "sube"): lambda: Mouse.scroll(4),
            ("scroll down", "baja"): lambda: Mouse.scroll(-4),
            ("click", "left click", "haz clic"): pyautogui.click,
            ("right click", "clic derecho"): Mouse.right_click,
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

    def _command(self, text: str):
        if self._settings(text):
            return
        words = text.split()

        if words[0] in ("press", "pulsa", "presiona", "hold") and len(words) > 1:
            if Actions.press_combo(words[1:]):
                return

        for trigger in ("open ", "launch ", "start ", "abre ", "abrir "):
            if text.startswith(trigger):
                Actions.open_app(text[len(trigger):])
                return

        for trigger in ("search for ", "search ", "google ", "busca ", "buscar "):
            if text.startswith(trigger) and len(text) > len(trigger):
                Actions.web_search(text[len(trigger):])
                return

        for trigger in ("type ", "write ", "escribe "):
            if text.startswith(trigger):
                Actions.type_text(text[len(trigger):])
                return

        # exact / substring match
        for phrases, action in self._commands.items():
            if any(p in text for p in phrases):
                action()
                Actions.last_command = phrases[0]
                beep(True)
                return

        # 🧠 smart fuzzy match — "closed window pls" still hits "close window"
        cutoff = CONFIG["FUZZY_MATCH"]
        if cutoff:
            close = difflib.get_close_matches(text, self._all_phrases, n=1,
                                              cutoff=cutoff)
            if close:
                phrase = close[0]
                for phrases, action in self._commands.items():
                    if phrase in phrases:
                        action()
                        Actions.last_command = f"{phrase} (~)"
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
                out += symbol
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
            if two in PUNCTUATION:
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
                out += tok[0]
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
#  AIR KEYBOARD — a keyboard floating on the camera. Hover with your index
#  finger, touch index+middle together (or pinch) to press. ⌨️✨
# ════════════════════════════════════════════════════════════════════════════

class AirKeyboard:
    ROWS = [
        list("1234567890"),
        list("qwertyuiop"),
        list("asdfghjkl"),
        list("zxcvbnm") + ["←"],
        ["SHIFT", "SPACE", "ENTER", "X"],
    ]

    def __init__(self, frame_w: int, frame_h: int):
        self.shift = False
        self.pressed_at = 0.0
        self.flash_key = None
        self.flash_until = 0.0
        self.keys: list[tuple[str, int, int, int, int]] = []   # (label,x,y,w,h)
        kb_top = int(frame_h * 0.28)
        kb_h = int(frame_h * 0.62)
        row_h = kb_h // len(self.ROWS)
        for r, row in enumerate(self.ROWS):
            kw = frame_w // (len(row) + 1)
            total = kw * len(row)
            x0 = (frame_w - total) // 2
            for c, label in enumerate(row):
                self.keys.append((label, x0 + c * kw + 3,
                                  kb_top + r * row_h + 3, kw - 6, row_h - 6))

    def hovered(self, px: int, py: int):
        for key in self.keys:
            label, x, y, w, h = key
            if x <= px <= x + w and y <= py <= y + h:
                return key
        return None

    def press(self, label: str):
        now = time.time()
        if now - self.pressed_at < 0.45:        # per-key cooldown
            return
        self.pressed_at = now
        self.flash_key, self.flash_until = label, now + 0.25
        beep(True)
        if label == "SHIFT":
            self.shift = not self.shift
            return
        if label == "SPACE":
            do(lambda: pyautogui.press("space"))
        elif label == "ENTER":
            do(lambda: pyautogui.press("enter"))
        elif label == "←":
            do(lambda: pyautogui.press("backspace"))
        elif label == "X":
            pass                                 # handled by GestureEngine
        else:
            char = label.upper() if self.shift else label
            do(lambda: kb.write(char))
            Actions.last_command = f"⌨ {char}"

    def draw(self, frame, hover):
        now = time.time()
        overlay = frame.copy()
        for label, x, y, w, h in self.keys:
            is_hover = hover is not None and hover[0] == label
            is_flash = label == self.flash_key and now < self.flash_until
            if is_flash:
                color, fill = (90, 255, 120), -1
            elif is_hover:
                color, fill = (80, 220, 255), -1
            elif label == "SHIFT" and self.shift:
                color, fill = (200, 160, 60), -1
            else:
                color, fill = (45, 40, 35), -1
            cv2.rectangle(overlay, (x, y), (x + w, y + h), color, fill)
            cv2.rectangle(overlay, (x, y), (x + w, y + h), (120, 120, 120), 1)
            text = label.upper() if (self.shift and len(label) == 1) else label
            tcol = (10, 10, 10) if (is_hover or is_flash) else (230, 230, 230)
            scale = 0.7 if len(label) == 1 else 0.5
            size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 2)[0]
            cv2.putText(overlay, text, (x + (w - size[0]) // 2,
                        y + (h + size[1]) // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, scale, tcol, 2)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)


# ════════════════════════════════════════════════════════════════════════════
#  GESTURE ENGINE — hand → mouse + actions (stabilized, no ghost gestures)
# ════════════════════════════════════════════════════════════════════════════

WRIST, THUMB_TIP, THUMB_IP = 0, 4, 3
INDEX_TIP, INDEX_PIP, INDEX_MCP = 8, 6, 5
MIDDLE_TIP, MIDDLE_PIP, MIDDLE_MCP = 12, 10, 9
RING_TIP, RING_PIP = 16, 14
PINKY_TIP, PINKY_PIP = 20, 18


class GestureEngine:
    """Webcam loop. A gesture only fires after it's been seen for
    STABLE_FRAMES consecutive frames — twitchy hands can't ghost-trigger
    anything anymore. All slow actions go through the Worker thread, and the
    mouse uses the native Windows API, so the camera NEVER freezes."""

    def __init__(self, show_preview: bool = True):
        self.enabled = True
        self.running = True
        self.paused = False
        self.show_preview = show_preview
        self.gesture_name = "—"
        self.osk: AirKeyboard | None = None
        self.osk_on = False
        self.frame_w = CONFIG["FRAME_WIDTH"]
        self.frame_h = CONFIG["FRAME_HEIGHT"]

        self.prev_x, self.prev_y = SCREEN_W / 2, SCREEN_H / 2
        self.last_click = 0.0
        self.last_action = 0.0
        self.hold_since = 0.0
        self.pinching = False
        self.mid_pinching = False
        self.dragging = False
        self.scroll_anchor = None
        self.swipe_anchor = None
        self.prev_frame_time = 0.0

        # stability: a label must repeat before it becomes active
        self.label_history: deque = deque(maxlen=12)
        self.active_label = "none"

        self.hands = mp.solutions.hands.Hands(
            max_num_hands=1,
            model_complexity=0,
            min_detection_confidence=CONFIG["DETECTION_CONFIDENCE"],
            min_tracking_confidence=CONFIG["TRACKING_CONFIDENCE"],
        )
        self.drawer = mp.solutions.drawing_utils
        self.styles = mp.solutions.drawing_styles

    def toggle_osk(self, on: bool | None = None):
        self.osk_on = (not self.osk_on) if on is None else on
        if self.osk_on and self.osk is None:
            self.osk = AirKeyboard(self.frame_w, self.frame_h)
        Actions._did(f"air keyboard {'ON' if self.osk_on else 'OFF'}",
                     "Keyboard on" if self.osk_on else "Keyboard off")

    # ── hand geometry ──────────────────────────────────────────────────────
    @staticmethod
    def _dist(a, b) -> float:
        return math.hypot(a.x - b.x, a.y - b.y)

    def _hand_size(self, lm) -> float:
        return self._dist(lm[WRIST], lm[MIDDLE_MCP]) + 1e-6

    def _fingers_up(self, lm) -> list[bool]:
        size = self._hand_size(lm)
        thumb = self._dist(lm[THUMB_TIP], lm[PINKY_PIP]) / size > 0.95
        fingers = [thumb]
        for tip, pip in ((INDEX_TIP, INDEX_PIP), (MIDDLE_TIP, MIDDLE_PIP),
                         (RING_TIP, RING_PIP), (PINKY_TIP, PINKY_PIP)):
            fingers.append(lm[tip].y < lm[pip].y)
        return fingers

    def _pinch_ratio(self, lm, finger_tip: int) -> float:
        return self._dist(lm[THUMB_TIP], lm[finger_tip]) / self._hand_size(lm)

    # ── classify the hand into ONE label per frame ─────────────────────────
    def _classify(self, lm) -> str:
        thumb, index, middle, ring, pinky = self._fingers_up(lm)
        n = thumb + index + middle + ring + pinky
        if n == 5:
            return "palm"
        if n == 0:
            return "fist"
        if thumb and n == 1:
            return "thumb_up" if lm[THUMB_TIP].y < lm[WRIST].y else "thumb_down"
        if pinky and not index and not middle and not ring:
            return "pinky"
        if index and middle and ring and not pinky:
            return "three"
        if index and middle and not ring and not pinky:
            return "two"
        if index and not middle and not ring and not pinky:
            return "cursor"
        return "none"

    def _stable(self, label: str) -> str:
        """Return the active label; only switch after STABLE_FRAMES repeats."""
        self.label_history.append(label)
        need = CONFIG["STABLE_FRAMES"]
        if label != self.active_label:
            recent = list(self.label_history)[-need:]
            if len(recent) == need and all(l == label for l in recent):
                self.active_label = label
                self.hold_since = 0.0          # restart hold timers on change
                self.scroll_anchor = None
                self.swipe_anchor = None
        return self.active_label

    # ── per-frame logic ────────────────────────────────────────────────────
    def _process_hand(self, lm, now: float):
        raw = self._classify(lm)
        label = self._stable(raw)
        cooldown_ok = now - self.last_action > CONFIG["ACTION_COOLDOWN"]

        # air keyboard hijacks the hand while it's on
        if self.osk_on and self.osk:
            self._process_osk(lm, now, label)
            return

        if label == "palm":
            held = now - self.hold_since if self.hold_since else 0.0
            self.gesture_name = "open palm 🖐️"
            if self.hold_since == 0.0:
                self.hold_since = now
            elif held > CONFIG["PALM_HOLD_TIME"] and cooldown_ok:
                self.paused = not self.paused
                self.last_action = now
                self.hold_since = 0.0
                Actions._did("gestures PAUSED" if self.paused else "gestures RESUMED",
                             "Paused" if self.paused else "Resumed")
            self._end_drag()
            return

        if self.paused:
            self.gesture_name = "paused (palm 🖐️ to resume)"
            return

        if label == "fist" and allowed("fist"):
            held = now - self.hold_since if self.hold_since else 0.0
            remaining = CONFIG["FIST_HOLD_TIME"] - held
            self.gesture_name = f"fist ✊ close in {max(remaining, 0):.1f}s"
            if self.hold_since == 0.0:
                self.hold_since = now
            elif held > CONFIG["FIST_HOLD_TIME"] and cooldown_ok:
                do(Actions.close_window)
                self.last_action = now
                self.hold_since = 0.0
            self._end_drag()
            return

        if label in ("thumb_up", "thumb_down") and allowed("thumbs"):
            self.gesture_name = "thumbs 👍" if label == "thumb_up" else "thumbs 👎"
            if cooldown_ok:
                d = "up" if label == "thumb_up" else "down"
                do(lambda: Actions.volume(d))
                self.last_action = now
            return

        if label == "pinky" and allowed("pinky"):
            self.gesture_name = "pinky 🤙 minimize"
            if cooldown_ok:
                do(Actions.minimize_window)
                self.last_action = now
            return

        if label == "three" and allowed("swipe"):
            self.gesture_name = "three 🤟 swipe ←/→ desktop"
            x = lm[INDEX_TIP].x
            if self.swipe_anchor is None:
                self.swipe_anchor = (x, now)
            else:
                x0, t0 = self.swipe_anchor
                dt = now - t0
                if dt > 0.04:
                    speed = (x - x0) / dt
                    if abs(speed) > CONFIG["SWIPE_SPEED"] and cooldown_ok:
                        d = "right" if speed > 0 else "left"
                        do(lambda: Actions.desktop(d))
                        self.last_action = now
                        self.swipe_anchor = None
                    else:
                        self.swipe_anchor = (x, now)
            return

        if label == "two":
            # middle-finger pinch = right click, otherwise scroll
            if allowed("rightclick"):
                mid = self._pinch_ratio(lm, MIDDLE_TIP)
                if not self.mid_pinching and mid < CONFIG["PINCH_ON"]:
                    self.mid_pinching = True
                    if now - self.last_click > CONFIG["CLICK_COOLDOWN"]:
                        Mouse.right_click()
                        self.last_click = now
                        Actions.last_command = "right click"
                        beep(True)
                    self.gesture_name = "right click 🤌"
                    return
                if self.mid_pinching and mid > CONFIG["PINCH_OFF"]:
                    self.mid_pinching = False
            if allowed("scroll"):
                self.gesture_name = "scroll ✌️"
                y = lm[INDEX_TIP].y
                if self.scroll_anchor is None:
                    self.scroll_anchor = y
                else:
                    delta = self.scroll_anchor - y
                    step = CONFIG["SCROLL_STEP"]
                    if abs(delta) > step:
                        Mouse.scroll(int(delta / step))
                        self.scroll_anchor = y
            self._end_drag()
            return

        if label == "cursor" and allowed("cursor"):
            self._move_cursor(lm)
            if allowed("click"):
                ratio = self._pinch_ratio(lm, INDEX_TIP)
                if not self.pinching and ratio < CONFIG["PINCH_ON"]:
                    self.pinching = True
                    if now - self.last_click > CONFIG["CLICK_COOLDOWN"]:
                        Mouse.down()
                        self.dragging = True
                        self.last_click = now
                        Actions.last_command = "click / drag"
                        beep(True)
                elif self.pinching and ratio > CONFIG["PINCH_OFF"]:
                    self.pinching = False
                    self._end_drag()
            self.gesture_name = "pinch 🤏 hold=drag" if self.pinching else "cursor ☝️"
            return

        self.gesture_name = "—"
        self._end_drag()

    # ── air keyboard frame logic ───────────────────────────────────────────
    def _process_osk(self, lm, now: float, label: str):
        if label == "palm":   # palm still pauses/exits keyboard
            self.gesture_name = "palm 🖐️ (hold to close keyboard)"
            if self.hold_since == 0.0:
                self.hold_since = now
            elif now - self.hold_since > CONFIG["PALM_HOLD_TIME"]:
                self.toggle_osk(False)
                self.hold_since = 0.0
            return
        self.hold_since = 0.0
        px = int(lm[INDEX_TIP].x * self.frame_w)
        py = int(lm[INDEX_TIP].y * self.frame_h)
        self._osk_hover = (px, py)
        hover = self.osk.hovered(px, py)
        # press = index+middle tips touching OR thumb pinch — your choice
        size = self._hand_size(lm)
        two_finger = self._dist(lm[INDEX_TIP], lm[MIDDLE_TIP]) / size < 0.30
        pinch = self._pinch_ratio(lm, INDEX_TIP) < CONFIG["PINCH_ON"]
        pressing = two_finger or pinch
        self.gesture_name = f"⌨️ air keyboard {'PRESS' if pressing else 'hover'}"
        if hover and pressing:
            if hover[0] == "X":
                self.toggle_osk(False)
            else:
                self.osk.press(hover[0])
        self._osk_current_hover = hover

    def _move_cursor(self, lm):
        m = CONFIG["CONTROL_MARGIN"]
        x = np.interp(lm[INDEX_TIP].x, (m, 1 - m), (0, SCREEN_W))
        y = np.interp(lm[INDEX_TIP].y, (m, 1 - m), (0, SCREEN_H))
        s = CONFIG["SMOOTHING"]
        self.prev_x += (x - self.prev_x) * s
        self.prev_y += (y - self.prev_y) * s
        Mouse.move(self.prev_x, self.prev_y)

    def _end_drag(self):
        self.pinching = False
        if self.dragging:
            Mouse.up()
            self.dragging = False

    # ── HUD ────────────────────────────────────────────────────────────────
    def _draw_hud(self, frame, voice: "VoiceEngine | None", fps: float):
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (0, 0), (w, 78), (20, 16, 12), -1)
        cv2.putText(frame, "A U R A", (16, 32),
                    cv2.FONT_HERSHEY_DUPLEX, 0.9, (80, 220, 255), 2)
        status = "PAUSED" if self.paused else ("ON" if self.enabled else "OFF")
        cv2.putText(frame,
                    f"{CONFIG['MODE']}  |  {CONFIG['LANGUAGE']}  |  "
                    f"gestures {status}  |  {fps:.0f} fps",
                    (16, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
        cv2.putText(frame, f"{self.gesture_name}", (300, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.62, (120, 255, 120), 2)
        vmode = voice.mode if voice and voice.enabled else "voice off"
        cv2.putText(frame, f"voice: {vmode}", (300, 62),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 200, 90), 1)
        cv2.rectangle(frame, (0, h - 52), (w, h), (20, 16, 12), -1)
        cv2.putText(frame, f"last: {Actions.last_command}", (16, h - 31),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 255), 1)
        cv2.putText(frame,
                    "[K]eyboard  [M]ode  [L]anguage  [P]ause  [Q]uit",
                    (16, h - 9), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (140, 140, 140), 1)
        if self.osk_on and self.osk:
            hover = getattr(self, "_osk_current_hover", None)
            self.osk.draw(frame, hover)
            tip = getattr(self, "_osk_hover", None)
            if tip:
                cv2.circle(frame, tip, 10, (80, 220, 255), 2)
        else:
            m = CONFIG["CONTROL_MARGIN"]
            cv2.rectangle(frame, (int(w * m), int(h * m)),
                          (int(w * (1 - m)), int(h * (1 - m))), (60, 60, 90), 1)

    def _handle_key(self, key: int, voice: "VoiceEngine | None"):
        if key == ord("q"):
            self.running = False
        elif key == ord("k"):
            self.toggle_osk()
        elif key == ord("p"):
            self.paused = not self.paused
            Actions._did("gestures PAUSED" if self.paused else "gestures RESUMED")
        elif key == ord("m"):
            order = ["EASY", "NORMAL", "PRO"]
            nxt = order[(order.index(CONFIG["MODE"]) + 1) % 3]
            apply_mode(nxt)
            Actions._did(f"gesture mode → {nxt}", f"{nxt} mode")
        elif key == ord("l"):
            cur = CONFIG["LANGUAGE"]
            nxt = LANG_CYCLE[(LANG_CYCLE.index(cur) + 1) % len(LANG_CYCLE)] \
                if cur in LANG_CYCLE else LANG_CYCLE[0]
            CONFIG["LANGUAGE"] = nxt
            Actions._did(f"language → {nxt}")

    # ── main loop ──────────────────────────────────────────────────────────
    def run(self, voice: "VoiceEngine | None" = None):
        cap = cv2.VideoCapture(CONFIG["CAMERA_INDEX"], cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, CONFIG["FRAME_WIDTH"])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CONFIG["FRAME_HEIGHT"])
        if not cap.isOpened():
            log("no camera found — gesture control disabled (voice still works)")
            self.enabled = False
            while self.running:
                time.sleep(0.5)
            return

        self.frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or self.frame_w
        self.frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or self.frame_h
        log("camera online — show me your hand!")
        VOICE.say("Aura gestures online")

        while self.running:
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.05)
                continue
            frame = cv2.flip(frame, 1)
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
                    self.label_history.clear()
                    self.active_label = "none"
                    self.hold_since = 0.0
                    self.swipe_anchor = self.scroll_anchor = None
                    self._osk_current_hover = None
                    self._end_drag()

            if self.show_preview:
                fps = 1.0 / max(now - self.prev_frame_time, 1e-6)
                self.prev_frame_time = now
                self._draw_hud(frame, voice, fps)
                cv2.imshow("AURA", frame)
                key = cv2.waitKey(1) & 0xFF
                if key != 255:
                    self._handle_key(key, voice)
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
    checks.append(("native mouse API", "OK" if Mouse._u32 else "fallback: pyautogui"))
    checks.append(("SpeechRecognition", sr.__version__))
    _ = sr.Recognizer()
    checks.append(("Recognizer", "builds OK"))
    checks.append(("keyboard", "imported OK"))
    try:
        engine = pyttsx3.init()
        del engine
        checks.append(("pyttsx3 TTS", "init OK"))
    except Exception as e:
        checks.append(("pyttsx3 TTS", f"warning: {e}"))
    _ = AirKeyboard(960, 540)
    checks.append(("AirKeyboard", f"{len(_.keys)} keys OK"))
    _ = GestureEngine.__new__(GestureEngine)
    checks.append(("GestureEngine", "class OK"))
    _ = VoiceEngine()
    checks.append(("VoiceEngine", "builds OK"))
    checks.append(("modes", " / ".join(MODES)))
    checks.append(("languages", " ".join(LANG_CYCLE)))
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
    parser.add_argument("--mode", default=None, choices=["easy", "normal", "pro"],
                        help="gesture difficulty preset")
    parser.add_argument("--camera", type=int, default=None, help="camera index")
    parser.add_argument("--quiet", action="store_true", help="no TTS voice feedback")
    parser.add_argument("--self-test", action="store_true", help="verify install & exit")
    args = parser.parse_args()

    if args.lang:
        CONFIG["LANGUAGE"] = args.lang
    if args.mode:
        apply_mode(args.mode)
    if args.camera is not None:
        CONFIG["CAMERA_INDEX"] = args.camera
    if args.quiet:
        CONFIG["VOICE_FEEDBACK"] = False
        VOICE.enabled = False

    if args.self_test:
        return self_test()

    print(__doc__.split("ONE FILE")[0])
    log(f"screen {SCREEN_W}x{SCREEN_H} | mode {CONFIG['MODE']} | "
        f"language {CONFIG['LANGUAGE']}")
    log("window keys: K keyboard · M mode · L language · P pause · Q quit")
    log("hotkeys: Ctrl+Alt+G gestures · Ctrl+Alt+V voice · Ctrl+Alt+Q quit")

    gestures = GestureEngine(show_preview=not args.no_preview)
    if args.no_camera:
        gestures.enabled = False

    voice = None
    if not args.no_voice:
        voice = VoiceEngine(gestures)
        voice.start()

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
            gestures.run(voice)
    except KeyboardInterrupt:
        pass
    finally:
        if voice:
            voice.running = False
    log("bye! 👋")
    return 0


if __name__ == "__main__":
    sys.exit(main())
