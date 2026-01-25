import json
import io
import numpy as np
from openai import OpenAI
from gtts import gTTS
from typing import Dict, Any, Tuple, Optional

# --- CONFIGURATION ---
DEEPSEEK_CONFIG = {
    "api_key": "a12a7d3705b12aeb46eb4cc8d77f5446",
    "base_url": "https://deepseekv32-3ca9s.paas.ai.telus.com/v1",
    "model": "deepseek-ai/DeepSeek-V3.2-Exp"
}

GEMMA_CONFIG = {
    "api_key": "dc8704d41888afb2b889a8ebac81d12f",
    "base_url": "https://gemma-3-27b-3ca9s.paas.ai.telus.com/v1",
    "model": "google/gemma-3-27b-it"
}

PHYSICS_SYSTEM_PROMPT = """
You are 'Entropix Core'. Analyze the 10x10 thermal matrix.
Identify the single hottest coordinate [row, col].

CALCULATE 3D KINETICS:
1. YAW (Horizontal): Col 0-3="-45", Col 4-6="0", Col 7-9="+45"
2. PITCH (Vertical): Row 0-3="-30", Row 4-6="0", Row 7-9="+30"

Output JSON: {"target": [row, col], "reasoning": "Diagnosis...", "yaw": "-45", "pitch": "+30"}
"""

client_physics = OpenAI(api_key=DEEPSEEK_CONFIG["api_key"], base_url=DEEPSEEK_CONFIG["base_url"])
client_voice = OpenAI(api_key=GEMMA_CONFIG["api_key"], base_url=GEMMA_CONFIG["base_url"])

def get_physics_decision(grid_data: np.ndarray) -> Dict[str, Any]:
    grid_str = np.array2string(grid_data, precision=1)
    try:
        response = client_physics.chat.completions.create(
            model=DEEPSEEK_CONFIG["model"], 
            messages=[
                {"role": "system", "content": PHYSICS_SYSTEM_PROMPT}, 
                {"role": "user", "content": f"Telemetry: {grid_str}"}
            ],
            max_tokens=150, temperature=0.1
        )
        content = response.choices[0].message.content.replace("```json", "").replace("```", "").strip()
        return json.loads(content)
    except Exception as e:
        return {"target": [5, 5], "reasoning": f"FAILSAFE: {str(e)}", "yaw": "0", "pitch": "0"}

def get_voice_report(status: str, max_temp: float, savings: float, threat_count: int) -> Tuple[str, Optional[io.BytesIO]]:
    if threat_count > 1:
        context = f"WARNING: {threat_count} SEPARATE THERMAL BREACHES."
    else:
        context = "Single target lock."

    prompt = (
        f"Status: {status}. {context} Max Temp: {max_temp:.1f}C. "
        "Generate a 3-word MAXIMUM military command."
    )
    
    try:
        response = client_voice.chat.completions.create(
            model=GEMMA_CONFIG["model"],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=15
        )
        text = response.choices[0].message.content.strip()
        tts = gTTS(text=text, lang='en')
        audio = io.BytesIO()
        tts.write_to_fp(audio)
        audio.seek(0)
        return text, audio
    except Exception:
        return "ALERT SYSTEM OFFLINE", None