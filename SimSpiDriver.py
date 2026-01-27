# --- SIMULATION DRIVER (NO HARDWARE) --
class SimSpiDriver():
    """Software-only driver for testing. Logs to console."""
    def __init__(self):
        self.virtual_motor_state = {}
        
    def send_to_node(self, node_id, motor_values):
        # 1. Store state in memory
        self.virtual_motor_state[node_id] = motor_values.copy()
        
        # 2. Print to console (instead of real hardware)
        print(f"[SIM] Packet to Node {node_id}: {motor_values}")
        
    def get_node_state(self, node_id):
        return self.virtual_motor_state.get(node_id, [1000]*12)