# patterns/executor.py
import time
from typing import Callable, Dict, List
from datetime import datetime

class PatternExecutor:
    """Executes patterns on the motor grid"""
    
    def __init__(self, grid_manager, spi_driver):
        self.grid = grid_manager
        self.spi = spi_driver
        self.is_running = False
        self.current_pattern = None
        self.execution_log = []
    
    def execute(self, pattern_func: Callable, duration: float = 5.0, 
                fps: int = 30, pattern_name: str = "unknown") -> Dict:
        """
        Execute a pattern function over time
        Returns execution statistics
        """
        print(f"\n[Pattern] Starting '{pattern_name}' for {duration}s at {fps}fps")
        
        self.is_running = True
        self.current_pattern = pattern_name
        
        start_time = time.time()
        frame_count = 0
        frame_delay = 1.0 / fps
        
        stats = {
            'pattern_name': pattern_name,
            'start_time': datetime.now().isoformat(),
            'target_duration': duration,
            'target_fps': fps,
            'frames_executed': 0,
            'actual_fps': 0.0,
            'spi_errors': 0
        }
        
        try:
            while time.time() - start_time < duration and self.is_running:
                frame_start = time.time()
                current_time = time.time() - start_time
                frame_count += 1
                
                # Update all motors in grid
                updates = 0
                for (x, y), motor in self.grid.grid.items():
                    intensity = pattern_func(x, y, current_time)
                    if self.grid.set_intensity(x, y, intensity):
                        updates += 1
                
                # Send commands to hardware
                commands = self.grid.get_pico_commands()
                spi_success = self.spi.broadcast([commands[i] for i in sorted(commands.keys())])
                
                if not spi_success:
                    stats['spi_errors'] += 1
                
                # Log frame execution
                frame_time = time.time() - frame_start
                self.execution_log.append({
                    'frame': frame_count,
                    'timestamp': datetime.now().isoformat(),
                    'pattern_time': current_time,
                    'updates': updates,
                    'frame_duration': frame_time,
                    'spi_success': spi_success
                })
                
                # Maintain frame rate
                elapsed = time.time() - frame_start
                if elapsed < frame_delay:
                    time.sleep(frame_delay - elapsed)
            
        except KeyboardInterrupt:
            print("\n[Pattern] Interrupted by user")
        finally:
            self.is_running = False
        
        # Calculate statistics
        actual_duration = time.time() - start_time
        stats['end_time'] = datetime.now().isoformat()
        stats['actual_duration'] = actual_duration
        stats['frames_executed'] = frame_count
        stats['actual_fps'] = frame_count / actual_duration if actual_duration > 0 else 0
        
        print(f"[Pattern] '{pattern_name}' completed:")
        print(f"  Frames: {frame_count}, Duration: {actual_duration:.2f}s")
        print(f"  Target FPS: {fps}, Actual FPS: {stats['actual_fps']:.1f}")
        print(f"  SPI Errors: {stats['spi_errors']}")
        
        return stats
    
    def stop(self):
        """Stop pattern execution"""
        self.is_running = False
        print("[Pattern] Stopping execution")
    
    def get_execution_log(self) -> List[Dict]:
        """Get detailed execution log"""
        return self.execution_log.copy()