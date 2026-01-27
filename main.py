# main.py
import motor_core
import SimSpiDriver
from grid_manager import MotorGridManager
from test_patterns import MotorPatterns

def main():
    # 1. Initialize system
    print("\n--- Initializing Motor Grid System ---")
    spi_driver = SimSpiDriver()
    grid = MotorGridManager(rows=6, cols=6, spi_controller=spi_driver)
    
    # 2. Test individual motor control
    print("\n--- Testing Individual Motor Control ---")
    grid.set_intensity_grid(0, 0, 0.5)   # Center position, 50% intensity
    grid.set_intensity_grid(3, 3, 0.8)   # Center motor, 80% intensity
    grid.set_intensity_grid(5, 5, 0.2)   # Corner motor, 20% intensity
    
    # 3. Run patterns 
    print("\n--- Running Radial Wave Pattern ---")
    radial_wave_pattern = MotorPatterns.radial_wave(center_x=3, center_y=3, radius=5, time_step=0)
    MotorPatterns.execute_pattern(grid, radial_wave_pattern, duration=1.0, fps=10)

    print("\n--- Running Checkerboard Pattern ---")
    checkerboard_pattern = MotorPatterns.checkerboard(phase=0)
    MotorPatterns.execute_pattern(grid, checkerboard_pattern, duration=1.0, fps=10)
        
    # 4. Return all motors to idle (1000µs)
    print("\n--- Returning all motors to idle ---")
    for (x, y) in grid.grid:
        grid.set_intensity_grid(x, y, 0.0)
    
    print("\nSystem test complete!")

if __name__ == "__main__":
    main()