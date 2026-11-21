<div align="center">

# Entropix

**Autonomous Thermal Regulation & Fault-Tolerant Kinetic Control Engine**

[![CI](https://github.com/aakashkrmishra09/entropix-kinetic-defense/actions/workflows/ci.yml/badge.svg)](https://github.com/aakashkrmishra09/entropix-kinetic-defense/actions/workflows/ci.yml)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://aakash-entropix-kinetic-defense.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/Tests-Pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white)](tests/test_entropix.py)

[Live App](https://aakash-entropix-kinetic-defense.streamlit.app/) · [Architecture](#architecture) · [Quick Start](#quick-start) · [Testing](#testing)

</div>

---

## Overview

High-density compute environments suffer from localized thermal spikes that traditional room-wide HVAC systems address slowly and inefficiently. **Entropix** simulates a **10x10 3D thermal digital twin** paired with a **3-axis targeted cooling actuator** and **fault-tolerant AI decisioning**.

Rather than trusting unverified model outputs directly, Entropix pairs LLM reasoning (`DeepSeek-V3` / `Gemma-3`) with **deterministic fallback logic**, **hard actuator bounds**, and an **Emergency SCRAM override**.

---

## Key Features

- **Decoupled Physics Engine (`simulation.py`):** Pure `NumPy` thermodynamic diffusion, multi-hotspot load injections, and localized cooling dispersion isolated from UI state.
- **Resilient AI + Deterministic Fallback (`ai_engine.py`):** Uses `DeepSeek-V3` for structured JSON target selection and `Gemma-3` for alert synthesis, automatically falling back to a deterministic peak-thermal solver when API keys are absent or calls fail.
- **Safety Guardrails & SCRAM (`app.py`):** Enforces immediate SCRAM shutdown lockdown and clamps actuator angles (`yaw`, `pitch`) and grid coordinates to safe bounds before execution.
- **Automated CI Pipeline (`.github/workflows/ci.yml`):** Runs `pytest` automatically on pushes and pull requests.

---

## Architecture

```text
10x10 Thermal Grid (simulation.py)
        |
        v
SCRAM Safety Check (app.py) ---> Immediate lockdown if active
        |
        v
Decision Engine (ai_engine.py)
  |-- Primary: DeepSeek-V3 JSON target + angle inference
  +-- Fallback: Deterministic peak-hotspot solver (no API key required)
        |
        v
Actuator Guardrails (app.py) ---> Clamp yaw, pitch, and coordinates
        |
        v
Cooling Execution + Audit Log + Alerting (Gemma-3 / gTTS)
