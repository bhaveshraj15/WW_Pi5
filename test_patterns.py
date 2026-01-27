import math
import time

class MotorPatterns:
    """Collection of pre-defined motor patterns."""
    
    @staticmethod
    def radial_wave(center_x, center_y, radius, time_step):
        """
        Creates a radial wave pattern.
        Returns intensity (0.0-1.0) for position (x, y) at time_step.
        """
        def pattern_func(x, y, time_step=time_step):
            distance = math.sqrt((x - center_x)**2 + (y - center_y)**2)
            # Wave equation: intensity = sin(distance - time_step)
            intensity = 0.5 + 0.5 * math.sin(distance - time_step)
            return max(0.0, min(1.0, intensity))
        return pattern_func
    
    
    @staticmethod  
    def checkerboard(phase):
        """Alternating checkerboard pattern."""
        def pattern_func(x, y, time_step=0):
            if (x + y + phase) % 2 == 0:
                return 0.8  # Bright
            return 0.2      # Dim
        return pattern_func

    def execute_pattern(grid_manager, pattern_func, duration=5.0, fps=30):
        """
        Executes a pattern function over time.
        pattern_func: Function that takes (x, y, time) and returns intensity
        """
        start_time = time.time()
        frame_delay = 1.0 / fps
        
        while time.time() - start_time < duration:
            current_time = time.time() - start_time
            
            # Update all motors in the grid
            for (x, y), motor in grid_manager.grid.items():
                intensity = pattern_func(x, y, current_time)
                grid_manager.set_intensity_grid(x, y, intensity)
            
            time.sleep(frame_delay)