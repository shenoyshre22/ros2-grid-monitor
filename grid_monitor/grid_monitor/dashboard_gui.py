import sys
import threading
import tkinter as tk
from tkinter import ttk
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, String
from grid_interfaces.srv import InjectError

class DashboardGUI(Node):
    def __init__(self, root):
        super().__init__('dashboard_gui')
        self.root = root
        self.root.title("AC Power Grid Monitor Dashboard")
        self.root.geometry("700x500")
        
        # Local state storage matrices
        self.voltage_points = [0.0] * 100  # Rolling visual grid plot array
        self.current_alarm_state = "NOMINAL STATE"
        
        # ROS 2 Service Client initialization
        self.client = self.create_client(InjectError, 'inject_grid_error')
        
        # ROS 2 Subscriber setups
        self.voltage_sub = self.create_subscription(Float32, '/grid/voltage_samples', self.voltage_callback, 10)
        self.alarm_sub = self.create_subscription(String, '/grid/alarm_status', self.alarm_callback, 10)
        
        # UI Component Assembly
        self.create_widgets()
        
        # Synchronize Tkinter loop to periodically refresh UI elements
        self.root.after(50, self.update_gui_elements)

    def create_widgets(self):
        # 1. Main Oscilloscope Canvas Layout Window
        self.canvas_label = tk.Label(self.root, text="Live Voltage Oscilloscope Window (+/- 4V Scaling)", font=("Arial", 11, "bold"))
        self.canvas_label.pack(pady=5)
        
        self.canvas = tk.Canvas(self.root, width=600, height=200, bg="black")
        self.canvas.pack(pady=5)
        
        # 2. Alarm Status Indicator Block Banner
        self.status_frame = tk.Frame(self.root, bd=2, relief="ridge")
        self.status_frame.pack(fill="x", padx=20, pady=10)
        
        self.status_title = tk.Label(self.status_frame, text="SYSTEM SECURITY STATE:", font=("Arial", 10, "bold"))
        self.status_title.pack(side="left", padx=5, pady=5)
        
        self.status_label = tk.Label(self.status_frame, text="INITIALIZING", font=("Arial", 11, "bold"), fg="blue")
        self.status_label.pack(side="left", padx=5, pady=5)
        
        # 3. Error Injection Control Center (The Knob / Slider)
        self.control_frame = tk.LabelFrame(self.root, text="Grid Degradation Control Panel", font=("Arial", 10, "bold"), padx=10, pady=10)
        self.control_frame.pack(fill="x", padx=20, pady=10)
        
        self.slider_label = tk.Label(self.control_frame, text="Inject Error Drop Percentage (%):", font=("Arial", 9))
        self.slider_label.pack(anchor="w")
        
        self.error_slider = ttk.Scale(self.control_frame, from_=0.0, to=50.0, orient="horizontal", command=self.on_slider_move)
        self.error_slider.set(0.0)
        self.error_slider.pack(fill="x", expand=True, pady=5)
        
        self.value_display = tk.Label(self.control_frame, text="Current Injection Target: 0.0%", font=("Arial", 9, "italic"), fg="purple")
        self.value_display.pack(anchor="e")

    def voltage_callback(self, msg):
        # Update our graphical point arrays sequentially
        self.voltage_points.append(msg.data)
        if len(self.voltage_points) > 100:
            self.voltage_points.pop(0)

    def alarm_callback(self, msg):
        self.current_alarm_state = msg.data

    def on_slider_move(self, value):
        parsed_val = float(value)
        self.value_display.config(text=f"Current Injection Target: {parsed_val:.1f}%")
        
        # Avoid blocking UI threads; fire and forget service request calls asynchronously
        if self.client.service_is_ready():
            req = InjectError.Request()
            req.error_percentage = parsed_val
            self.client.call_async(req)

    def update_gui_elements(self):
        # Draw the live oscilloscope canvas trace line
        self.canvas.delete("all")
        
        # Draw zero voltage baseline axis reference indicators
        self.canvas.create_line(0, 100, 600, 100, fill="#333333", dash=(4, 4))
        
        # Plot continuous sequence arrays mapping incoming samples
        points_count = len(self.voltage_points)
        if points_count > 1:
            dx = 600 / (points_count - 1)
            for i in range(points_count - 1):
                x1 = i * dx
                # Map -4V to +4V into canvas height boundaries (200px)
                y1 = 100 - (self.voltage_points[i] * 22)  
                x2 = (i + 1) * dx
                y2 = 100 - (self.voltage_points[i+1] * 22)
                
                # Dynamic wire line color shifts based on grid state
                line_color = "#00FF00" if "CRITICAL" not in self.current_alarm_state else "#FF0000"
                self.canvas.create_line(x1, y1, x2, y2, fill=line_color, width=2)
        
        # Refresh the UI alarm system banner color rules
        if "CRITICAL" in self.current_alarm_state:
            self.status_label.config(text=self.current_alarm_state, fg="white", bg="red")
            self.status_frame.config(bg="red")
        else:
            self.status_label.config(text="GRID HEALTHY - NOMINAL OPERATIONS", fg="green", bg=self.root.cget('bg'))
            self.status_frame.config(bg=self.root.cget('bg'))
            
        # Keep loop cycling every 50ms
        self.root.after(50, self.update_gui_elements)

def ros_spin_thread(node):
    rclpy.spin(node)

def main(args=None):
    rclpy.init(args=args)
    root = tk.Tk()
    node = DashboardGUI(root)
    
    # Run the background tracking interface loops on a separate thread to keep UI interactive
    thread = threading.Thread(target=ros_spin_thread, args=(node,), daemon=True)
    thread.start()
    
    # Hand control over completely to the main UI frame
    root.mainloop()
    
    # Clean up operations when user exits window interface frames
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()