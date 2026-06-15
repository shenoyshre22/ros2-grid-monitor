import rcl_interfaces
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String
from grid_interfaces.srv import InjectError
import math
import time

class VoltageSimulator(Node):
    def __init__(self):
        super().__init__('voltage_simulator')
        
        # Publishers
        self.voltage_pub = self.create_publisher(Float32, '/grid/voltage_samples', 10)
        self.alarm_pub = self.create_publisher(String, '/grid/alarm_status', 10)
        
        # Service Server for Error Injection
        self.srv = self.create_service(InjectError, 'inject_grid_error', self.handle_error_injection)
        
        # Grid parameters
        self.frequency = 50.0  # 50 Hz
        self.base_peak_voltage = 4.0  # Stepped down from 230V to 4V
        self.error_factor = 1.0  # 1.0 means 100% nominal grid voltage
        
        # Sampling configuration
        # 50 Hz means 1 cycle = 0.02 seconds. We sample at 1000 Hz (20 samples per cycle)
        self.sampling_period = 0.001  
        self.start_time = time.time()
        
        # Running Data structures
        self.current_cycle_peak = 0.0
        self.peak_history = []
        self.sample_count_in_cycle = 0
        self.samples_per_cycle = 20
        
        # Create execution processing loop
        self.timer = self.create_timer(self.sampling_period, self.process_voltage_sample)
        self.get_logger().info("Voltage Simulator with 200-Peak Running Average initialized.")

    def handle_error_injection(self, request, response):
        # Calculate degradation scale. e.g., 15% error reduces nominal supply multiplier to 0.85
        percentage = request.error_percentage
        if 0.0 <= percentage <= 100.0:
            self.error_factor = (100.0 - percentage) / 100.0
            response.success = True
            response.message = f"Injected drop of {percentage}%. Voltage multiplier set to {self.error_factor:.2f}"
            self.get_logger().warn(response.message)
        else:
            response.success = False
            response.message = "Invalid error range. Must be between 0 and 100."
        return response

    def process_voltage_sample(self):
        elapsed_time = time.time() - self.start_time
        
        # Apply the error factor dynamically to simulate grid drops
        current_peak_target = self.base_peak_voltage * self.error_factor
        
        # Generate baseline sine wave: V(t) = V_peak * sin(2 * pi * f * t)
        raw_sample = current_peak_target * math.sin(2 * math.pi * self.frequency * elapsed_time)
        
        # Broadcast the raw raw voltage sample for the GUI visualizer
        msg = Float32()
        msg.data = raw_sample
        self.voltage_pub.publish(msg)
        
        # Track peak value within the current single sinusoidal oscillation cycle
        abs_sample = abs(raw_sample)
        if abs_sample > self.current_cycle_peak:
            self.current_cycle_peak = abs_sample
            
        self.sample_count_in_cycle += 1
        
        # Once an entire cycle finishes processing, push the peak value to our window
        if self.sample_count_in_cycle >= self.samples_per_cycle:
            self.peak_history.append(self.current_cycle_peak)
            
            # Maintain strict window limits (Limit history to the last 200 recorded peaks)
            if len(self.peak_history) > 200:
                self.peak_history.pop(0)
                
            # Compute the moving running average across the peak window buffer
            running_avg_peak = sum(self.peak_history) / len(self.peak_history)
            
            # Threshold evaluation check: Critical Limit = 4.0V - 10% = 3.6V
            alarm_msg = String()
            if running_avg_peak < 3.6:
                alarm_msg.data = f"CRITICAL ALARM: Grid brownout detected! Running Avg Peak: {running_avg_peak:.2f}V (Below 10% safety limit)"
                self.alarm_pub.publish(alarm_msg)
                self.get_logger().error(alarm_msg.data)
            else:
                alarm_msg.data = "NOMINAL STATE"
                self.alarm_pub.publish(alarm_msg)
            
            # Reset single cycle counters
            self.current_cycle_peak = 0.0
            self.sample_count_in_cycle = 0

def main(args=None):
    rclpy.init(args=args)
    node = VoltageSimulator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()