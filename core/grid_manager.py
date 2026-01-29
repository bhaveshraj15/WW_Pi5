# core/grid_manager.py
from typing import Dict, List, Tuple, Optional
import numpy as np
from .motor_node import MotorNode

class MotorGridManager:
    """Manages the entire NxM motor grid"""
    
    def __init__(self, rows: int, cols: int, motors_per_pico: int = 12):
        self.rows = rows
        self.cols = cols
        self.motors_per_pico = motors_per_pico
        
        # Create motor grid
        self.grid: Dict[Tuple[int, int], MotorNode] = {}
        self._create_grid()
        
        # Organize by Pico for efficient updates
        self.pico_map: Dict[int, List[MotorNode]] = {}
        self._organize_by_pico()
        
        # Motor limits
        self.min_pulse = 1000
        self.max_pulse = 2000
        
        print(f"[Grid] Created {rows}x{cols} grid ({rows*cols} motors)")
        print(f"[Grid] Organized into {len(self.pico_map)} Pico groups")
    
    def _create_grid(self):
        """Create motor nodes with Pico/channel assignments"""
        for y in range(self.rows):
            for x in range(self.cols):
                linear_idx = y * self.cols + x
                pico_id = linear_idx // self.motors_per_pico
                channel = linear_idx % self.motors_per_pico
                
                self.grid[(x, y)] = MotorNode(
                    grid_x=x,
                    grid_y=y,
                    pico_id=pico_id,
                    channel=channel
                )
    
    def _organize_by_pico(self):
        """Group motors by their controlling Pico"""
        self.pico_map.clear()
        for motor in self.grid.values():
            if motor.pico_id not in self.pico_map:
                self.pico_map[motor.pico_id] = []
            self.pico_map[motor.pico_id].append(motor)
        
        # Sort by channel for consistent ordering
        for pico_id in self.pico_map:
            self.pico_map[pico_id].sort(key=lambda m: m.channel)
    
    def set_motor(self, x: int, y: int, pulse_us: int) -> bool:
        """Set a specific motor's pulse width"""
        if (x, y) not in self.grid:
            print(f"[Grid] Invalid coordinates: ({x}, {y})")
            return False
        
        motor = self.grid[(x, y)]
        return motor.set_pulse(pulse_us, (self.min_pulse, self.max_pulse))
    
    def set_intensity(self, x: int, y: int, intensity: float) -> bool:
        """Set motor by intensity (0.0 to 1.0)"""
        if (x, y) not in self.grid:
            return False
        
        motor = self.grid[(x, y)]
        return motor.set_intensity(intensity, (self.min_pulse, self.max_pulse))
    
    def get_pico_commands(self) -> Dict[int, List[int]]:
        """
        Get motor commands organized by Pico
        Returns: {pico_id: [pulse_for_motor_0, pulse_for_motor_1, ...]}
        """
        commands = {}
        
        for pico_id, motors in self.pico_map.items():
            commands[pico_id] = [motor.current_pulse for motor in motors]
        
        return commands
    
    def get_motor(self, x: int, y: int) -> Optional[MotorNode]:
        """Get motor at specified coordinates"""
        return self.grid.get((x, y))
    
    def get_grid_array(self, attribute='pulse') -> np.ndarray:
        """Get grid data as 2D numpy array"""
        arr = np.zeros((self.rows, self.cols))
        
        for y in range(self.rows):
            for x in range(self.cols):
                motor = self.grid.get((x, y))
                if motor:
                    if attribute == 'pulse':
                        arr[y, x] = motor.current_pulse
                    elif attribute == 'intensity':
                        arr[y, x] = motor.intensity
        
        return arr
    
    def idle_all(self):
        """Set all motors to idle/safe pulse"""
        for motor in self.grid.values():
            motor.set_pulse(self.min_pulse, (self.min_pulse, self.max_pulse))
    
    def set_all(self, pulse_us: int):
        """Set all motors to the same pulse"""
        pulse_us = max(self.min_pulse, min(pulse_us, self.max_pulse))
        for motor in self.grid.values():
            motor.set_pulse(pulse_us, (self.min_pulse, self.max_pulse))