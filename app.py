import streamlit as st
import numpy as np
import plotly.graph_objects as go
import time
import pandas as pd
from datetime import datetime
from simulation import ServerRoom
from ai_engine import get_physics_decision, get_voice_report

# --- CONSTANTS ---
CRITICAL_TEMP_THRESHOLD = 60.0
SAFE_TEMP_THRESHOLD = 20.0
MAX_GAUGE_VALUE = 100.0
THEME_COLOR = "#00FF99"
ALERT_COLOR = "#FF4B4B"
BG_COLOR = "#050505"

# --- CONFIGURATION & STYLES ---
st.set_page_config(
    page_title="Entropix | Sovereign Kinetic Defense", 
    layout="wide", 
    page_icon="🛡️"
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

# --- VISUALIZATION COMPONENTS ---
def render_3d_heatmap(grid: np.ndarray) -> go.Figure:
    fig = go.Figure(data=[go.Surface(z=grid, colorscale='Viridis')])
    fig.update_layout(
        title='Real-Time Thermal Topography',
        autosize=False,
        width=600, height=500,
        margin=dict(l=0, r=0, b=0, t=40),
        scene=dict(zaxis=dict(range=[15, 100]), aspectratio=dict(x=1, y=1, z=0.7))
    )
    return fig

def render_threat_gauge(current_val: float) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=current_val,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "CRITICAL THREAT LEVEL (°C)"},
        gauge={
            'axis': {'range': [SAFE_TEMP_THRESHOLD, MAX_GAUGE_VALUE]},
            'bar': {'color': ALERT_COLOR},
            'steps': [
                {'range': [0, CRITICAL_TEMP_THRESHOLD], 'color': "#111"},
                {'range': [CRITICAL_TEMP_THRESHOLD, MAX_GAUGE_VALUE], 'color': "#330000"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': CRITICAL_TEMP_THRESHOLD
            }
        }
    ))
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor="#000", font={'color': "#FFF"})
    return fig

