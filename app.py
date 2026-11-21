from datetime import datetime
import time
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ai_engine import get_physics_decision, get_voice_report
from simulation import ServerRoom

# --- CONSTANTS ---
CRITICAL_TEMP_THRESHOLD = 60.0
SAFE_TEMP_THRESHOLD = 20.0
MAX_GAUGE_VALUE = 100.0
MIN_YAW, MAX_YAW = -90, 90
MIN_PITCH, MAX_PITCH = -45, 45
SAVINGS_PER_INTERVENTION = 1.25

THEME_COLOR = "#00FF99"
ALERT_COLOR = "#FF4B4B"
BG_COLOR = "#050505"

# --- CONFIGURATION & STYLES ---
st.set_page_config(
    page_title="Entropix | Sovereign Kinetic Defense",
    layout="wide",
    page_icon="🛡️",
)

CUSTOM_CSS = f"""
    <style>
    .stApp {{ background-color: {BG_COLOR}; color: {THEME_COLOR}; }}
    .sovereign-badge {{
        background-color: #1a1a1a;
        border: 1px solid {THEME_COLOR};
        color: {THEME_COLOR};
        padding: 5px 10px;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
        font-size: 12px;
        text-align: center;
        margin-bottom: 20px;
    }}
    .stButton>button[kind="primary"] {{
        background-color: #FF0000;
        color: white;
        border: none;
        font-weight: bold;
    }}
    .metric-card {{ border: 1px solid #333; padding: 10px; border-radius: 5px; background: #111; }}
    div[data-testid="stMarkdownContainer"] p {{ font-family: 'Courier New', monospace; }}
    </style>
"""


# --- HELPERS & GUARDRAILS ---
def clamp_angle(val, min_val: int, max_val: int) -> int:
    try:
        parsed = int(float(val))
    except (TypeError, ValueError):
        return 0
    return max(min_val, min(max_val, parsed))


def sanitize_target(target, grid_shape: tuple[int, int]) -> list[int]:
    rows, cols = grid_shape
    if isinstance(target, (list, tuple)) and len(target) == 2:
        try:
            r = max(0, min(rows - 1, int(target[0])))
            c = max(0, min(cols - 1, int(target[1])))
            return [r, c]
        except (TypeError, ValueError):
            pass
    return [rows // 2, cols // 2]


def format_airflow_direction(yaw: int, pitch: int) -> str:
    h_text = "LEFT" if yaw < 0 else ("RIGHT" if yaw > 0 else "CENTER")
    v_text = "DOWN" if pitch < 0 else ("UP" if pitch > 0 else "LEVEL")
    return f"{h_text} / {v_text}"


# --- VISUALIZATION COMPONENTS ---
def render_3d_heatmap(grid: np.ndarray) -> go.Figure:
    fig = go.Figure(data=[go.Surface(z=grid, colorscale="Viridis")])
    fig.update_layout(
        title="Real-Time Thermal Topography",
        autosize=True,
        height=500,
        margin=dict(l=0, r=0, b=0, t=40),
        scene=dict(
            zaxis=dict(range=[15, 100]),
            aspectratio=dict(x=1, y=1, z=0.7),
        ),
    )
    return fig


def render_threat_gauge(current_val: float) -> go.Figure:
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=current_val,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "CRITICAL THREAT LEVEL (°C)"},
            gauge={
                "axis": {"range": [SAFE_TEMP_THRESHOLD, MAX_GAUGE_VALUE]},
                "bar": {"color": ALERT_COLOR},
                "steps": [
                    {"range": [0, CRITICAL_TEMP_THRESHOLD], "color": "#111"},
                    {"range": [CRITICAL_TEMP_THRESHOLD, MAX_GAUGE_VALUE], "color": "#330000"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": CRITICAL_TEMP_THRESHOLD,
                },
            },
        )
    )
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor="#000",
        font={"color": "#FFF"},
    )
    return fig


