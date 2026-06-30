"""Orchestrator DESKTOP (eksperimen) — task: buka Microsoft Paint.

Pakai DesktopComputer (pyautogui) ganti Playwright. Gemini computer-use cuma
punya ENVIRONMENT_BROWSER (belum ada desktop env), jadi:
- environment tetap ENVIRONMENT_BROWSER
- fungsi navigasi browser di-exclude (navigate/search/go_back/go_forward)
- open_web_browser dipakai ulang sbg "ambil screenshot desktop awal"

PERINGATAN: ini ngendaliin mouse/keyboard ASLI laptop. Geser mouse ke pojok
kiri-atas buat abort darurat (pyautogui FAILSAFE).
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
from llm_client import DEFAULT_MODEL
from desktop_computer import DesktopComputer

# --- Screenshot capture (dump tiap _shot ke disk) ------------------------
SHOTS_ROOT = Path(__file__).parent / "shots" / "desktop_form"
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

MODEL = DEFAULT_MODEL

WINDOW_TITLE = "Sample Form App"

TASK = """You are controlling a Windows desktop application that is ALREADY OPEN
and focused on a form page titled "Form Data Diri". Do NOT open any other app,
do NOT use the Start menu, do NOT touch the taskbar. Work only inside this window.

First call open_web_browser to capture the current screenshot of the app.

Goal: Fill in the 6 form fields, then click Submit.

Fill these values:
- Nama Lengkap : Budi Santoso
- Tempat Tinggal : Jakarta Selatan
- Tanggal Lahir : 17-08-1990
- Email : budi.santoso@example.com
- Nomor Telepon : 081234567890
- Pekerjaan : Software Engineer

Steps:
1. Click the input field next to a label, then type the matching value
2. Repeat for all 6 fields
3. Click the Submit button
4. Confirm by describing the status message shown after submit"""


def _focus_window():
    """Bawa window app ke depan biar klik/ketik ga nyasar ke window lain."""
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
                  f"Pastikan sample_app.py sudah jalan di halaman Form.")
    except Exception as e:
        print(f"[FOCUS] gagal activate window: {e}")


def main():
    print(f"\n{'='*60}")
    print(f"  Desktop CUA — target window: {WINDOW_TITLE}")
    print(f"  Model: {MODEL}")
    print(f"{'='*60}")
    print(f"\n[QUERY]\n{TASK}\n")
    print(f"{'='*60}\n")

    # Countdown biar kamu sempat lepas tangan dari mouse/keyboard.
    print("CUA mulai dalam 3 detik. Jangan sentuh mouse/keyboard.")
    time.sleep(3)
    _focus_window()
    time.sleep(1)  # kasih waktu window naik ke depan sebelum aksi pertama

    # Exclude fungsi navigasi browser; sisanya (click/type/key/scroll/drag) generik.
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

    # window_title -> CUA cuma liat window app ini, koordinat relatif ke window.
    with DesktopComputer(window_title=WINDOW_TITLE) as computer:
        agent = BrowserAgent(
            browser_computer=computer,
            query=TASK,
            model_name=MODEL,
        )
        # Override config default (browser) dengan config desktop.
        agent._generate_content_config = config
        agent.agent_loop()

    result = getattr(agent, "final_reasoning", "No final message")
    print(f"\n[RESULT] {result}\n")
    print(f"[CAPTURE] {_capture['step']} screenshot -> {SHOTS_ROOT}\n")


if __name__ == "__main__":
    main()
