import os
from typing import List, Optional, Tuple
import numpy as np

# --- PHYSICS CONSTANTS ---
GRID_SIZE = 10
AMBIENT_TEMP = 22.0
MIN_SAFE_TEMP = 18.0
DIFFUSION_RATE = 0.05
SPIKE_PROBABILITY = 0.3
MULTI_THREAT_CHANCE = 0.2
DIRECT_COOLING_POWER = 60.0
NEIGHBOR_COOLING_POWER = 15.0
HISTORY_LEN = 50


class ThermalSimulationCore:
    """Pure, framework-independent thermal grid and kinetic cooling engine."""

    def __init__(self, size: int = GRID_SIZE, seed: Optional[int] = None):
        self.size = size
        self.rng = np.random.default_rng(seed)
        self.grid = np.full((self.size, self.size), AMBIENT_TEMP, dtype=float)
        self._create_random_hotspots(1)
        self.history: List[float] = [AMBIENT_TEMP] * HISTORY_LEN

    def _create_random_hotspots(self, count: int) -> None:
        for _ in range(count):
            rx, ry = self.rng.integers(0, self.size, size=2)
            self.grid[rx, ry] += float(self.rng.integers(20, 41))

    def _simulate_load_spikes(self, grid: np.ndarray) -> np.ndarray:
        if self.rng.random() < SPIKE_PROBABILITY:
            num_spikes = 1
            if self.rng.random() < MULTI_THREAT_CHANCE:
                num_spikes = int(self.rng.integers(2, 4))

            for _ in range(num_spikes):
                rx, ry = self.rng.integers(0, self.size, size=2)
                grid[rx, ry] += float(self.rng.integers(50, 71))
        return grid

    def update_heat(self) -> np.ndarray:
        grid = self.grid
        new_grid = grid.copy()

        for i in range(self.size):
            for j in range(self.size):
                neighbors = []
                if i > 0:
                    neighbors.append(grid[i - 1, j])
                if i < self.size - 1:
                    neighbors.append(grid[i + 1, j])
                if j > 0:
                    neighbors.append(grid[i, j - 1])
                if j < self.size - 1:
                    neighbors.append(grid[i, j + 1])

                if neighbors:
                    avg_temp = sum(neighbors) / len(neighbors)
                    new_grid[i, j] += (avg_temp - grid[i, j]) * DIFFUSION_RATE

        self.grid = self._simulate_load_spikes(new_grid)

        max_t = float(np.max(self.grid))
        self.history.append(max_t)
        if len(self.history) > HISTORY_LEN:
            self.history.pop(0)

        return self.grid

    def apply_cooling(self, target_coords: List[int]) -> np.ndarray:
        x, y = int(target_coords[0]), int(target_coords[1])
        x = max(0, min(self.size - 1, x))
        y = max(0, min(self.size - 1, y))

        self.grid[x, y] -= DIRECT_COOLING_POWER

        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.size and 0 <= ny < self.size:
                    self.grid[nx, ny] -= NEIGHBOR_COOLING_POWER

        self.grid = np.maximum(self.grid, MIN_SAFE_TEMP)
        return self.grid


class ServerRoom:
    """Streamlit session-state adapter around ThermalSimulationCore."""

    def __init__(self, size: int = GRID_SIZE):
        import streamlit as st

        self.st = st
        self.size = size
        self._initialize_state()

    def _initialize_state(self) -> None:
        if "sim_core" not in self.st.session_state:
            self.st.session_state.sim_core = ThermalSimulationCore(size=self.size)
        if "grid" not in self.st.session_state:
            self.st.session_state.grid = self.st.session_state.sim_core.grid
        if "savings" not in self.st.session_state:
            self.st.session_state.savings = 0.0
        if "history" not in self.st.session_state:
            self.st.session_state.history = self.st.session_state.sim_core.history

    def update_heat(self) -> np.ndarray:
        core: ThermalSimulationCore = self.st.session_state.sim_core
        grid = core.update_heat()
        self.st.session_state.grid = grid
        self.st.session_state.history = core.history
        return grid

    def apply_cooling(self, target_coords: List[int]) -> None:
        core: ThermalSimulationCore = self.st.session_state.sim_core
        grid = core.apply_cooling(target_coords)
        self.st.session_state.grid = grid
        self.st.session_state.history = core.history