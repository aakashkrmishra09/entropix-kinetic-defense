import io
import json
import os
from typing import Any, Dict, Optional, Tuple

from gtts import gTTS
import numpy as np
from openai import OpenAI

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv(
    "DEEPSEEK_BASE_URL", "https://deepseekv32-3ca9s.paas.ai.telus.com/v1"
)
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-ai/DeepSeek-V3.2-Exp")

GEMMA_API_KEY = os.getenv("GEMMA_API_KEY", "")
GEMMA_BASE_URL = os.getenv(
    "GEMMA_BASE_URL", "https://gemma-3-27b-3ca9s.paas.ai.telus.com/v1"
)
GEMMA_MODEL = os.getenv("GEMMA_MODEL", "google/gemma-3-27b-it")

PHYSICS_SYSTEM_PROMPT = """
You are 'Entropix Core'. Analyze the 10x10 thermal matrix.
Identify the single hottest coordinate [row, col].

CALCULATE 3D KINETICS:
1. YAW (Horizontal): Col 0-3="-45", Col 4-6="0", Col 7-9="+45"
2. PITCH (Vertical): Row 0-3="-30", Row 4-6="0", Row 7-9="+30"

Output strictly JSON: {"target": [row, col], "reasoning": "Diagnosis...", "yaw": "-45", "pitch": "+30"}
"""


def _deterministic_fallback(grid_data: np.ndarray, reason: str) -> Dict[str, Any]:
    row, col = [int(v) for v in np.unravel_index(np.argmax(grid_data), grid_data.shape)]
    yaw = "-45" if col <= 3 else ("+45" if col >= 7 else "0")
    pitch = "-30" if row <= 3 else ("+30" if row >= 7 else "0")
    return {
        "target": [row, col],
        "reasoning": f"Deterministic fallback ({reason}) targeting peak thermal cell [{row}, {col}].",
        "yaw": yaw,
        "pitch": pitch,
    }


def get_physics_decision(grid_data: np.ndarray) -> Dict[str, Any]:
    if not DEEPSEEK_API_KEY:
        return _deterministic_fallback(grid_data, "DEEPSEEK_API_KEY not set")

    grid_str = np.array2string(grid_data, precision=1)
    try:
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": PHYSICS_SYSTEM_PROMPT},
                {"role": "user", "content": f"Telemetry: {grid_str}"},
            ],
            max_tokens=150,
            temperature=0.1,
        )
        content = (response.choices[0].message.content or "").strip()
        if content.startswith("```"):
            content = content.strip("`").replace("json", "", 1).strip()
        parsed = json.loads(content)
        if not isinstance(parsed, dict) or "target" not in parsed:
            return _deterministic_fallback(grid_data, "malformed LLM JSON")
        return parsed
    except Exception as exc:
        return _deterministic_fallback(grid_data, f"API error: {exc}")


def get_voice_report(
    status: str, max_temp: float, savings: float, threat_count: int
) -> Tuple[str, Optional[io.BytesIO]]:
    context = (
        f"WARNING: {threat_count} SEPARATE THERMAL BREACHES."
        if threat_count > 1
        else "Single target lock."
    )
    fallback_text = f"ALERT {threat_count} BREACHES" if threat_count > 1 else "THERMAL BREACH DETECTED"

    if not GEMMA_API_KEY:
        return fallback_text, None

    prompt = (
        f"Status: {status}. {context} Max Temp: {max_temp:.1f}C. "
        "Generate a 3-word MAXIMUM military command."
    )

    try:
        client = OpenAI(api_key=GEMMA_API_KEY, base_url=GEMMA_BASE_URL)
        response = client.chat.completions.create(
            model=GEMMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=15,
        )
        text = (response.choices[0].message.content or fallback_text).strip()
        tts = gTTS(text=text, lang="en")
        audio = io.BytesIO()
        tts.write_to_fp(audio)
        audio.seek(0)
        return text, audio
    except Exception:
        return fallback_text, None