# --- LOGIC & STATE MANAGEMENT ---
def init_session_state():
    """Initializes session variables WITHOUT overwriting the grid."""
    defaults = {
        'breach_active': False,
        'activity_log': [],
        'scram_triggered': False,
        'savings': 0.0,
        'history': [22.0] * 50
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

def log_intervention(target, yaw, pitch, reason, threat_count):
    try:
        y_val, p_val = int(yaw), int(pitch)
        dir_h = "LEFT" if y_val < 0 else ("RIGHT" if y_val > 0 else "CENTER")
        dir_v = "DOWN" if p_val < 0 else ("UP" if p_val > 0 else "LEVEL")
        readable_action = f"AIMING {dir_h} / {dir_v}"
    except ValueError:
        readable_action = f"YAW {yaw} / PITCH {pitch}"

    queue_note = f" [QUEUED: {threat_count-1} MORE]" if threat_count > 1 else ""
    
    st.session_state.activity_log.insert(0, {
        "TIMESTAMP": datetime.now().strftime('%H:%M:%S'),
        "SECTOR": str(target),
        "AIRFLOW DIRECTION": readable_action,
        "THREAT DIAGNOSIS": reason + queue_note
    })

# --- UI & APP LOGIC ---
def render_sidebar():
    with st.sidebar:
        st.header("COMMAND DECK")
        st.markdown("""
            <div class="sovereign-badge">
                🔒 DATA RESIDENCY: CANADA<br>
                ENCRYPTION: AES-256<br>
                CLOUD: TELUS SOVEREIGN
            </div>
        """, unsafe_allow_html=True)
        
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

    # --- INITIALIZE SIMULATION ---
    # This must run BEFORE any grid access
    room = ServerRoom(size=10)
    
    if live_mode:
        room.update_heat()
        time.sleep(0.5)

    # --- LAYOUT ---
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("📍 3D DIGITAL TWIN")
        
        # Safe access to grid now that room is initialized
        grid = st.session_state.grid
        threat_count = np.count_nonzero(grid > CRITICAL_TEMP_THRESHOLD)
        
        if threat_count > 1:
            st.warning(f"⚠️ MULTIPLE BREACHES ({threat_count}). PRIORITY QUEUE ACTIVE.")
        elif threat_count == 1:
            st.error("⚠️ SINGLE BREACH DETECTED.")
        elif live_mode:
            st.caption("⚡ SIMULATION RUNNING... (AUTO-REFRESH)")
        else:
            if st.button("STEP SIMULATION >>", type="secondary", use_container_width=True):
                room.update_heat()
        
        st.plotly_chart(render_3d_heatmap(grid), use_container_width=True)

    with col2:
        st.subheader("🧠 DEEPSEEK THREAT ENGINE")
        
        # Metrics
        m1, m2, m3, m4 = st.columns(4)
        current_max = np.max(st.session_state.grid)
        avg_temp = np.mean(st.session_state.grid)
        annual_proj = st.session_state.savings * 365 * 24
        
        m1.metric("Est. Savings", f"${st.session_state.savings:.2f}")
        m2.metric("Max Temp", f"{current_max:.1f}°C")
        m3.metric("Avg Temp", f"{avg_temp:.1f}°C")
        m4.metric("Proj. ROI", f"${annual_proj:,.0f}") 

        # Visuals
        st.plotly_chart(render_threat_gauge(current_max), use_container_width=True)
        st.caption("THREAT INTENSITY HISTORY")
        st.area_chart(pd.DataFrame(st.session_state.history, columns=["Max Temp"]), color=ALERT_COLOR, height=120)

        # Core Logic
        if current_max > CRITICAL_TEMP_THRESHOLD:
            if not st.session_state.breach_active:
                st.session_state.breach_active = True
                report, audio = get_voice_report("CRITICAL", current_max, st.session_state.savings, threat_count)
                st.audio(audio, format='audio/mp3', autoplay=True)
                st.toast(f"🔊 ALERT: {report}")

            decision = None
            if not live_mode:
                with st.spinner("DeepSeek Calculating Kinetics..."):
                    decision = get_physics_decision(st.session_state.grid)
            else:
                decision = get_physics_decision(st.session_state.grid)

            target = decision.get('target', [0, 0])
            yaw = decision.get('yaw', '0')
            pitch = decision.get('pitch', '0')
            
            try:
                h_text = "LEFT" if int(yaw) < 0 else ("RIGHT" if int(yaw) > 0 else "CENTER")
                v_text = "DOWN" if int(pitch) < 0 else ("UP" if int(pitch) > 0 else "LEVEL")
                direction_text = f"AIMING {h_text} & {v_text}"
            except:
                direction_text = "CALCULATING..."

            st.code(f"""
TARGET: {target}
AIRFLOW DIRECTION: {direction_text} ({yaw}° / {pitch}°)
LOGIC: {decision['reasoning']}
STATUS: {threat_count} ACTIVE THREATS
            """, language="yaml")

            if auto_mode:
                room.apply_cooling(target)
                st.session_state.savings += 1.25
                st.toast(f"⚡ NEUTRALIZED: {target}", icon="🛡️")
                log_intervention(target, yaw, pitch, decision['reasoning'], threat_count)
                st.session_state.breach_active = False 
                if live_mode:
                    time.sleep(1) 
                    st.rerun()
            else:
                if st.button("EXECUTE KINETIC RESPONSE", type="primary"):
                    room.apply_cooling(target)
                    st.session_state.savings += 1.25
                    log_intervention(target, yaw, pitch, decision['reasoning'], threat_count)
                    st.session_state.breach_active = False
                    st.success("TARGET NEUTRALIZED.")
                    time.sleep(1)
                    st.rerun()
        else:
            if st.session_state.breach_active:
                st.session_state.breach_active = False
            if live_mode:
                time.sleep(1)
                st.rerun()

    # Audit Log
    st.divider()
    st.subheader("📜 3D KINETIC AUDIT LOG (IMMUTABLE RECORD)")
    if st.session_state.activity_log:
        st.dataframe(
            pd.DataFrame(st.session_state.activity_log),
            use_container_width=True,
            hide_index=True,
            column_config={
                "TIMESTAMP": "Time",
                "SECTOR": "Target Sector",
                "AIRFLOW DIRECTION": "Airflow Direction",
                "THREAT DIAGNOSIS": "AI Diagnosis"
            }
        )
    else:
        st.info("System Secure. No kinetic interventions recorded yet.")

if __name__ == "__main__":
    main()