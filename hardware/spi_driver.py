# hardware/spi_driver.py
import struct
import time
import spidev 
import gpiod
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
    """Real SPI hardware driver for Raspberry Pi 5 using libgpiod"""
    
    def __init__(self, config: SPIConfig):
        self.config = config
        self.cs_pins = config.cs_pins
        
        # CHANGED: Initialize libgpiod for Chip Select lines
        # Open the GPIO chip. 'gpiochip4' is for the Pi 5's main header[citation:4][citation:5].
        self.gpio_chip = gpiod.Chip('gpiochip4')
        
        # Create and store line objects for each CS pin, set as outputs
        self.cs_lines = []
        for pin in self.cs_pins:
            line = self.gpio_chip.get_line(pin)
            # Request line for output, with a consumer label for debugging
            line.request(consumer=f"SPI_CS_{pin}", type=gpiod.LINE_REQ_DIR_OUT, default_val=1) # Start HIGH (deselected)
            self.cs_lines.append(line)
        
        # Initialize SPI (UNCHANGED from your original code)
        self.spi = spidev.SpiDev()
        self.spi.open(config.bus, config.device)
        self.spi.max_speed_hz = config.speed_hz
        self.spi.mode = config.mode
        
        print(f"[SPI] Initialized on bus {config.bus}, device {config.device}")
        print(f"[SPI] CS pins via libgpiod: {self.cs_pins}")
    
    def send_to_pico(self, pico_id: int, motor_pulses: List[int]) -> bool:
        if pico_id >= len(self.cs_lines):
            print(f"[SPI] Invalid Pico ID: {pico_id}")
            return False
        
        if len(motor_pulses) != 12:
            print(f"[SPI] Expected 12 motors, got {len(motor_pulses)}")
            return False
        
        # Create packet (UNCHANGED)
        packet = bytearray()
        packet.append(pico_id)
        for pulse in motor_pulses:
            packet.extend(struct.pack('>H', pulse))
        
        # Select Pico using libgpiod
        self.cs_lines[pico_id].set_value(0)  # CHANGED: Use set_value(0) for LOW
        
        try:
            # Send packet (UNCHANGED)
            self.spi.xfer2(packet)
            return True
        except Exception as e:
            print(f"[SPI] Send error: {e}")
            return False
        finally:
            # Deselect Pico using libgpiod
            self.cs_lines[pico_id].set_value(1)  # CHANGED: Use set_value(1) for HIGH
    
    def close(self):
        """Cleanup resources"""
        # Deselect all CS lines
        for line in self.cs_lines:
            line.set_value(1)
            line.release()  # CHANGED: Release GPIO line
        self.gpio_chip.close()  # CHANGED: Close the gpiod chip
        self.spi.close()
        print("[SPI] Driver closed (libgpiod cleanup done)")

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