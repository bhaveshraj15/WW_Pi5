# Pi Pico SPI Motor Controller Firmware
# Receives commands via SPI and sets 12 PWM outputs for ESCs.
# Save as 'main.py' to run on boot[citation:2].

from machine import Pin, SPI, PWM
import time

# ============================================================================
# CONFIGURATION: ADJUST THESE FOR YOUR SETUP
# ============================================================================

# 1. SPI SETUP (Must match your Pi 5's wiring)
# ----------------------------------------------------------------
# GPIO for Chip Select (CS) - Change this for each Pico in your network.
# Example: Pico #1 uses CS pin 5, Pico #2 uses CS pin 6, etc.
MY_CS_PIN = 5

# SPI Pins for Pico (SPI0, default pins)
SPI_ID = 0          # Use SPI port 0
SPI_SCK_PIN = 2     # Clock
SPI_MOSI_PIN = 0    # Data from Main to Pico[citation:10]
SPI_MISO_PIN = 1    # Data from Pico to Main (not used here but must be defined)

# 2. MOTOR & PWM SETUP
# ----------------------------------------------------------------
NUM_MOTORS = 12  # This Pico controls 12 motors
PWM_FREQ = 50    # Standard frequency for ESCs (50Hz)[citation:2]

# Define which Pico GPIO pins are connected to your 12 ESCs.
# WARNING: Ensure these pins support PWM[citation:5][citation:7].
MOTOR_PWM_PINS = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]

# 3. ESC SAFETY LIMITS (in microseconds)
# ----------------------------------------------------------------
PULSE_MIN = 1000  # Minimum pulse (stop/idle)
PULSE_MAX = 2000  # Maximum pulse (full throttle)
PULSE_SAFE = 1000 # Safe pulse to send on error or startup

# ============================================================================
# INITIALIZATION
# ============================================================================

print(f"Initializing Motor Controller on Pico...")
print(f"  - Controls {NUM_MOTORS} motors via pins {MOTOR_PWM_PINS}")
print(f"  - ESC PWM: {PWM_FREQ}Hz, Pulse range: {PULSE_MIN}-{PULSE_MAX}us")

# Initialize PWM objects for all motors
pwms = []
for i, pin_num in enumerate(MOTOR_PWM_PINS):
    try:
        pwm = PWM(Pin(pin_num))
        pwm.freq(PWM_FREQ)
        pwm.duty_u16(0)  # Start with 0% duty cycle (off)
        pwms.append(pwm)
        print(f"    Motor {i:2d} on GPIO{pin_num:2d}: OK")
    except Exception as e:
        print(f"    ERROR initializing Motor {i} on GPIO{pin_num}: {e}")
        # If initialization fails, add None as placeholder
        pwms.append(None)

# Set all motors to the safe idle pulse on startup
def init_safe_state():
    print("Setting all motors to SAFE idle pulse.")
    set_all_motors_pulse(PULSE_SAFE)

# Initialize SPI as a peripheral (slave)
print(f"\nInitializing SPI (ID={SPI_ID}) as peripheral...")
print(f"  CS Pin: GPIO{MY_CS_PIN}")

# Configure the Chip Select (CS) pin as an input with pull-up.
# The main controller will pull this LOW to select this Pico.
cs = Pin(MY_CS_PIN, Pin.IN, Pin.PULL_UP)

# Initialize SPI in peripheral mode.
# The Pico's MISO line is defined but won't be used for sending data back.
spi = SPI(SPI_ID,
          baudrate=1000000,   # 1 MHz, match your controller
          polarity=0,         # SPI mode 0 (common)
          phase=0,
          bits=8,
          firstbit=SPI.MSB,
          sck=Pin(SPI_SCK_PIN),
          mosi=Pin(SPI_MOSI_PIN),
          miso=Pin(SPI_MISO_PIN))

print("SPI Peripheral ready. Waiting for commands...\n")

# ============================================================================
# CORE FUNCTIONS
# ============================================================================

def microseconds_to_duty(pulse_us):
    """
    Convert a pulse width in microseconds to a 16-bit PWM duty cycle[citation:2][citation:7].
    Formula: duty = (pulse_us / period_us) * 65535
    For 50Hz: period = 20,000 microseconds (1 / 50Hz).
    """
    period_us = 1_000_000 / PWM_FREQ  # 20,000 us for 50Hz
    duty = int((pulse_us / period_us) * 65535)
    # Clamp to valid 16-bit range
    return max(0, min(65535, duty))

