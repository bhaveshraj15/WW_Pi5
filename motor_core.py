class MotorNode:
    """Represents a single motor in the grid."""
    def __init__(self, x, y, network_id, channel, initial_pulse=1000):
        self.grid_x = x
        self.grid_y = y
        self.network_id = network_id  # Which Pi Pico controls this motor
        self.channel = channel        # Which PWM pin on the Pico
        self.current_pulse = initial_pulse  # Current pulse width in µs (1000-2000)
        self.intensity = 0.0  # Normalized 0.0 to 1.0