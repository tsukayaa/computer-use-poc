"""Client buat gateway LLM internal Prudential ("prugenai").

Endpoint OpenAI-style /chat/completions. Dipakai buat lapis JUDGMENT (teks):
baca SPAJ, ekstrak data, mutusin approve/refer, dll.

CATATAN PENTING: ini BUKAN buat nyetir computer-use (klik/ketik di app).
Computer-use butuh Gemini native (:generateContent + tool computer_use),
gateway /chat/completions OpenAI-style ga support itu. Lihat agent.py.

Env yang dibutuhkan:
  PRU_LLM_URL   = URL lengkap sampai /chat/completions
  PRU_API_KEY   = nilai header x-api-key
  PRU_APP_ID    = nilai header app-id

Butuh: pip install httpx
"""
import asyncio
import os
from typing import Any

import httpx

PRU_LLM_URL = os.environ.get("PRU_LLM_URL")
PRU_API_KEY = os.environ.get("PRU_API_KEY")
PRU_APP_ID = os.environ.get("PRU_APP_ID")


def _headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "x-api-key": PRU_API_KEY or "",
        "app-id": PRU_APP_ID or "",
    }


def _build_payload(
    messages: list[dict[str, str]],
    *,
    model: str | None,
    temperature: float,
    top_p: float,
    frequency_penalty: float,
    presence_penalty: float,
    max_tokens: int,
    stream: bool,
    extra: dict[str, Any],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
        "frequency_penalty": frequency_penalty,
        "presence_penalty": presence_penalty,
        "max_tokens": max_tokens,
        "stream": stream,
    }
    if model:
        payload["model"] = model
    payload.update(extra)
    return payload


async def call_pru_llm(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float = 0.7,
    top_p: float = 1.0,
    frequency_penalty: float = 0.0,
    presence_penalty: float = 0.0,
    max_tokens: int = 1024,
    stream: bool = False,
    timeout: float = 60.0,
    **extra: Any,
) -> dict[str, Any]:
    """Hit gateway prugenai (OpenAI-style). Return JSON response mentah.

    messages: [{"role": "user"/"system"/"assistant", "content": "..."}]
    extra: field payload tambahan (mis. seed, stop, dll).
    """
    if not PRU_LLM_URL:
        raise RuntimeError("PRU_LLM_URL belum di-set.")

    payload = _build_payload(
        messages,
        model=model,
        temperature=temperature,
        top_p=top_p,
        frequency_penalty=frequency_penalty,
        presence_penalty=presence_penalty,
        max_tokens=max_tokens,
        stream=stream,
        extra=extra,
    )

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(PRU_LLM_URL, headers=_headers(), json=payload)
        resp.raise_for_status()
        return resp.json()


def extract_text(response: dict[str, Any]) -> str:
    """Ambil teks dari response OpenAI-style: choices[0].message.content."""
    try:
        return response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return ""


def call_pru_llm_sync(messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
    """Wrapper sync buat skrip non-async."""
    return asyncio.run(call_pru_llm(messages, **kwargs))


if __name__ == "__main__":
    # Smoke test: butuh PRU_LLM_URL / PRU_API_KEY / PRU_APP_ID di-set.
    msgs = [{"role": "user", "content": "Reply with exactly: OK"}]
    try:
        out = call_pru_llm_sync(msgs, max_tokens=10)
        print("RESPONSE:", extract_text(out))
    except Exception as e:
        print(f"FAILED: {e}")
