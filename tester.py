"""
Raspberry Pi 5 Single Motor Test with libgpiod
Controls one ESC via PWM signal on a specified GPIO pin.
"""

import gpiod
import time
import sys

class SingleMotorTester:
    def __init__(self, gpio_pin=17, pwm_freq=50):
        """
        Initialize motor controller for Raspberry Pi 5
        
        Args:
            gpio_pin: BCM pin number (not physical pin)
            pwm_freq: PWM frequency in Hz (50Hz for ESCs)
        """
        self.gpio_pin = gpio_pin
        self.pwm_freq = pwm_freq
        self.period_ns = int(1_000_000_000 / pwm_freq)  # Period in nanoseconds
        
        # Pi 5 uses gpiochip4
        self.chip = gpiod.Chip('gpiochip4', gpiod.Chip.OPEN_BY_NAME)
        
        # Request the GPIO line
        self.line = self.chip.get_line(gpio_pin)
        config = gpiod.line_request()
        config.consumer = "motor_pwm"
        config.request_type = gpiod.line_request.DIRECTION_OUTPUT
        self.line.request(config)
        
        # ESC pulse width limits (in microseconds)
        self.MIN_PULSE = 1000    # µs - stop/idle
        self.MAX_PULSE = 2000    # µs - full throttle
        self.NEUTRAL = 1500      # µs - neutral position
        
        print(f"Motor tester initialized on GPIO {gpio_pin}")
        print(f"PWM Frequency: {pwm_freq}Hz, Period: {self.period_ns/1_000_000:.2f}ms")
    
    def set_pulse_width(self, pulse_us):
        """
        Core function: Generate PWM pulse with specified width
        
        Args:
            pulse_us: Pulse width in microseconds (1000-2000)
        """
        # Validate and clamp pulse width
        pulse_us = max(self.MIN_PULSE, min(pulse_us, self.MAX_PULSE))
        
        # Convert microseconds to nanoseconds
        pulse_ns = int(pulse_us * 1000)
        
        # Generate one PWM pulse
        self.line.set_value(1)
        time.sleep(pulse_ns / 1_000_000_000)  # Convert ns to seconds
        self.line.set_value(0)
        
        # Wait for the rest of the period
        wait_ns = self.period_ns - pulse_ns
        if wait_ns > 0:
            time.sleep(wait_ns / 1_000_000_000)
        
        return pulse_us
    
    def set_pulse_continuous(self, pulse_us, duration_sec=1.0):
        """
        Send continuous PWM pulses for a specified duration
        
        Args:
            pulse_us: Pulse width in microseconds
            duration_sec: How long to send pulses
        """
        end_time = time.time() + duration_sec
        pulse_count = 0
        
        print(f"Sending {pulse_us}µs pulses for {duration_sec} seconds...")
        
        while time.time() < end_time:
            actual_pulse = self.set_pulse_width(pulse_us)
            pulse_count += 1
            
            # Print progress every 50 pulses
            if pulse_count % 50 == 0:
                elapsed = duration_sec - (end_time - time.time())
                print(f"  Progress: {elapsed:.1f}s | Pulses: {pulse_count}")
        
        print(f"Completed: {pulse_count} pulses sent")
        return pulse_count
    
    def cleanup(self):
        """Clean up GPIO resources"""
        print("\nCleaning up GPIO...")
        self.line.set_value(0)
        self.line.release()
        self.chip.close()
        print("GPIO resources released.")

def main():
    """Main test function"""
    # Configuration - change GPIO pin as needed
    TEST_GPIO_PIN = 17  # BCM pin 17 (physical pin 11)
    
    tester = None
    
    try:
        # Initialize tester
        tester = SingleMotorTester(gpio_pin=TEST_GPIO_PIN)
        
        # Uncomment the test you want to run:
        
        # 1. Basic calibration (do this first with new ESCs)
        # tester.calibration_sequence()
        
        # 2. Simple throttle test
        print("\n=== BASIC THROTTLE TEST ===")
        tester.set_pulse_continuous(1000, 1.0)   # Idle
        tester.set_pulse_continuous(1500, 2.0)   # 50% throttle
        tester.set_pulse_continuous(1000, 1.0)   # Back to idle
        
        # 3. Smooth sweep (optional)
        # tester.smooth_sweep_test(1000, 1800, 10, 0.02)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if tester:
            tester.cleanup()
        print("\nTest complete!")

if __name__ == "__main__":
    main()