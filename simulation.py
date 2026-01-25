import numpy as np
import streamlit as st
from typing import List

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

class ServerRoom:
    """
    Physics Engine for Entropix.
    Manages the 2D thermal grid state, thermodynamic diffusion, 
    stochastic load generation, and kinetic cooling interventions.
    """
    
    def __init__(self, size: int = GRID_SIZE):
        self.size = size
        self._initialize_state()

    def _initialize_state(self):
        """Ensures session state variables exist on first load."""
        if 'grid' not in st.session_state:
            st.session_state.grid = np.full((self.size, self.size), AMBIENT_TEMP)
            self._create_random_hotspots(1)
        
        if 'savings' not in st.session_state:
            st.session_state.savings = 0.0

        if 'history' not in st.session_state:
            st.session_state.history = [AMBIENT_TEMP] * HISTORY_LEN

    def _create_random_hotspots(self, count: int):
        for _ in range(count):
            rx, ry = np.random.randint(0, self.size, 2)
            st.session_state.grid[rx, ry] += np.random.randint(20, 40)

    def _simulate_load_spikes(self, grid: np.ndarray) -> np.ndarray:
        if np.random.rand() < SPIKE_PROBABILITY:
            num_spikes = 1
            if np.random.rand() < MULTI_THREAT_CHANCE:
                num_spikes = np.random.randint(2, 4)
            
            for _ in range(num_spikes):
                rx, ry = np.random.randint(0, self.size, 2)
                grid[rx, ry] += np.random.randint(50, 70)
        return grid

    def update_heat(self) -> np.ndarray:
        grid = st.session_state.grid
        new_grid = grid.copy()
        
        # Thermal Diffusion
        for i in range(self.size):
            for j in range(self.size):
                neighbors = []
                if i > 0: neighbors.append(grid[i-1, j])
                if i < self.size-1: neighbors.append(grid[i+1, j])
                if j > 0: neighbors.append(grid[i, j-1])
                if j < self.size-1: neighbors.append(grid[i, j+1])
                
                if neighbors:
                    avg_temp = sum(neighbors) / len(neighbors)
                    new_grid[i, j] += (avg_temp - grid[i, j]) * DIFFUSION_RATE

        # Load Spikes
        new_grid = self._simulate_load_spikes(new_grid)

        # Update State
        st.session_state.grid = new_grid
        
        # Update History
        max_t = np.max(new_grid)
        st.session_state.history.append(max_t)
        if len(st.session_state.history) > HISTORY_LEN:
            st.session_state.history.pop(0)
            
        return st.session_state.grid

    def apply_cooling(self, target_coords: List[int]):
        x, y = target_coords
        grid = st.session_state.grid
        
        # Kinetic Cooling Impact
        grid[x, y] -= DIRECT_COOLING_POWER
        
        # Blast Radius
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.size and 0 <= ny < self.size:
                    grid[nx, ny] -= NEIGHBOR_COOLING_POWER
        
        st.session_state.grid = np.maximum(grid, MIN_SAFE_TEMP)