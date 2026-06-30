"""Konfig LLM terpusat -- SATU base URL buat SEMUA akses LLM di project ini.

Semua call LLM (computer-use NgendaliiN app + judgment teks) lewat gateway
internal Prudential ("prugenai") pakai Gemini native generateContent.

Kenapa generateContent (bukan /chat/completions, bukan Interactions API):
  - Computer-use (gemini-3.5-flash) HANYA jalan lewat generateContent.
  - /chat/completions OpenAI-style NOLAK tool computer_use.
  - Interactions API (baru) belum support computer_use.
  Ref: ai.google.dev/gemini-api/docs/generate-content/computer-use

CUKUP 3 VARIABEL (set di .env, JANGAN commit):
  PRU_LLM_URL   = base URL gateway prugenai (root, SEBELUM /v1beta).
                  genai nyusun: {PRU_LLM_URL}/v1beta/models/{model}:generateContent
  PRU_API_KEY   = nilai header x-api-key
  PRU_APP_ID    = nilai header app-id

Model GA perlu di-set: udah dipatok di sini (gemini-3.5-flash) + ditentuin
proxy Prudential. Kalau perlu ganti, ubah DEFAULT_MODEL di bawah.
"""
import os

from google import genai
from google.genai import types

# Model default seluruh project. gemini-3.5-flash = model computer-use
# (lihat docs) dan tetap bisa judgment teks biasa.
DEFAULT_MODEL = "gemini-3.5-flash"


def _http_options() -> types.HttpOptions | None:
    """Bangun HttpOptions dari env. None kalau PRU_LLM_URL ga di-set."""
    base_url = os.environ.get("PRU_LLM_URL")
    if not base_url:
        return None  # fallback: SDK nembak generativelanguage.googleapis.com langsung

    headers = {
        "x-api-key": os.environ.get("PRU_API_KEY", ""),
        "app-id": os.environ.get("PRU_APP_ID", ""),
    }
    return types.HttpOptions(base_url=base_url, headers=headers)


def build_client() -> genai.Client:
    """genai.Client yang nunjuk ke gateway prugenai (1 base URL)."""
    return genai.Client(
        api_key=os.environ.get("PRU_API_KEY") or os.environ.get("GEMINI_API_KEY"),
        http_options=_http_options(),
    )
