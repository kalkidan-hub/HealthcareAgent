from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

from google import genai

_GEMINI_CLIENT = None


def _configure_client() -> None:
    global _GEMINI_CLIENT
    if _GEMINI_CLIENT is not None:
        return

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set. Add it to .env or export it before starting the app.")

    _GEMINI_CLIENT = genai.Client(api_key=api_key)


def ask_gemini(prompt: str, *, model_name: str = "gemini-2.5-flash"):
    _configure_client()
    return _GEMINI_CLIENT.models.generate_content(model=model_name, contents=prompt)