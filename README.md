# ROS 2 AC Power Grid Brownout Monitor and Visualizer

An industrial simulation architecture that models an AC power-grid brownout monitoring system. It scales down a 230V mains supply to a safe 4V instrumentation level, processes a 200-peak rolling window average to filter transient noise, and exposes a real-time Tkinter GUI dashboard with an integrated error-injection control panel.

---

## 1. Core Engineering Concepts and Mathematical Background

### The Hardware Instrumentation Scaling (230V to 4V)
In physical electrical distribution systems, monitoring a high-voltage 230V AC line directly with microcontroller pins or computer processing layers will destroy the instrumentation hardware. To safely observe the line state:
* A physical step-down step-transformer scales the alternating signal down to a proportional plus or minus 4V range.
* When the mains power supply is at its healthy, nominal level (230V), the scaled simulation wave operates at an ideal Peak Voltage of exactly 4.0V.

### Establishing the 10% Drop Safety Threshold
The system is safety-bounded to flag an emergency alert if the grid voltage degrades past a 10% limit. The threshold calculation is derived directly from the ideal instrumented baseline:

10% Voltage Drop Margin = 4.0V * 0.10 = 0.4V
Critical Safety Threshold = 4.0V - 0.4V = 3.6V

* Nominal Safe Zone: Any computed average peak voltage >= 3.6V.
* Critical Danger Zone: Any computed average peak voltage < 3.6V (triggers immediate system alarms).

### Signal Processing: 200-Peak Rolling Moving Average
Transient line noise, inductive motor kicks, or brief sub-second grid spikes can cause temporary voltage drops. If the alarm responded instantly to a single sample, it would cause constant false alarms in industrial settings. To avoid this, a moving window filter collects data over time before making a decision.

#### 1. Tracking Individual Oscillation Peaks
The grid frequency operates at 50 Hz (50 full sine wave cycles per second). 
* The duration of one single complete wave cycle is exactly:
  Period (T) = 1 / 50 Hz = 0.02 seconds
* Within this 0.02-second window, the simulator reads 20 discrete samples. The system monitors these samples, isolates the absolute highest magnitude value to establish that cycle's peak, and discards the standard intermediate points.

#### 2. The 4-Second Rolling Window Buffer
Once a cycle finishes, its isolated peak is appended to a history buffer limited to a maximum length of 200 peaks.
* At 50 cycles per second, filling this 200-peak list requires exactly:
  Window Horizon = 200 peaks / 50 cycles/sec = 4.0 seconds
* When peak number 201 arrives, the oldest historical peak (index 0) is dropped. Every cycle, the node computes the running average:
  Running Average Peak = (Sum of all 200 current peaks) / 200
If this running average falls below 3.6V, the alarm triggers.

### The Electrical Danger of a Brownout (Why the Alarm Matters)
A brownout is a severe drop in grid voltage while the circuit remains powered. It is distinct from a blackout (total power loss). The name comes from incandescent bulbs turning a dim, brownish-yellow as voltage drops.

For inductive equipment (like refrigerators, cooling compressors, and industrial pumps), a brownout is highly destructive. These systems require a fixed amount of continuous Electrical Power (P) to drive their mechanical loads. Electrical power is defined by:

P = V * I

Where V is Voltage and I is Current (Amperes). If the line voltage drops substantially (e.g., down to a simulated 2V / real-world 115V):
1. The electric motor continues to demand the same total Power (P) to keep turning.
2. Because Voltage (V) dropped, the Current (I) drawn from the line must dramatically spike to compensate.
3. Electrical heat generation inside copper motor coils scales with the square of the current:
   Heat Generated is proportional to I^2
4. This current spike causes rapid overheating, melting wire insulation, shorting components, and burning out the machinery.

---

## 2. Step-by-Step Package Workspace Assembly

Custom interfaces containing .srv definitions must be compiled within a CMake build pipeline (ament_cmake). Once compiled, they can be imported into Python packages (ament_python) containing your core execution logic.

### STEP A: Build the Interface Package (grid_interfaces)
Open your terminal and initialize the interface structures:
```bash
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_cmake grid_interfaces
mkdir -p grid_interfaces/srv
touch grid_interfaces/srv/InjectError.srv
```

### STEP B: Build the Core Control Package (grid_monitor)
Create the Python-based execution package linked to your newly defined interfaces:
```bash
cd ~/ros2_ws/src
ros2 pkg create --build-type ament_python grid_monitor --dependencies rclpy std_msgs grid_interfaces
touch grid_monitor/grid_monitor/voltage_simulator.py
touch grid_monitor/grid_monitor/dashboard_gui.py
```

### STEP C: Make other necessary file changes
make sure to change setup.py ,CMakeLists.txt and package.xml in both ``` grid_interfaces/package.xml ```  and in ```grid_monitor/package.xml```


### STEP D: run in two separarte terminals:
make sure to run ```~/ros2_ws/install/setup.bash``` inside every single new terminal tab you open before typing the launch commands below.
in Terminal 1:
```bash 
source ~/ros2_ws/install/setup.bash
ros2 run grid_monitor voltage_simulator
```

in a new terminal , Terminal 2:
```bash
source ~/ros2_ws/install/setup.bash
ros2 run grid_monitor dashboard_gui
```


### OUTPUTS:
first case: Case 1 (Healthy State - Green Waveform):
  <img width="1845" height="534" alt="image" src="https://github.com/user-attachments/assets/1f086228-69a5-40df-9909-4161f958fbb0" />

    Explanation: The system displays a stable green sine wave because the injected error drop is at 9.2%, which keeps the voltage within the allowed operating parameters.

    Why: Since 9.2% degradation is below the 10% critical threshold, the running average peak remains above 3.6V, maintaining a nominal system state and keeping the alarm silent.
  


Case 2 (Alarm State - Red Waveform):
    <img width="1845" height="534" alt="image" src="https://github.com/user-attachments/assets/ddb199cf-148b-4b85-a4ea-8a49aa88d204" />

    Explanation: The dashboard flashes a bright red waveform and throws a critical warning because a 17.2% grid error has been injected into the simulation pipeline.

    Why: A drop of 17.2% drags the nominal voltage down significantly, causing the 200-peak rolling window average to fall to 3.31V (below the strict 3.6V safety boundary), which immediately triggers the brownout alert.
    



