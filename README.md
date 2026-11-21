# 🛡️ Entropix // Sovereign Kinetic Defense

[![Entropix CI](https://github.com/aakashkrmishra09/entropix-kinetic-defense/actions/workflows/ci.yml/badge.svg)](https://github.com/aakashkrmishra09/entropix-kinetic-defense/actions/workflows/ci.yml)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://aakash-entropix-kinetic-defense.streamlit.app/)

**AI-Driven Autonomous Thermal Regulation & Fault-Tolerant Control Prototype**  
*Built by Aakash Kumar Mishra* | **[Launch Live 3D Digital Twin →](https://aakash-entropix-kinetic-defense.streamlit.app/)**

---

## 🚨 Problem Statement
Traditional data-center HVAC systems cool entire server halls in response to localized rack hotspots, wasting substantial energy. **Entropix** models a targeted **3-axis kinetic cooling turret** paired with a **10×10 3D thermal digital twin** to detect localized thermal spikes and direct cooling airflow precisely to the highest-risk sector.

---

## 🏗️ System Architecture & Safety Guardrails

\\	ext
[10x10 Thermal Grid (simulation.py)]
          │
          ▼
[Emergency SCRAM Check (app.py)] ──► (If Triggered: Immediate Lockdown)
          │
          ▼
[AI Reasoning Engine (ai_engine.py)]
   ├── Primary: DeepSeek-V3 JSON Inference (Target [row, col], Yaw, Pitch)
   └── Fallback: Deterministic Peak-Cell & Angle Solver (Offline / Timeout Safe)
          │
          ▼
[Actuator Guardrails (app.py)] ──► Clamps Yaw [-90°, 90°], Pitch [-45°, 45°], Grid Bounds
          │
          ▼
[Kinetic Cooling + Immutable Audit Log + Gemma-3 / Offline Alerting]
\
### Key Engineering Highlights
- **Decoupled Physics Core (\simulation.py\):** Separates pure NumPy thermodynamic diffusion, stochastic multi-hotspot load spikes, and cooling blast-radius math (\ThermalSimulationCore\) from Streamlit session state for deterministic unit testing.
- **Resilient LLM Integration (\i_engine.py\):** Queries DeepSeek-V3 for structured JSON targeting and Gemma-3 for voice alerts via environment-configured endpoints, with automatic fallback to a deterministic peak-thermal solver when offline or unconfigured.
- **Deterministic Safety Guardrails (\pp.py\):** Enforces a hard **Emergency SCRAM** shutdown override and clamps all LLM-predicted \yaw\, \pitch\, and grid coordinates to safe mechanical bounds before actuation.
- **Automated Verification (\	ests/\ + GitHub Actions):** Includes \pytest\ unit tests verifying thermal bounds, cooling safety floors, fallback targeting, and coordinate clamping.

---

## 🛠️ Tech Stack
- **Simulation & Numerics:** Python 3.10+, NumPy, Pandas
- **AI & Audio:** DeepSeek-V3 (OpenAI-compatible API), Google Gemma-3, gTTS
- **Visualization & UI:** Streamlit, Plotly (3D Surface Topography & Threat Gauge)
- **Testing & CI:** Pytest, GitHub Actions

---

## 🚀 Local Setup & Execution

**1. Clone the Repository**
\\ash
git clone https://github.com/aakashkrmishra09/entropix-kinetic-defense.git
cd entropix-kinetic-defense
\
**2. Create a Virtual Environment & Install Dependencies**
\\ash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
\
**3. Configure Environment Variables (Optional)**
The system runs out-of-the-box in deterministic fallback mode without API keys. To enable live DeepSeek-V3 and Gemma-3 endpoints:
\\ash
copy .env.example .env
# Add your DEEPSEEK_API_KEY and GEMMA_API_KEY inside .env
\
**4. Run Tests & Launch Dashboard**
\\ash
pytest -v
streamlit run app.py
\