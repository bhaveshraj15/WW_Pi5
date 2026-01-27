from motor_core import MotorNode

class MotorGridManager:
    """Manages the entire NxM motor grid and coordinates with hardware."""
    
    def __init__(self, rows, cols, spi_controller):
        """
        rows, cols: Dimensions of your motor grid
        spi_controller: Instance of SimSpiDriver or real SPI driver to communicate with Pico(s)
        """
        self.rows = rows
        self.cols = cols
        self.spi = spi_controller
        
        # Create motor map
        self.grid = self._create_motor_map(rows, cols)
        
        # Track which Pico controls which motors
        self.node_motors = self._organize_by_node()
        
    def _create_motor_map(self, rows, cols):
        """Initializes the grid with MotorNode objects."""
        grid = {}
        # This mapping assumes 3 Picos controlling a 6x6 grid (12 motors each)
        # MODIFY THIS based on your actual Pico-motor wiring plan
        for x in range(cols):
            for y in range(rows):
                # Example mapping: Pico 0 gets first 12 motors, Pico 1 next 12, etc.
                linear_index = y * cols + x
                node_id = linear_index // 12  # Each Pico controls 12 motors
                channel = linear_index % 12   # Which pin on the Pico
                
                grid[(x, y)] = MotorNode(x, y, node_id, channel)
        return grid
    
    def _organize_by_node(self):
        """Groups motors by their controlling Pico for efficient updates."""
        node_motors = {}
        for motor in self.grid.values():
            if motor.network_id not in node_motors:
                node_motors[motor.network_id] = []
            node_motors[motor.network_id].append(motor)
        return node_motors
    
    def set_motor_pulse(self, x, y, pulse_us):
        """Sets a specific motor's pulse width and sends update to hardware."""
        motor = self.grid[(x, y)]
        
        # Validate and update
        pulse_us = max(1000, min(2000, pulse_us))
        motor.current_pulse = pulse_us
        motor.intensity = (pulse_us - 1000) / 1000.0  # Convert to 0.0-1.0
        
        # Send update to the appropriate Pico
        self._update_node(motor.network_id)
    
    def _update_node(self, node_id):
        """Sends updated pulse values for all motors on a specific Pico."""
        if node_id not in self.node_motors:
            return
            
        # Collect current pulses for all motors on this Pico
        motor_values = []
        for motor in sorted(self.node_motors[node_id], key=lambda m: m.channel):
            motor_values.append(motor.current_pulse)
        
        # Send to hardware (or simulation)
        self.spi.send_to_node(node_id, motor_values)
    
    def set_intensity_grid(self, x, y, intensity):
        """Higher-level control: set intensity (0.0-1.0) which maps to pulse width."""
        pulse_us = 1000 + int(intensity * 1000)
        self.set_motor_pulse(x, y, pulse_us)