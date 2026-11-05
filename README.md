# UAV Swarm Simulation System

A lightweight, high-performance, software-based **3D Unmanned Aerial Vehicle (UAV) Swarm Simulation System** built with Python, Ursina Engine (Panda3D), and NumPy.

The system simulates multiple virtual drones, synchronizes their flight movements, renders dynamic 3D mathematical formations, performs real-time proximity and collision detection, exports/imports trajectory data (JSON and CSV), and provides centralized fleet controls with both internal simulation and external MAVLink/SITL communication adapters.

---

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Running the Simulation](#running-the-simulation)
- [Controls and Keyboard Shortcuts](#controls-and-keyboard-shortcuts)
- [Mathematical Formations](#mathematical-formations)
- [Proximity and Collision Detection](#proximity-and-collision-detection)
- [Trajectory Recording & Playback](#trajectory-recording--playback)
- [MAVLink and SITL Integration](#mavlink-and-sitl-integration)
- [Running Tests](#running-tests)

---

## Features

- **High-Performance 3D Environment:** Dark slate viewport, ground reference grid on the X-Z plane, and 3D reference axes (Red: +X, Green: +Y/Altitude, Blue: +Z).
- **Multi-Drone Fleet Management:** Dynamic creation, positioning, and lifecycle coordination for any number of UAVs (default: 16).
- **Quad-rotor 3D Visuals:** Detailed drone models with rotating propeller discs, vertical altitude drop-lines, floating billboard identification labels (`D00`, `D01`...), and state-driven RGB LED indicators.
- **Color-Coded Operational States:**
  - `IDLE`: Muted Slate Gray
  - `ARMED` / `LAUNCHING`: Electric Sky Blue / Amber
  - `IN_FLIGHT`: Emerald Active Green
  - `TRANSITIONING`: Cyan
  - `LANDING`: Warm Orange
  - `LANDED`: Resting Dark Gray
  - `WARNING` / `COLLISION`: Bright Crimson Red
- **Mathematical 3D Formations:**
  1. **Line** (1D collinear along lateral axis)
  2. **V Formation** (migratory bird chevron)
  3. **Circle** (equispaced circular perimeter)
  4. **Square** (perimeter perimeter boundary)
  5. **Triangle** (equilateral delta wing)
  6. **Helix** (3D cylindrical spiral with vertical dispersion)
- **Smooth Trajectory Interpolation:** Cubic smoothstep easing ($3t^2 - 2t^3$) prevents teleportation and sudden velocity jumps during synchronized transitions.
- **Proximity & Collision Detection:**
  - Continuous pairwise distance matrix calculation via NumPy.
  - Configurable safety thresholds (Proximity warning: 2.2m, Critical collision: 1.2m).
  - Pre-transition collision prediction checks candidate paths before motion starts.
- **Integrated Dashboard HUD:** Compact, minimal UI for centralized fleet commands, formation selection, parameter steppers (speed and spacing), and real-time safety alerts.
- **Trajectory Storage and Playback:** Export and import drone keyframes (ID, timestamp, coordinates, RGB colors, states) in JSON and CSV formats with full in-simulator replay.
- **Extensible Communication Layer:** Abstracted `VehicleAdapterBase` supporting fast local in-memory simulation (`LocalSimulationAdapter`) and networked MAVLink UDP integration (`MAVLinkAdapter`).

---

## Technology Stack

- **Language:** Python 3.10+ (tested on Python 3.14)
- **3D Graphics Engine:** Ursina Engine 8.3.0 / Panda3D 1.10.16
- **Mathematical Computation:** NumPy
- **Drone Protocol:** MAVLink v2 (`pymavlink` 2.4.50) / UDP sockets
- **Data Serialization:** JSON and CSV
- **Testing Framework:** pytest 9.2.0

---

## Architecture

The system maintains a clean 3-layer architecture:

```
┌────────────────────────────────────────────────────────┐
│               3D Simulation Layer                      │
│   (Ursina Viewport, Ground Grid, Camera, Drone Visuals)│
└──────────────────────────┬─────────────────────────────┘
                           │ updates
┌──────────────────────────▼─────────────────────────────┐
│               Central Control Layer                    │
│     (SwarmManager, Formations, Trajectory, Collision)  │
└──────────────────────────┬─────────────────────────────┘
                           │ dispatches
┌──────────────────────────▼─────────────────────────────┐
│               Communication Layer                      │
│   (VehicleAdapterBase: LocalSimulation / MAVLink UDP)  │
└────────────────────────────────────────────────────────┘
```

1. **3D Simulation Layer (`uav_swarm/simulation/`):** Manages entity rendering, propeller animations, billboard labels, lighting, and camera orbit/pan/zoom.
2. **Central Control Layer (`uav_swarm/swarm/`):** Pure mathematical calculations and fleet coordination independent of graphics rendering.
3. **Communication Layer (`uav_swarm/communication/`):** Common vehicle interface decoupling autonomy communication from simulation loops.

---

## Project Structure

```text
UAV Swarm System/
├── main.py                          # Root launcher script
├── requirements.txt                 # Project dependencies
├── README.md                        # Complete documentation
│
├── uav_swarm/                       # Primary application package
│   ├── __init__.py
│   ├── config.py                    # Constants, color mapping, defaults
│   ├── main.py                      # Application entry point and arguments
│   │
│   ├── simulation/                  # 3D Ursina rendering layer
│   │   ├── __init__.py
│   │   ├── environment.py           # Ground grid, reference axes, dark theme
│   │   ├── drone.py                 # 3D quadcopter entity, propellers, labels
│   │   └── camera.py                # Orbit, pan, zoom, preset view angles
│   │
│   ├── swarm/                       # Fleet logic & mathematics
│   │   ├── __init__.py
│   │   ├── manager.py               # SwarmManager, fleet lifecycle & playback
│   │   ├── formations.py            # Line, V, Circle, Square, Triangle, Helix
│   │   ├── trajectory.py            # Cubic smoothstep trajectory interpolation
│   │   └── collision.py             # Pairwise distance & conflict prediction
│   │
│   ├── communication/               # Hardware / SITL abstraction
│   │   ├── __init__.py
│   │   ├── base.py                  # VehicleAdapterBase and telemetry container
│   │   ├── simulator_adapter.py     # High-performance in-memory simulation
│   │   └── mavlink_adapter.py       # UDP socket & pymavlink adapter
│   │
│   └── dashboard/                   # Integrated HUD
│       ├── __init__.py
│       └── controls.py              # Status banner, action buttons, steppers
│
├── data/
│   └── formations/                  # Stored JSON/CSV trajectories
│       └── sample_helix_flight.json # Pre-generated sample trajectory
│
└── tests/                           # Comprehensive test suite
    ├── __init__.py
    ├── test_formations.py           # Mathematical formation tests
    ├── test_trajectory.py           # Easing and interpolation tests
    ├── test_collision.py            # Proximity and collision tests
    ├── test_manager_and_storage.py  # Fleet lifecycle, I/O, playback tests
    ├── test_communication.py        # Adapter lifecycle and timeout tests
    └── test_simulation_entities.py  # Headless Ursina rendering tests
```

---

## Installation

1. **Clone or navigate to the workspace directory:**
   ```bash
   cd "UAV Swarm System"
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

   *(Dependencies installed: `ursina`, `numpy`, `pytest`, `pymavlink`)*

---

## Running the Simulation

### Standard Interactive Launch (Default 16 Drones):
```bash
python main.py
```

### Custom Swarm Parameters via CLI:
```bash
# Launch a swarm of 25 drones at 6.0m altitude with 3.5m spacing:
python main.py --drones 25 --altitude 6.0 --spacing 3.5 --speed 5.0

# Launch with external MAVLink UDP adapter:
python main.py --drones 8 --adapter mavlink
```

### Command-Line Arguments:
- `--drones INT`: Number of virtual drones in the swarm (default: `16`).
- `--altitude FLOAT`: Target hover altitude in meters (default: `5.0`).
- `--spacing FLOAT`: Separation spacing between formation nodes in meters (default: `3.0`).
- `--speed FLOAT`: Flight speed in meters per second (default: `4.0`).
- `--adapter {simulation,mavlink}`: Communication adapter backend (default: `simulation`).
- `--headless`: Run offscreen without opening an interactive window (useful for CI/automated testing).
- `--steps INT`: Run for a fixed number of frames and exit cleanly.

---

## Controls and Keyboard Shortcuts

### Mouse Controls:
- **Right Mouse Button (Hold & Drag):** Orbit camera around swarm center.
- **Middle Mouse Button (Hold & Drag)** or **Shift + Right Mouse Drag:** Pan camera laterally and vertically.
- **Mouse Scroll Wheel:** Zoom in and out smoothly.

### Keyboard Shortcuts:
| Key | Action |
|---|---|
| **Space** | Pause / Resume simulation |
| **L** | Launch All (arm and ascend to target altitude) |
| **K** | Land All (descend to ground coordinates) |
| **R** | Reset simulation to initial ground layout |
| **1** | Camera View: Oblique 3D Perspective (default) |
| **2** | Camera View: Top-Down Aerial View (ortho-style) |
| **3** | Camera View: Front Facing View |
| **4** | Camera View: Side Lateral View |
| **F** | Focus / Re-center camera on origin |
| **Arrow Keys** | Keyboard camera orbit |
| **Escape** | Exit simulation |

### Dashboard On-Screen Buttons:
- **[Launch All]**: Arms all drones and ascends smoothly to configured hover altitude.
- **[Land All]**: Directs drones to touch down on their respective ground coordinates.
- **[Reset]**: Instantly resets fleet positions, velocities, and statuses back to initial ground state.
- **[Pause / Resume]**: Pauses or resumes simulation time.
- **[Line], [V Formation], [Circle], [Square], [Triangle], [Helix]**: Switches formation.
- **Spacing [ - ] / [ + ]**: Adjusts formation spacing by 0.5m increments.
- **Speed [ - ] / [ + ]**: Adjusts flight velocity by 1.0 m/s increments.
- **[Save JSON] / [Save CSV]**: Exports live trajectory snapshot to `data/formations/`.
- **[Load & Replay]**: Loads latest trajectory file and replays flight path.

---

## Mathematical Formations

All formation calculations are implemented with pure NumPy in `uav_swarm/swarm/formations.py` with zero rendering engine dependencies:

1. **Line Formation:**
   $$x_i = c_x + \left(i - \frac{N - 1}{2}\right) \cdot \text{spacing},\quad y_i = \text{altitude},\quad z_i = c_z$$
2. **V Formation (Chevron):**
   Apex at lead drone ($i=0$), with left and right wing ranks swept back at $\theta = 35^\circ$:
   $$x_i = \text{side} \cdot k \cdot \text{spacing} \cdot \cos(35^\circ),\quad z_i = -k \cdot \text{spacing} \cdot \sin(35^\circ)$$
3. **Circle Formation:**
   Equispaced perimeter points with radius $R = \max\left(\text{spacing}, \frac{N \cdot \text{spacing}}{2\pi}\right)$:
   $$x_i = c_x + R \cos\left(\frac{2\pi i}{N}\right),\quad z_i = c_z + R \sin\left(\frac{2\pi i}{N}\right)$$
4. **Square Formation:**
   Perimeter boundary mapping with side length $L = \max(2 \cdot \text{spacing}, N \cdot \text{spacing} / 4)$.
5. **Triangle Formation:**
   Equilateral triangular grid organized row-by-row with forward apex ($+Z$).
6. **Helix (3D Spiral):**
   True 3D cylindrical spiral with vertical altitude dispersion over a configured span:
   $$\theta_i = \frac{4\pi i}{N},\quad x_i = c_x + R \cos(\theta_i),\quad z_i = c_z + R \sin(\theta_i),\quad y_i = y_{\text{base}} + i \cdot \frac{H}{N-1}$$

---

## Proximity and Collision Detection

The safety engine in `uav_swarm/swarm/collision.py` executes two levels of validation:

1. **Real-Time Runtime Detection:**
   On every frame, pairwise Euclidean distances are calculated:
   $$D_{ij} = \|\mathbf{p}_i - \mathbf{p}_j\|$$
   - $D_{ij} < 1.2\,\text{m}$ $\rightarrow$ **Critical Collision Alarm**: HUD displays alert and affected drones illuminate in crimson red.
   - $1.2\,\text{m} \le D_{ij} < 2.2\,\text{m}$ $\rightarrow$ **Proximity Warning**: HUD displays warning message and affected drones highlight in amber/red.
2. **Pre-Transition Trajectory Conflict Prediction:**
   Before commanding a formation change, the trajectory is sampled at 25 intermediate time steps ($t \in [0, 1]$). If any two paths cross closer than the warning distance, the dashboard alerts the operator with the specific drone IDs and the exact timeline progress where the conflict will occur.

---

## Trajectory Recording & Playback

Formation trajectories can be exported and imported in both JSON and CSV formats.

### Data Format Specification:
Each record contains:
- `drone_id`: Integer ID of the drone (`0, 1, ...`)
- `timestamp`: Epoch or relative timestamp in seconds
- `x`, `y`, `z`: 3D Cartesian coordinates in meters
- `r`, `g`, `b`: Normalized RGB color values `[0.0, 1.0]`
- `state`: String representation of drone state (e.g. `IN_FLIGHT`)

### Sample JSON Structure:
```json
{
  "formation": "Helix",
  "keyframes": [
    {
      "drone_id": 0,
      "timestamp": 1793845792.199,
      "x": -3.0,
      "y": 5.0,
      "z": -3.0,
      "r": 0.15,
      "g": 0.90,
      "b": 0.45,
      "state": "IN_FLIGHT"
    }
  ]
}
```

Files are automatically saved to `data/formations/`. Clicking **[Load & Replay]** inside the simulator automatically discovers the latest saved file and executes trajectory playback.

---

## MAVLink and SITL Integration

The communication architecture separates the simulation loop from networking adapters:

- **Local Simulation Adapter (`LocalSimulationAdapter`):** The default zero-overhead adapter executing deterministic in-memory kinematics.
- **MAVLink / SITL Adapter (`MAVLinkAdapter`):** Networked adapter that connects to external autopilot SITL instances (e.g. ArduPilot SITL or PX4 SITL) over localhost UDP ports.

### Port Allocation:
Each vehicle is addressed on a dedicated UDP port:
```text
Port = BASE_PORT + drone_id  (e.g., Drone 0: 14550, Drone 1: 14551, Drone 2: 14552 ...)
```

### SITL Setup (Optional):
To connect to an external SITL autopilot:
1. Start your SITL instance (e.g., ArduPilot SITL):
   ```bash
   sim_vehicle.py -v ArduCopter -I 0 --out udp:127.0.0.1:14550
   ```
2. Launch the UAV Swarm system with the MAVLink adapter:
   ```bash
   python main.py --adapter mavlink --drones 1
   ```
3. If no SITL instance is broadcasting, the adapter handles timeouts and network unreachability gracefully without freezing or crashing the simulator.

---

## Running Tests

The test suite thoroughly covers all mathematical formations, trajectory interpolation, collision detection, serialization, and communication adapters:

```bash
# Run the entire test suite:
pytest -v
```

### Verified Test Categories:
- `test_formations.py`: Shape, symmetry, spacing, radius, altitude, and edge cases ($N=0, 1, 16$) across all 6 formations.
- `test_trajectory.py`: Smoothstep easing mathematical properties ($3t^2 - 2t^3$), velocity bounds, and synchronized waypoint interpolation.
- `test_collision.py`: Pairwise distance matrix computation, proximity alerts, and pre-transition conflict predictions.
- `test_manager_and_storage.py`: Centralized fleet lifecycle (`launch_all`, `land_all`, `reset`), JSON/CSV export & import, and playback execution.
- `test_communication.py`: `LocalSimulationAdapter` and `MAVLinkAdapter` lifecycle, telemetry streaming, and socket timeout handling.
- `test_simulation_entities.py`: Headless Ursina 3D rendering pipeline, visual entities, and dashboard components.

---

## License

MIT License. Designed and developed for lightweight, high-performance UAV swarm simulation and research.

