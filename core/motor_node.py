# core/motor_node.py
from dataclasses import dataclass
from typing import Tuple

@dataclass
class MotorNode:
    """Represents a single motor in the grid"""
    grid_x: int
    grid_y: int
    pico_id: int          # Which Pi Pico controls this motor
    channel: int          # Which PWM pin on the Pico (0-11)
    current_pulse: int = 1000
    target_pulse: int = 1000
    intensity: float = 0.0
    
    @property
    def coord(self) -> Tuple[int, int]:
        return (self.grid_x, self.grid_y)
    
    def set_pulse(self, pulse_us: int, limits=(1000, 2000)) -> bool:
        """Set motor pulse with limits"""
        min_pulse, max_pulse = limits
        pulse_us = max(min_pulse, min(pulse_us, max_pulse))
        
        self.target_pulse = pulse_us
        self.current_pulse = pulse_us
        self.intensity = (pulse_us - min_pulse) / (max_pulse - min_pulse)
        return True
    
    def set_intensity(self, intensity: float, limits=(1000, 2000)) -> bool:
        """Set motor by intensity (0.0 to 1.0)"""
        intensity = max(0.0, min(1.0, intensity))
        min_pulse, max_pulse = limits
        pulse_us = min_pulse + int(intensity * (max_pulse - min_pulse))
        return self.set_pulse(pulse_us, limits)