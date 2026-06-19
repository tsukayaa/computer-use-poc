import argparse
import csv
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / "computer-use-preview" / ".env")

# Headless dikontrol via env (GKE set "true"). Default false buat run lokal.
os.environ.setdefault("PLAYWRIGHT_HEADLESS", "false")

sys.path.insert(0, str(Path(__file__).parent.parent / "computer-use-preview"))

from agent import BrowserAgent
from computers import PlaywrightComputer
from computers.playwright import playwright as pw

import prelogin

# --- Screenshot capture ---------------------------------------------------
# Tiap step agent (current_state) ngehasilin PNG. Kita dump ke disk biar
# bisa diintip walau jalan headless di GKE. State capture per-run di sini.
SHOTS_ROOT = Path(__file__).parent / "shots"
_capture = {"dir": None, "step": 0}

_orig_current_state = pw.PlaywrightComputer.current_state

def _capturing_current_state(self):
    state = _orig_current_state(self)
    if _capture["dir"] is not None:
        _capture["step"] += 1
        fname = _capture["dir"] / f"step_{_capture['step']:04d}.png"
        fname.write_bytes(state.screenshot)
    return state

pw.PlaywrightComputer.current_state = _capturing_current_state
# -------------------------------------------------------------------------

SCREEN_SIZE = (1440, 900)
MODEL = "gemini-2.5-computer-use-preview-10-2025"
TARGET_URL = "https://www.saucedemo.com"
# URL halaman setelah login. Cookie session di-load lewat storage_state, tapi
# beberapa app (spt saucedemo) tetap tampilkan login di root -> buka URL ini
# langsung supaya agent mulai di halaman ter-autentikasi. Ganti untuk Prudential.
POST_LOGIN_URL = "https://www.saucedemo.com/inventory.html"


def build_task(user: dict) -> str:
    # NOTE: tidak ada password di prompt. Browser sudah login lewat prelogin
    # (storage_state). Agent mulai dari halaman setelah login.
    return f"""You are already logged in to the web application at {TARGET_URL}.

Steps:
1. Wait for the current page to fully load
2. Look at the page and describe what is on it: the main menu items, headings, and any visible content
3. Report what you see as confirmation that you are logged in"""


def run_user(user: dict, index: int):
    task = build_task(user)

    # Prelogin deterministik (Playwright murni): isi user+password, simpan
    # cookie ke auth.json. Password TIDAK pernah masuk ke prompt AI / Google.
    auth_path = prelogin.prelogin(user, index)

    # Folder capture per user: shots/user_1_standard_user/step_0001.png ...
    run_dir = SHOTS_ROOT / f"user_{index + 1}_{user['username']}"
    run_dir.mkdir(parents=True, exist_ok=True)
    _capture["dir"] = run_dir
    _capture["step"] = 0

    print(f"\n{'='*60}")
    print(f"  User {index + 1}")
    print(f"  Login: {user['username']}")
    print(f"  Capture: {run_dir}")
    print(f"{'='*60}")
    print(f"\n[QUERY]\n{task}\n")

    # storage_state=auth_path -> browser mulai sudah login.
    # initial_url=POST_LOGIN_URL -> agent mulai di halaman ter-autentikasi.
    computer = PlaywrightComputer(
        screen_size=SCREEN_SIZE,
        initial_url=POST_LOGIN_URL,
        storage_state=str(auth_path),
    )

    with computer as browser:
        agent = BrowserAgent(
            browser_computer=browser,
            query=task,
            model_name=MODEL,
        )
        agent.agent_loop()

    result = getattr(agent, "final_reasoning", "No final message")
    print(f"\n[RESULT] {result}\n")
    print(f"[CAPTURE] {_capture['step']} screenshot tersimpan di {run_dir}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", type=int, default=None,
                        help="Run only this user (1-indexed). Omit to run all.")
    args = parser.parse_args()

    csv_path = Path(__file__).parent / "users.csv"
    with open(csv_path, newline="", encoding="utf-8") as f:
        users = list(csv.DictReader(f))

    if args.user is not None:
        idx = args.user - 1
        if idx < 0 or idx >= len(users):
            print(f"Invalid --user {args.user}. Valid range: 1-{len(users)}.")
            sys.exit(1)
        targets = [(idx, users[idx])]
    else:
        targets = list(enumerate(users))

    print(f"SauceDemo Purchase POC")
    print(f"Running {len(targets)} user(s)\n")

    for i, (idx, user) in enumerate(targets):
        try:
            run_user(user, idx)
        except Exception as e:
            print(f"\n[User {idx + 1}] FAILED: {e}\n")

        if i < len(targets) - 1:
            print("Waiting 3s before next user...")
            time.sleep(3)

    print(f"\n{'='*60}")
    print(f"Done. {len(targets)} user(s) processed.")


if __name__ == "__main__":
    main()
