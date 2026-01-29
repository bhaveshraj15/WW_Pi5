# hardware/spi_driver.py
import struct
import time
import RPi.GPIO as GPIO
from dataclasses import dataclass
from typing import List, Optional
import yaml

@dataclass
class SPIConfig:
    bus: int = 0
    device: int = 0
    speed_hz: int = 1000000
    mode: int = 0
    cs_pins: List[int] = None
    
    def __post_init__(self):
        if self.cs_pins is None:
            self.cs_pins = [8, 7, 22]  # Default CS pins

class RealSPIDriver:
    """Real SPI hardware driver for Raspberry Pi 5"""
    
    def __init__(self, config: SPIConfig):
        self.config = config
        self.cs_pins = config.cs_pins
        
        # Initialize GPIO for Chip Select
        GPIO.setmode(GPIO.BCM)
        for pin in self.cs_pins:
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.HIGH)
        
        # Initialize SPI
        import spidev
        self.spi = spidev.SpiDev()
        self.spi.open(config.bus, config.device)
        self.spi.max_speed_hz = config.speed_hz
        self.spi.mode = config.mode
        
        print(f"[SPI] Initialized on bus {config.bus}, device {config.device}")
        print(f"[SPI] CS pins: {self.cs_pins}")
    
    def send_to_pico(self, pico_id: int, motor_pulses: List[int]) -> bool:
        """
        Send motor commands to a specific Pico
        Packet format: [pico_id] + [12 x 2-byte pulses]
        """
        if pico_id >= len(self.cs_pins):
            print(f"[SPI] Invalid Pico ID: {pico_id}")
            return False
        
        if len(motor_pulses) != 12:
            print(f"[SPI] Expected 12 motors, got {len(motor_pulses)}")
            return False
        
        # Create packet
        packet = bytearray()
        packet.append(pico_id)  # Target Pico ID
        
        for pulse in motor_pulses:
            # Convert to 2 bytes, big-endian
            packet.extend(struct.pack('>H', pulse))
        
        # Select Pico
        GPIO.output(self.cs_pins[pico_id], GPIO.LOW)
        
        try:
            # Send packet
            self.spi.xfer2(packet)
            return True
        except Exception as e:
            print(f"[SPI] Send error: {e}")
            return False
        finally:
            # Deselect Pico
            GPIO.output(self.cs_pins[pico_id], GPIO.HIGH)
    
    def broadcast(self, motor_pulses: List[List[int]]) -> bool:
        """Send commands to all Picos sequentially"""
        success = True
        for pico_id, pulses in enumerate(motor_pulses):
            if not self.send_to_pico(pico_id, pulses):
                success = False
        return success
    
    def close(self):
        """Cleanup resources"""
        for pin in self.cs_pins:
            GPIO.output(pin, GPIO.HIGH)
        self.spi.close()
        GPIO.cleanup()
        print("[SPI] Driver closed")

class SimSPIDriver:
    """Simulation driver for testing without hardware"""
    
    def __init__(self, config: SPIConfig):
        self.config = config
        self.cs_pins = config.cs_pins
        self.packet_log = []
        
        # Simulated Pico states
        self.pico_states = {i: [1000]*12 for i in range(len(config.cs_pins))}
        
        print(f"[SIM-SPI] Initialized with {len(config.cs_pins)} simulated Picos")
    
    def send_to_pico(self, pico_id: int, motor_pulses: List[int]) -> bool:
        """Simulate sending to Pico"""
        if pico_id >= len(self.cs_pins):
            return False
        
        # Log packet
        packet = {
            'timestamp': time.time(),
            'pico_id': pico_id,
            'pulses': motor_pulses.copy(),
            'hex': self._packet_to_hex(pico_id, motor_pulses)
        }
        self.packet_log.append(packet)
        
        # Update simulated state
        self.pico_states[pico_id] = motor_pulses.copy()
        
        print(f"[SIM-SPI] → Pico{pico_id}: {motor_pulses}")
        return True
    
    def _packet_to_hex(self, pico_id: int, pulses: List[int]) -> str:
        """Convert packet to hex string for logging"""
        packet = bytearray()
        packet.append(pico_id)
        for pulse in pulses:
            packet.extend(struct.pack('>H', pulse))
        return packet.hex()
    
    def broadcast(self, motor_pulses: List[List[int]]) -> bool:
        """Simulate broadcast to all Picos"""
        for pico_id, pulses in enumerate(motor_pulses):
            self.send_to_pico(pico_id, pulses)
        return True
    
    def get_pico_state(self, pico_id: int) -> List[int]:
        """Get simulated Pico state"""
        return self.pico_states.get(pico_id, [1000]*12)
    
    def close(self):
        """Cleanup simulation"""
        print("[SIM-SPI] Driver closed")