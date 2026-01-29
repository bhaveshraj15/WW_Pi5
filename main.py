# main.py
#!/usr/bin/env python3
"""
Raspberry Pi 5 Motor Grid Controller
Controls 6x6 motor grid via 3 Pi Picos over SPI
"""

import sys
import time
import yaml
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from hardware.spi_driver import RealSPIDriver, SimSPIDriver, SPIConfig
from core.grid_manager import MotorGridManager
from patterns.waveforms import WaveformGenerator
from patterns.executor import PatternExecutor
from utils.loggers import DatabaseLogger, CSVLogger
from utils.visualizer import GridVisualizer

class MotorGridController:
    """Main controller application"""
    
    def __init__(self, config_path: str = "config/grid_config.yaml", 
                 simulation_mode: bool = False):
        
        # Load configuration
        self.config = self._load_config(config_path)
        self.simulation_mode = simulation_mode
        
        # Initialize components
        self._init_components()
        
        print("\n" + "="*60)
        print("MOTOR GRID CONTROLLER")
        print("="*60)
        print(f"Grid: {self.grid.rows}x{self.grid.cols} ({self.grid.rows*self.grid.cols} motors)")
        print(f"Picos: {len(self.spi_config.cs_pins)}")
        print(f"Mode: {'SIMULATION' if simulation_mode else 'HARDWARE'}")
        print("="*60)
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _init_components(self):
        """Initialize all system components"""
        
        # SPI Configuration
        spi_cfg = self.config['spi']
        self.spi_config = SPIConfig(
            bus=spi_cfg['bus'],
            device=spi_cfg['device'],
            speed_hz=spi_cfg['speed_hz'],
            mode=spi_cfg['mode'],
            cs_pins=spi_cfg['cs_pins']
        )
        
        # Initialize SPI driver
        if self.simulation_mode:
            self.spi_driver = SimSPIDriver(self.spi_config)
        else:
            self.spi_driver = RealSPIDriver(self.spi_config)
        
        # Grid Configuration
        grid_cfg = self.config['grid']
        self.grid = MotorGridManager(
            rows=grid_cfg['rows'],
            cols=grid_cfg['cols'],
            motors_per_pico=grid_cfg['motors_per_pico']
        )
        
        # Pattern Executor
        self.executor = PatternExecutor(self.grid, self.spi_driver)
        
        # Logging
        log_cfg = self.config['logging']
        self.db_logger = DatabaseLogger(log_cfg['database_path'])
        self.csv_logger = CSVLogger()
        
        # Session ID
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def test_individual_motors(self):
        """Test individual motor control"""
        print("\n[Test] Individual Motor Control")
        
        test_points = [
            (0, 0, 0.3),   # Corner, 30%
            (3, 3, 0.7),   # Center, 70%
            (5, 5, 1.0),   # Opposite corner, 100%
        ]
        
        for x, y, intensity in test_points:
            print(f"  Motor ({x},{y}) -> {intensity*100:.0f}%")
            self.grid.set_intensity(x, y, intensity)
            
            # Send commands
            commands = self.grid.get_pico_commands()
            self.spi_driver.broadcast([commands[i] for i in sorted(commands.keys())])
            
            time.sleep(0.5)
        
        # Return to idle
        self.grid.idle_all()
        commands = self.grid.get_pico_commands()
        self.spi_driver.broadcast([commands[i] for i in sorted(commands.keys())])
        
        # Log test
        self.db_logger.log_motor_state(list(self.grid.grid.values()), self.session_id)
    
    def run_pattern_demo(self):
        """Run a demo sequence of patterns"""
        patterns = [
            ("Radial Wave", WaveformGenerator.radial_wave(2.5, 2.5, 2.0, 0.5), 6.0),
            ("Row Sweep", WaveformGenerator.row_sweep('right', 0.8), 4.0),
            ("Spiral", WaveformGenerator.spiral(2.5, 2.5, 3.0, 0.3), 8.0),
            ("Checkerboard", WaveformGenerator.checkerboard(0.5), 3.0),
        ]
        
        for name, pattern, duration in patterns:
            print(f"\n[Demo] Running '{name}' for {duration}s")
            
            stats = self.executor.execute(
                pattern_func=pattern,
                duration=duration,
                fps=20,
                pattern_name=name
            )
            
            # Log execution
            self.db_logger.log_pattern_execution(stats)
            
            # Brief pause between patterns
            time.sleep(1)
    
    def interactive_control(self):
        """Interactive command-line control"""
        print("\n[Interactive] Enter commands (type 'help' for options)")
        
        while True:
            try:
                cmd = input("\nmotor> ").strip().lower()
                
                if cmd == 'help':
                    self._print_help()
                elif cmd == 'exit':
                    break
                elif cmd.startswith('set '):
                    self._handle_set_command(cmd)
                elif cmd == 'idle':
                    self.grid.idle_all()
                    self._send_commands()
                    print("All motors set to idle")
                elif cmd == 'show':
                    self._show_grid()
                elif cmd == 'viz':
                    self._visualize_grid()
                elif cmd == 'test':
                    self.test_individual_motors()
                elif cmd == 'demo':
                    self.run_pattern_demo()
                else:
                    print(f"Unknown command: {cmd}")
                    
            except KeyboardInterrupt:
                print("\nExiting interactive mode")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def _handle_set_command(self, cmd: str):
        """Handle set commands"""
        parts = cmd.split()
        if len(parts) == 4:  # set x y intensity
            try:
                x = int(parts[1])
                y = int(parts[2])
                intensity = float(parts[3])
                
                if self.grid.set_intensity(x, y, intensity):
                    self._send_commands()
                    print(f"Set ({x},{y}) to {intensity*100:.1f}%")
                else:
                    print("Invalid coordinates or intensity")
            except ValueError:
                print("Invalid command format. Use: set x y intensity")
    
    def _send_commands(self):
        """Send current grid state to hardware"""
        commands = self.grid.get_pico_commands()
        self.spi_driver.broadcast([commands[i] for i in sorted(commands.keys())])
    
    def _show_grid(self):
        """Display current grid state"""
        grid_array = self.grid.get_grid_array('intensity')
        print("\nCurrent Grid Intensities:")
        for y in range(self.grid.rows):
            row = [f"{grid_array[y, x]:.2f}" for x in range(self.grid.cols)]
            print("  " + " ".join(row))
    
    def _visualize_grid(self):
        """Create visualization of current grid"""
        grid_array = self.grid.get_grid_array('intensity')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save visualization
        save_path = f"logs/grid_viz_{timestamp}.png"
        GridVisualizer.plot_grid(grid_array, "Current Motor Grid", save_path=save_path)
    
    def _print_help(self):
        """Print command help"""
        print("\nAvailable commands:")
        print("  set x y intensity   - Set motor at (x,y) to intensity (0.0-1.0)")
        print("  idle                - Set all motors to idle/safe")
        print("  show                - Show current grid state")
        print("  viz                 - Create visualization")
        print("  test                - Run individual motor test")
        print("  demo                - Run pattern demo")
        print("  exit                - Exit interactive mode")
        print("  help                - Show this help")
    
    def cleanup(self):
        """Cleanup resources"""
        print("\n[Cleanup] Shutting down...")
        
        # Set all motors to idle
        self.grid.idle_all()
        self._send_commands()
        
        # Close SPI driver
        self.spi_driver.close()
        
        # Close database
        self.db_logger.close()
        
        print("[Cleanup] Complete")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Motor Grid Controller")
    parser.add_argument("--simulate", action="store_true", 
                       help="Run in simulation mode (no hardware)")
    parser.add_argument("--config", default="config/grid_config.yaml",
                       help="Path to configuration file")
    
    args = parser.parse_args()
    
    # Create controller
    controller = MotorGridController(
        config_path=args.config,
        simulation_mode=args.simulate
    )
    
    try:
        # Run interactive control
        controller.interactive_control()
        
    except KeyboardInterrupt:
        print("\n\nController stopped by user")
    finally:
        # Always cleanup
        controller.cleanup()

if __name__ == "__main__":
    main()