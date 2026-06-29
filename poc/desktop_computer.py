"""Computer impl untuk DESKTOP Windows (bukan browser).

Ganti Playwright dengan kontrol OS-level:
- screenshot layar penuh via pyautogui
- mouse/keyboard via pyautogui

EKSPERIMEN. Gemini computer-use di-optimize buat browser, BUKAN desktop native.
Akurasi bisa turun. Ini buat buktiin konsep desktop control lokal Windows.

Method browser-only (open_web_browser, navigate, search, go_back/forward)
di-no-op -> cuma return state sekarang. Di orchestrator, fungsi-fungsi itu
juga di-exclude dari tool model lewat excluded_predefined_functions.
"""
import io
import time
from typing import Literal

import pyautogui

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "computer-use-preview"))
from computers.computer import Computer, EnvState

# Safety: geser mouse ke pojok kiri-atas buat abort darurat.
pyautogui.FAILSAFE = True
# Jeda kecil tiap aksi biar UI sempat reaksi.
pyautogui.PAUSE = 0.3

# Map nama key dari model -> nama key pyautogui.
KEY_MAP = {
    "return": "enter",
    "control": "ctrl",
    "super": "win",
    "windows": "win",
    "meta": "win",
    "escape": "esc",
    "pageup": "pageup",
    "pagedown": "pagedown",
}


def _map_key(k: str) -> str:
    k = k.strip().lower()
    return KEY_MAP.get(k, k)


class DesktopComputer(Computer):
    """Kontrol desktop Windows lokal pakai pyautogui."""

    def __init__(
        self,
        screen_size: tuple[int, int] | None = None,
        window_title: str | None = None,
    ):
        # Kalau window_title diisi -> screenshot & koordinat DIBATASI ke window
        # itu doang (model ga liat layar lain, grounding lebih akurat).
        # Kalau None -> full screen.
        self._window_title = window_title
        self._offset = (0, 0)  # (left, top) window di layar
        self._screen_size = screen_size or tuple(pyautogui.size())
        if window_title:
            self._refresh_region()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    # --- region (window-scoped) -----------------------------------------
    def _refresh_region(self):
        """Update offset + size dari posisi window app saat ini."""
        try:
            import pygetwindow as gw
            wins = gw.getWindowsWithTitle(self._window_title)
            if wins:
                w = wins[0]
                self._offset = (w.left, w.top)
                self._screen_size = (w.width, w.height)
        except Exception as e:
            print(f"[REGION] gagal baca window: {e}")

    def _abs(self, x: int, y: int) -> tuple[int, int]:
        """Koordinat relatif-window -> absolut layar (tambah offset)."""
        return x + self._offset[0], y + self._offset[1]

    # --- state ----------------------------------------------------------
    def _shot(self) -> EnvState:
        if self._window_title:
            self._refresh_region()
            left, top = self._offset
            w, h = self._screen_size
            img = pyautogui.screenshot(region=(left, top, w, h))
        else:
            img = pyautogui.screenshot()
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return EnvState(screenshot=buf.getvalue(), url="desktop")

    def current_state(self) -> EnvState:
        return self._shot()

    def screen_size(self) -> tuple[int, int]:
        return self._screen_size

    # --- aksi desktop ---------------------------------------------------
    def click_at(self, x: int, y: int) -> EnvState:
        ax, ay = self._abs(x, y)
        pyautogui.click(x=ax, y=ay)
        return self._shot()

    def hover_at(self, x: int, y: int) -> EnvState:
        ax, ay = self._abs(x, y)
        pyautogui.moveTo(ax, ay)
        return self._shot()

    def type_text_at(
        self,
        x: int,
        y: int,
        text: str,
        press_enter: bool,
        clear_before_typing: bool,
    ) -> EnvState:
        ax, ay = self._abs(x, y)
        pyautogui.click(x=ax, y=ay)
        if clear_before_typing:
            pyautogui.hotkey("ctrl", "a")
            pyautogui.press("delete")
        pyautogui.write(text, interval=0.02)
        if press_enter:
            pyautogui.press("enter")
        return self._shot()

    def key_combination(self, keys: list[str]) -> EnvState:
        mapped = [_map_key(k) for k in keys]
        if len(mapped) == 1:
            pyautogui.press(mapped[0])
        else:
            pyautogui.hotkey(*mapped)
        return self._shot()

    def scroll_document(
        self, direction: Literal["up", "down", "left", "right"]
    ) -> EnvState:
        amount = 800 if direction in ("up", "right") else -800
        if direction in ("up", "down"):
            pyautogui.scroll(amount)
        else:
            pyautogui.hscroll(amount)
        return self._shot()

    def scroll_at(
        self,
        x: int,
        y: int,
        direction: Literal["up", "down", "left", "right"],
        magnitude: int,
    ) -> EnvState:
        ax, ay = self._abs(x, y)
        pyautogui.moveTo(ax, ay)
        amount = magnitude if direction in ("up", "right") else -magnitude
        if direction in ("up", "down"):
            pyautogui.scroll(amount)
        else:
            pyautogui.hscroll(amount)
        return self._shot()

    def drag_and_drop(
        self, x: int, y: int, destination_x: int, destination_y: int
    ) -> EnvState:
        ax, ay = self._abs(x, y)
        adx, ady = self._abs(destination_x, destination_y)
        pyautogui.moveTo(ax, ay)
        pyautogui.dragTo(adx, ady, duration=0.5, button="left")
        return self._shot()

    def wait_5_seconds(self) -> EnvState:
        time.sleep(5)
        return self._shot()

    # --- browser-only: no-op buat desktop -------------------------------
    def open_web_browser(self) -> EnvState:
        return self._shot()

    def navigate(self, url: str) -> EnvState:
        return self._shot()

    def search(self) -> EnvState:
        return self._shot()

    def go_back(self) -> EnvState:
        return self._shot()

    def go_forward(self) -> EnvState:
        return self._shot()