# --- LOGIC & STATE MANAGEMENT ---
def init_session_state():
    defaults = {
        "breach_active": False,
        "activity_log": [],
        "scram_triggered": False,
        "savings": 0.0,
        "history": [22.0] * 50,
        "last_decision": None,
        "step_count": 0,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def log_intervention(target: list[int], yaw: int, pitch: int, reason: str, threat_count: int):
    direction = format_airflow_direction(yaw, pitch)
    queue_note = f" [QUEUED: {threat_count - 1} MORE]" if threat_count > 1 else ""

    st.session_state.activity_log.insert(
        0,
        {
            "TIMESTAMP": datetime.now().strftime("%H:%M:%S"),
            "SECTOR": str(target),
            "AIRFLOW DIRECTION": f"AIMING {direction} ({yaw}° / {pitch}°)",
            "THREAT DIAGNOSIS": f"{reason}{queue_note}",
        },
    )


def apply_cooling_action(room: ServerRoom, target: list[int], yaw: int, pitch: int, reasoning: str, threat_count: int):
    room.apply_cooling(target)
    st.session_state.savings += SAVINGS_PER_INTERVENTION
    log_intervention(target, yaw, pitch, reasoning, threat_count)
    st.session_state.breach_active = False
    st.session_state.last_decision = None


# --- UI & APP LOGIC ---
def render_sidebar():
    with st.sidebar:
        st.header("COMMAND DECK")
        st.markdown(
            f"""
            <div class="sovereign-badge">
                🔒 DATA RESIDENCY: CANADA<br>
                ENCRYPTION: AES-256<br>
                CLOUD: TELUS SOVEREIGN
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("### ⚙️ SIMULATION CONTROL")
        live_mode = st.toggle("RUN LIVE SIMULATION", value=False)

        st.divider()
        st.markdown("### 🛡️ DEFENSE PROTOCOLS")
        auto_mode = st.toggle("ARM AUTONOMOUS RESPONSE", value=False)

        if auto_mode:
            st.error("⚠️ SYSTEM ARMED: AI HAS CONTROL")
        else:
            st.success("MANUAL OVERRIDE ENGAGED")

        st.divider()
        if st.button("🚨 EMERGENCY SCRAM (SHUTDOWN)", type="primary"):
            st.session_state.scram_triggered = True
            st.session_state.breach_active = False
            st.session_state.last_decision = None
            st.rerun()

    return live_mode, auto_mode


def handle_scram_state():
    if st.session_state.scram_triggered:
        st.error("🛑 SYSTEM LOCKDOWN INITIATED. KINETIC SYSTEMS OFFLINE.")
        if st.button("🔄 INITIATE SYSTEM REBOOT", type="secondary"):
            st.session_state.scram_triggered = False
            st.rerun()
        st.stop()


def main():
    init_session_state()
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.title("🛡️ ENTROPIX // KINETIC DEFENSE")
    st.caption("TELUS SOVEREIGN AI • 3-AXIS AUTONOMOUS REGULATION")

    live_mode, auto_mode = render_sidebar()
    handle_scram_state()

    room = ServerRoom(size=10)
    if live_mode:
        room.update_heat()
        st.session_state.step_count += 1

    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("📍 3D DIGITAL TWIN")
        grid = st.session_state.grid
        threat_count = int(np.count_nonzero(grid > CRITICAL_TEMP_THRESHOLD))

        if threat_count > 1:
            st.warning(f"⚠️ MULTIPLE BREACHES ({threat_count}). PRIORITY QUEUE ACTIVE.")
        elif threat_count == 1:
            st.error("⚠️ SINGLE BREACH DETECTED.")
        elif live_mode:
            st.caption("⚡ SIMULATION RUNNING... (LIVE STEP MODE)")
        else:
            if st.button("STEP SIMULATION >>", type="secondary", width="stretch"):
                room.update_heat()
                st.session_state.step_count += 1
                st.rerun()

        st.plotly_chart(render_3d_heatmap(grid), width="stretch")

    with col2:
        st.subheader("🧠 DEEPSEEK THREAT ENGINE")

        current_max = float(np.max(grid))
        avg_temp = float(np.mean(grid))
        annual_proj = st.session_state.savings * 365 * 24

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Est. Savings", f"${st.session_state.savings:.2f}")
        m2.metric("Max Temp", f"{current_max:.1f}°C")
        m3.metric("Avg Temp", f"{avg_temp:.1f}°C")
        m4.metric("Proj. ROI", f"${annual_proj:,.0f}")

        st.plotly_chart(render_threat_gauge(current_max), width="stretch")
        st.caption("THREAT INTENSITY HISTORY")
        st.area_chart(
            pd.DataFrame(st.session_state.history, columns=["Max Temp"]),
            color=ALERT_COLOR,
            height=120,
        )

        if current_max > CRITICAL_TEMP_THRESHOLD:
            if not st.session_state.breach_active:
                st.session_state.breach_active = True
                report, audio = get_voice_report(
                    "CRITICAL", current_max, st.session_state.savings, threat_count
                )
                if audio:
                    st.audio(audio, format="audio/mp3", autoplay=True)
                st.toast(f"🔊 ALERT: {report}")

            if st.session_state.last_decision is None or live_mode:
                if not live_mode:
                    with st.spinner("DeepSeek Calculating Kinetics..."):
                        raw_decision = get_physics_decision(grid)
                else:
                    raw_decision = get_physics_decision(grid)
                st.session_state.last_decision = raw_decision or {}

            decision = st.session_state.last_decision
            target = sanitize_target(decision.get("target"), grid.shape)
            yaw = clamp_angle(decision.get("yaw", 0), MIN_YAW, MAX_YAW)
            pitch = clamp_angle(decision.get("pitch", 0), MIN_PITCH, MAX_PITCH)
            reasoning = str(decision.get("reasoning", "Thermal threshold exceeded."))
            direction_text = f"AIMING {format_airflow_direction(yaw, pitch)}"

            st.code(
                f"""
TARGET: {target}
AIRFLOW DIRECTION: {direction_text} ({yaw}° / {pitch}°)
LOGIC: {reasoning}
STATUS: {threat_count} ACTIVE THREATS
                """.strip(),
                language="yaml",
            )

            if auto_mode:
                apply_cooling_action(room, target, yaw, pitch, reasoning, threat_count)
                st.toast(f"⚡ NEUTRALIZED: {target}", icon="🛡️")
                if live_mode:
                    time.sleep(0.8)
                    st.rerun()
            else:
                if st.button("EXECUTE KINETIC RESPONSE", type="primary"):
                    apply_cooling_action(room, target, yaw, pitch, reasoning, threat_count)
                    st.success("TARGET NEUTRALIZED.")
                    time.sleep(0.5)
                    st.rerun()
        else:
            st.session_state.breach_active = False
            st.session_state.last_decision = None
            if live_mode:
                time.sleep(0.8)
                st.rerun()

    st.divider()
    st.subheader("📜 3D KINETIC AUDIT LOG (IMMUTABLE RECORD)")
    if st.session_state.activity_log:
        st.dataframe(
            pd.DataFrame(st.session_state.activity_log),
            width="stretch",
            hide_index=True,
            column_config={
                "TIMESTAMP": "Time",
                "SECTOR": "Target Sector",
                "AIRFLOW DIRECTION": "Airflow Direction",
                "THREAT DIAGNOSIS": "AI Diagnosis",
            },
        )
    else:
        st.info("System Secure. No kinetic interventions recorded yet.")


if __name__ == "__main__":
    main()