"""Judgment LLM (teks) lewat gateway Prudential -- SATU base URL.

Lapis JUDGMENT: baca SPAJ, ekstrak data, mutusin approve/refer, dll.

DULU: OpenAI-style /chat/completions = call HTTP terpisah.
SEKARANG: disatukan -> teks judgment juga lewat Gemini generateContent di
gateway yang SAMA dengan computer-use. Config base URL/header/model ada di
computer-use-preview/llm_client.py. Cuma 3 var: PRU_LLM_URL, PRU_API_KEY,
PRU_APP_ID (lihat llm_client.py).
"""
import asyncio
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

# Baca .env: cek poc/.env lalu computer-use-preview/.env.
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).parent.parent / "computer-use-preview" / ".env")

# llm_client tinggal di folder computer-use-preview.
sys.path.insert(0, str(Path(__file__).parent.parent / "computer-use-preview"))
from google.genai import types  # noqa: E402
from llm_client import DEFAULT_MODEL, build_client  # noqa: E402


def _split_messages(messages: list[dict[str, str]]) -> tuple[str | None, list[types.Content]]:
    """OpenAI-style messages -> (system_instruction, contents genai).

    role "system" -> system_instruction (digabung). "assistant" -> role "model".
    """
    system_parts: list[str] = []
    contents: list[types.Content] = []
    for m in messages:
        role = m.get("role", "user")
        text = m.get("content", "")
        if role == "system":
            system_parts.append(text)
            continue
        genai_role = "model" if role == "assistant" else "user"
        contents.append(types.Content(role=genai_role, parts=[types.Part(text=text)]))
    system = "\n".join(system_parts) if system_parts else None
    return system, contents


async def call_pru_llm(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float = 0.7,
    top_p: float = 1.0,
    max_tokens: int = 1024,
    timeout: float = 60.0,
    **extra: Any,
) -> types.GenerateContentResponse:
    """Hit gateway prugenai (Gemini generateContent). Return response genai.

    messages: [{"role": "user"/"system"/"assistant", "content": "..."}]
    """
    system, contents = _split_messages(messages)
    config = types.GenerateContentConfig(
        temperature=temperature,
        top_p=top_p,
        max_output_tokens=max_tokens,
        system_instruction=system,
        http_options=types.HttpOptions(timeout=int(timeout * 1000)),
        **extra,
    )
    client = build_client()
    # generate_content sync -> jalanin di thread biar ga blok event loop.
    return await asyncio.to_thread(
        client.models.generate_content,
        model=model or DEFAULT_MODEL,
        contents=contents,
        config=config,
    )


def extract_text(response: types.GenerateContentResponse) -> str:
    """Ambil teks dari response genai."""
    return getattr(response, "text", "") or ""


def call_pru_llm_sync(messages: list[dict[str, str]], **kwargs: Any) -> types.GenerateContentResponse:
    """Wrapper sync buat skrip non-async."""
    return asyncio.run(call_pru_llm(messages, **kwargs))


if __name__ == "__main__":
    # Smoke test: butuh LLM_BASE_URL + LLM_EXTRA_HEADERS di-set (lihat llm_client).
    msgs = [{"role": "user", "content": "Reply with exactly: OK"}]
    try:
        out = call_pru_llm_sync(msgs, max_tokens=10)
        print("RESPONSE:", extract_text(out))
    except Exception as e:
        print(f"FAILED: {e}")
