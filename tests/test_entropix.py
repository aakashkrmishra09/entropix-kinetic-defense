import numpy as np

from ai_engine import get_physics_decision
from app import clamp_angle, format_airflow_direction, sanitize_target
from simulation import MIN_SAFE_TEMP, ThermalSimulationCore


def test_thermal_core_initializes_grid_and_history():
    core = ThermalSimulationCore(size=10, seed=42)
    assert core.grid.shape == (10, 10)
    assert len(core.history) == 50
    assert float(np.max(core.grid)) > 22.0


def test_apply_cooling_respects_minimum_safe_temp():
    core = ThermalSimulationCore(size=10, seed=42)
    core.grid[4, 4] = 85.0
    updated = core.apply_cooling([4, 4])
    assert float(np.min(updated)) >= MIN_SAFE_TEMP
    assert float(updated[4, 4]) < 85.0


def test_deterministic_fallback_targets_hottest_cell():
    grid = np.full((10, 10), 22.0)
    grid[8, 9] = 78.5
    decision = get_physics_decision(grid)
    assert decision["target"] == [8, 9]
    assert decision["yaw"] == "+45"
    assert decision["pitch"] == "+30"


def test_guardrails_clamp_angles_and_sanitize_targets():
    assert clamp_angle(250, -90, 90) == 90
    assert clamp_angle(-250, -90, 90) == -90
    assert clamp_angle("invalid", -45, 45) == 0
    assert sanitize_target([99, -5], (10, 10)) == [9, 0]
    assert sanitize_target(None, (10, 10)) == [5, 5]
    assert format_airflow_direction(-45, 30) == "LEFT / UP"