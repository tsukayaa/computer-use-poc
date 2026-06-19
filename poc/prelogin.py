"""Prelogin deterministik (Playwright murni, BUKAN AI).

Tujuan: login pakai username/password lalu simpan cookie/session ke auth.json.
Password cuma kepegang script lokal ini -- TIDAK PERNAH dikirim ke model AI /
server Google. Computer-use agent nanti load auth.json -> mulai dalam keadaan
sudah login, jadi agent tidak pernah lihat kredensial.

Cookie ada masa berlaku (TTL ditentukan server). Kalau auth.json expired,
jalankan ulang script ini buat refresh.

Selector di bawah untuk saucedemo.com (POC). Untuk app Prudential asli:
inspect element halaman login -> ganti USERNAME_SELECTOR / PASSWORD_SELECTOR /
LOGIN_BUTTON_SELECTOR / POST_LOGIN_SELECTOR.
"""
import argparse
import csv
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

TARGET_URL = "https://www.saucedemo.com"

# --- Selector spesifik aplikasi (ganti untuk Prudential) -----------------
USERNAME_SELECTOR = "#user-name"
PASSWORD_SELECTOR = "#password"
LOGIN_BUTTON_SELECTOR = "#login-button"
# Selector yang HANYA muncul setelah login sukses -> bukti login berhasil.
POST_LOGIN_SELECTOR = ".inventory_list"
# -------------------------------------------------------------------------

AUTH_DIR = Path(__file__).parent / "auth"


def prelogin(user: dict, index: int) -> Path:
    auth_path = AUTH_DIR / f"user_{index + 1}_{user['username']}.json"
    auth_path.parent.mkdir(parents=True, exist_ok=True)

    headless = os.environ.get("PLAYWRIGHT_HEADLESS", "false").lower() == "true"

    print(f"[PRELOGIN] User {index + 1}: {user['username']}")
    print(f"[PRELOGIN] Target: {TARGET_URL}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()

        page.goto(TARGET_URL)
        page.fill(USERNAME_SELECTOR, user["username"])
        page.fill(PASSWORD_SELECTOR, user["password"])
        page.click(LOGIN_BUTTON_SELECTOR)

        # Tunggu elemen post-login -> konfirmasi login sukses sebelum simpan cookie.
        page.wait_for_selector(POST_LOGIN_SELECTOR, timeout=15000)

        context.storage_state(path=str(auth_path))
        browser.close()

    print(f"[PRELOGIN] Sukses. Session disimpan -> {auth_path}")
    return auth_path


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

    for idx, user in targets:
        try:
            prelogin(user, idx)
        except Exception as e:
            print(f"[PRELOGIN] User {idx + 1} FAILED: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