def set_motor_pulse(motor_index, pulse_us):
    """
    Set a specific motor to a given pulse width.
    Clamps the pulse to the safe min/max range.
    """
    if motor_index < 0 or motor_index >= NUM_MOTORS:
        return False
    if pwms[motor_index] is None:
        return False

    # Clamp to valid range
    pulse_us = max(PULSE_MIN, min(PULSE_MAX, pulse_us))

    # Convert and set the duty cycle
    duty = microseconds_to_duty(pulse_us)
    pwms[motor_index].duty_u16(duty)

    return True

def set_all_motors_pulse(pulse_us):
    """Set all motors to the same pulse width."""
    pulse_us = max(PULSE_MIN, min(PULSE_MAX, pulse_us))
    for i in range(NUM_MOTORS):
        set_motor_pulse(i, pulse_us)

def decode_spi_packet(packet_bytes):
    """
    Decode the SPI packet according to our protocol.
    Expected format (25 bytes):
        Byte 0: Target Node ID
        Bytes 1-24: 12 x Motor Pulses (2 bytes each, big-endian)
    Returns: (node_id, motor_pulses_list) or (None, []) on error.
    """
    if len(packet_bytes) != 25:
        print(f"  ERROR: Packet length {len(packet_bytes)} != 25")
        return None, []

    target_node_id = packet_bytes[0]
    motor_pulses = []

    # Decode 12 motor pulses (2 bytes each, big-endian)
    for i in range(12):
        start_idx = 1 + (i * 2)
        # Combine two bytes into a 16-bit integer
        high_byte = packet_bytes[start_idx]
        low_byte = packet_bytes[start_idx + 1]
        pulse = (high_byte << 8) | low_byte
        motor_pulses.append(pulse)

    return target_node_id, motor_pulses

def process_command(target_id, motor_pulses):
    """
    Process a valid command. If the target ID matches this Pico's
    configured ID, update the motors.
    """
    # For simplicity, this Pico's ID is derived from its CS pin number.
    # Example: CS Pin 5 -> Node ID 0, CS Pin 6 -> Node ID 1, etc.
    # You can change this logic.
    my_node_id = MY_CS_PIN - 5  # Example mapping

    if target_id != my_node_id:
        # Packet is for a different Pico, ignore silently.
        return

    # Packet is for us! Update motors.
    print(f"  -> CMD for Node {target_id}: Updating {NUM_MOTORS} motors.")
    for i, pulse in enumerate(motor_pulses):
        if set_motor_pulse(i, pulse):
            # Optional: Print detailed log for debugging
            # print(f"     Motor {i}: {pulse} us")
            pass
        else:
            print(f"     ERROR setting Motor {i}")

# ============================================================================
# MAIN LOOP
# ============================================================================

# Start in safe state
init_safe_state()

# Buffer to hold incoming SPI data (25 bytes as per our protocol)
packet_buffer = bytearray(25)

print("\n=== Entering Main Command Loop ===")
print("Waiting for SPI selection on CS pin...")
print("Press Ctrl+C in Thonny to stop[citation:2].\n")

try:
    while True:
        # Wait for the Chip Select (CS) line to go LOW (active).
        # This indicates the main Pi 5 wants to talk to us.
        if cs.value() == 0:
            # Read the full SPI packet into our buffer.
            # The `readinto` method blocks until the buffer is filled.
            spi.readinto(packet_buffer)

            # Decode the received packet
            target_id, motor_pulses = decode_spi_packet(packet_buffer)

            if target_id is not None:
                # Process the command if decoding was successful
                process_command(target_id, motor_pulses)
            else:
                print("  ERROR: Failed to decode packet.")

            # Small delay to prevent overwhelming the loop
            time.sleep_ms(1)

        # Brief pause to yield control
        time.sleep_ms(1)

except KeyboardInterrupt:
    # This block runs if you stop the script in Thonny[citation:2].
    print("\n\nKeyboard interrupt detected.")

finally:
    # CRITICAL: Always return motors to safe state on exit.
    print("Returning all motors to SAFE idle pulse.")
    set_all_motors_pulse(PULSE_SAFE)
    time.sleep(0.5)

    # Clean up PWM objects
    for pwm in pwms:
        if pwm:
            pwm.deinit()
    print("PWM deinitialized. Firmware stopped.")