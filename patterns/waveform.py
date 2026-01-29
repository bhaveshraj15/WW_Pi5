# patterns/waveforms.py
import math
import numpy as np
from typing import Callable

class WaveformGenerator:
    """Generates various motor patterns"""
    
    @staticmethod
    def radial_wave(center_x: float, center_y: float, 
                   wavelength: float = 2.0, speed: float = 1.0) -> Callable:
        """Create a radial wave emanating from center"""
        def pattern(x: int, y: int, t: float) -> float:
            dx = x - center_x
            dy = y - center_y
            distance = math.sqrt(dx*dx + dy*dy)
            value = math.sin(distance * (2*math.pi/wavelength) - t * speed * 2*math.pi)
            return 0.5 + 0.5 * value
        return pattern
    
    @staticmethod
    def row_sweep(direction: str = 'right', speed: float = 1.0) -> Callable:
        """Create a row-by-row sweeping pattern"""
        def pattern(x: int, y: int, t: float) -> float:
            if direction == 'right':
                pos = (x - t * speed) % 2.0
            else:  # left
                pos = (x + t * speed) % 2.0
            return max(0.0, 1.0 - abs(pos - 1.0))
        return pattern
    
    @staticmethod
    def checkerboard(swap_freq: float = 0.5) -> Callable:
        """Create alternating checkerboard pattern"""
        def pattern(x: int, y: int, t: float) -> float:
            swap = math.sin(t * swap_freq * 2 * math.pi) > 0
            if (x + y) % 2 == (1 if swap else 0):
                return 0.8
            return 0.2
        return pattern
    
    @staticmethod
    def spiral(center_x: float, center_y: float, 
              rotations: float = 3.0, speed: float = 1.0) -> Callable:
        """Create a rotating spiral pattern"""
        def pattern(x: int, y: int, t: float) -> float:
            dx = x - center_x
            dy = y - center_y
            
            # Convert to polar coordinates
            angle = math.atan2(dy, dx)
            radius = math.sqrt(dx*dx + dy*dy)
            
            # Spiral equation
            value = math.sin(angle * rotations - t * speed * 2 * math.pi + radius * 0.5)
            return 0.5 + 0.5 * value
        return pattern
    
    @staticmethod
    def perlin_noise(scale: float = 0.3, speed: float = 0.5) -> Callable:
        """Create Perlin noise-like pattern (simplified)"""
        def pattern(x: int, y: int, t: float) -> float:
            # Simplified gradient noise
            nx = scale * x + t * speed
            ny = scale * y
            
            # Simple hash-based noise
            def noise(nx, ny):
                return math.sin(nx * 12.9898 + ny * 78.233) * 43758.5453
            
            value = math.sin(noise(nx, ny) + t * speed)
            return 0.5 + 0.5 * value
        return pattern