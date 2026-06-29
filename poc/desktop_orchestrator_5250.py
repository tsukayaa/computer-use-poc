"""Orchestrator buat sample_app_5250.py — tes CUA di UI gaya 5250 keyboard-driven.

App harus SUDAH kebuka + SUDAH sign-on, di layar "Financial Underwriting".
CUA isi field pakai navigasi keyboard (Tab antar field) lalu Enter submit.

DUMMY data, ga ada PII. Abort darurat: mouse ke pojok kiri-atas.
"""
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / "computer-use-preview" / ".env")

sys.path.insert(0, str(Path(__file__).parent.parent / "computer-use-preview"))

from google.genai import types
from agent import BrowserAgent
from desktop_computer import DesktopComputer

# --- Screenshot capture --------------------------------------------------
SHOTS_ROOT = Path(__file__).parent / "shots" / "desktop_5250"
_capture = {"step": 0}

_orig_shot = DesktopComputer._shot

def _capturing_shot(self):
    state = _orig_shot(self)
    _capture["step"] += 1
    SHOTS_ROOT.mkdir(parents=True, exist_ok=True)
    (SHOTS_ROOT / f"step_{_capture['step']:04d}.png").write_bytes(state.screenshot)
    return state

DesktopComputer._shot = _capturing_shot
# -------------------------------------------------------------------------

MODEL = "gemini-2.5-computer-use-preview-10-2025"
WINDOW_TITLE = "B - 5250 Display"

TASK = """You are controlling a green-screen terminal application (IBM 5250 style)
that is ALREADY OPEN and signed on, currently showing the "Main Menu".
This is a KEYBOARD-ONLY application: THE MOUSE DOES NOT WORK. Clicking does
nothing. You MUST use the keyboard for everything.
Do NOT open any other app, do NOT use the Start menu or taskbar. Work only in
this window.

First call open_web_browser to capture the current screenshot of the app.

Keyboard you can use (via key_combination):
- "tab" / "shift+tab" : move to next / previous field
- "down" / "up"       : move between fields
- "enter"             : submit / confirm a screen
- Type text with type_text_at (it will type into the currently focused field;
  the click part has no effect because the mouse is disabled, so make sure the
  correct field is focused first using tab/arrow keys).

Goal:
1. From the Main Menu, select option 1 ("Financial Underwriting by Contract"):
   type "1" then press Enter. This opens the underwriting screen.
2. On the underwriting screen, fill these fields (use tab/arrow keys to move
   focus, the first field is already focused):
   - Client Number : 51448776
   - Client Name   : SITI AMINAH
   - Currency      : IDR
   - Coverage Code : DTHS
   - Sum At Risk   : 2624000000
3. Press Enter to submit.
4. Confirm by describing the status line shown after submit (e.g. "Record saved").

Remember: navigate using the keyboard only. The mouse will not move focus."""


def _focus_window():
    try:
        import pygetwindow as gw
        wins = gw.getWindowsWithTitle(WINDOW_TITLE)
        if wins:
            w = wins[0]
            if w.isMinimized:
                w.restore()
            w.activate()
            print(f"[FOCUS] Window '{WINDOW_TITLE}' dibawa ke depan.")
        else:
            print(f"[FOCUS] WARNING: window '{WINDOW_TITLE}' tidak ditemukan. "
                  f"Pastikan sample_app_5250.py jalan & sudah sign-on.")
    except Exception as e:
        print(f"[FOCUS] gagal activate window: {e}")


def main():
    print(f"\n{'='*60}")
    print(f"  Desktop CUA (5250) — target window: {WINDOW_TITLE}")
    print(f"  Model: {MODEL}")
    print(f"{'='*60}")
    print(f"\n[QUERY]\n{TASK}\n")
    print(f"{'='*60}\n")

    print("CUA mulai dalam 3 detik. Jangan sentuh mouse/keyboard.")
    time.sleep(3)
    _focus_window()
    time.sleep(1)

    config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        top_k=40,
        max_output_tokens=8192,
        tools=[
            types.Tool(
                computer_use=types.ComputerUse(
                    environment=types.Environment.ENVIRONMENT_BROWSER,
                    excluded_predefined_functions=[
                        "navigate", "search", "go_back", "go_forward",
                    ],
                ),
            ),
        ],
        thinking_config=types.ThinkingConfig(include_thoughts=True),
    )

    with DesktopComputer(window_title=WINDOW_TITLE) as computer:
        agent = BrowserAgent(
            browser_computer=computer,
            query=TASK,
            model_name=MODEL,
        )
        agent._generate_content_config = config
        agent.agent_loop()

    result = getattr(agent, "final_reasoning", "No final message")
    print(f"\n[RESULT] {result}\n")
    print(f"[CAPTURE] {_capture['step']} screenshot -> {SHOTS_ROOT}\n")


if __name__ == "__main__":
    main()
