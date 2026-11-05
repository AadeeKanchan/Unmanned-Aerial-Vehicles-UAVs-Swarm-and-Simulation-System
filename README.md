# 🛸 Unmanned Aerial Vehicles (UAVs) Swarm and Simulation System 🛩️

A lightweight, high-performance, software-based **3D Unmanned Aerial Vehicle (UAV) Swarm Simulation System** built with Python, Ursina Engine (Panda3D), and NumPy.

This system bypasses the need for expensive physical hardware by building a pure-software virtual sandbox for testing distributed robotics, autonomous fleet coordination, dynamic 3D formations, real-time proximity safety, and complex spatial drone shows.

---

## 📌 Project Overview

Developing a physical drone swarm introduces steep barriers to entry: high hardware costs, complex electronics troubleshooting, risk of catastrophic crashes, and strict airspace regulatory frameworks.

This repository provides a **purely software-driven approach** to multi-UAV orchestration. By utilizing a **centralized command broadcast architecture**, the system treats the fleet as a single synchronized distributed network. The software scales from a few drones up to large fleets, executing smooth, mathematical transitions between complex 3D shapes without physical hardware limitations.

External SITL (Software In The Loop) autonomy stacks (e.g., ArduPilot SITL / PX4 SITL) are supported through an isolated MAVLink UDP communication adapter.

---

## 🏗️ System Architecture

The project is built around a decoupled, three-tier architecture running completely inside a local environment:

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

1. **3D Simulation Layer (`uav_swarm/simulation/`):**
   - [`environment.py`](uav_swarm/simulation/environment.py): Minimal dark slate viewport (`(0.07, 0.08, 0.10)`), X-Z horizontal ground grid, and 3D reference axes (Red: $+X$, Green: $+Y$/Altitude, Blue: $+Z$).
   - [`drone.py`](uav_swarm/simulation/drone.py): Quadcopter 3D visual models with counter-rotating propeller discs, vertical altitude drop-lines, floating billboard identification labels (`D00`, `D01`...), and state-driven RGB LED indicators.
   - [`camera.py`](uav_swarm/simulation/camera.py): Orbit (right-mouse drag), pan (middle-mouse / shift+drag), zoom (scroll wheel), and preset views (`1`: 3D Oblique, `2`: Top-down, `3`: Front, `4`: Side, `F`: Focus).

2. **Central Control Layer (`uav_swarm/swarm/`):**
   - [`manager.py`](uav_swarm/swarm/manager.py): [`SwarmManager`](uav_swarm/swarm/manager.py) coordinates fleet lifecycle (`launch_all`, `land_all`, `reset_simulation`, `change_formation`, `toggle_pause`), and trajectory I/O and replay.
   - [`formations.py`](uav_swarm/swarm/formations.py): Pure NumPy mathematical formation generators (Line, V-Formation, Circle, Square, Triangle, Helix).
   - [`trajectory.py`](uav_swarm/swarm/trajectory.py): Cubic smoothstep easing ($3t^2 - 2t^3$) for synchronized acceleration/deceleration without teleportation or velocity jumps.
   - [`collision.py`](uav_swarm/swarm/collision.py): Pairwise distance matrix calculation, proximity warnings ($< 2.2\,\text{m}$), critical collision alerts ($< 1.2\,\text{m}$), and pre-transition trajectory conflict prediction.

3. **Communication Layer (`uav_swarm/communication/`):**
   - [`base.py`](uav_swarm/communication/base.py): Unified [`VehicleAdapterBase`](uav_swarm/communication/base.py) abstract interface and [`VehicleTelemetry`](uav_swarm/communication/base.py) container.
   - [`simulator_adapter.py`](uav_swarm/communication/simulator_adapter.py): Fast in-memory simulation adapter for deterministic local execution.
   - [`mavlink_adapter.py`](uav_swarm/communication/mavlink_adapter.py): Networked MAVLink/SITL UDP adapter with per-drone port mapping (`14550 + drone_id`), non-blocking I/O, and graceful timeout handling.

4. **Integrated Dashboard HUD (`uav_swarm/dashboard/controls.py`):**
   - Fleet summary header: Total, active, and connected drone counters, current formation, and live proximity safety status.
   - Action controls: `[Launch All]`, `[Land All]`, `[Reset]`, `[Pause/Resume]`.
   - Formation selectors: `[Line]`, `[V Formation]`, `[Circle]`, `[Square]`, `[Triangle]`, `[Helix]`.
   - Steppers: Spacing ($\pm 0.5\,\text{m}$) and Speed ($\pm 1.0\,\text{m/s}$).
   - Trajectory storage: `[Save JSON]`, `[Save CSV]`, and `[Load & Replay]`.

---

## ⚡ Key Features & Capabilities

- **One-Click Fleet Synchronization:** Centralized command dispatching that arms, launches, and lands an entire fleet concurrently with smooth transitions.
- **Dynamic 3D Drone Visuals:** Quadcopter bodies with spinning rotor blades, altitude ground drop-lines, billboard identification labels (`D00`, `D01`...), and state-driven RGB LED indicators.
- **Color-Coded Operational States:**
  - `IDLE`: Soft Slate Gray
  - `ARMED` / `LAUNCHING`: Electric Sky Blue / Amber
  - `IN_FLIGHT`: Emerald Active Green
  - `TRANSITIONING`: Cyan
  - `LANDING`: Warm Orange
  - `LANDED`: Resting Dark Gray
  - `WARNING` / `COLLISION`: Bright Crimson Red
- **Mathematical 3D Formations:**
  1. **Line** (collinear along lateral X axis)
  2. **V Formation** (migratory bird chevron with swept wings)
  3. **Circle** (equispaced perimeter ring)
  4. **Square** (perimeter boundary layout)
  5. **Triangle** (equilateral delta wing structure)
  6. **Helix** (3D cylindrical spiral with vertical altitude dispersion)
- **Smooth Trajectory Interpolation:** Cubic smoothstep easing ($3t^2 - 2t^3$) prevents teleportation and sudden velocity jumps during synchronized transitions.
- **Proximity & Collision Detection:**
  - Real-time pairwise distance matrix calculation via NumPy.
  - Configurable safety thresholds (Proximity warning: $2.2\,\text{m}$, Critical collision: $1.2\,\text{m}$).
  - Pre-transition collision prediction samples candidate flight paths before motion begins.
- **Interactive 3D Camera Controls:** Orbit, pan, zoom, and preset viewing angles (`1`: Oblique 3D, `2`: Top-Down, `3`: Front, `4`: Side, `F`: Focus).
- **Trajectory Storage & Playback:** Export and import keyframes (ID, timestamp, 3D coordinates, RGB colors, states) in JSON and CSV formats with full in-simulator replay.
- **Hardware-Agnostic Core:** Decoupled communication layer with standard MAVLink telemetry mapping, keeping the software ready for external SITL autonomy stacks.

---

## 🛠️ Technology Stack

- **Primary Language:** Python 3.10+ (tested on Python 3.14)
- **3D Engine:** Ursina Engine 8.3.0 (Panda3D 1.10.16)
- **Mathematical Operations:** NumPy
- **Concurrency & Networking:** Python `asyncio` & UDP sockets
- **Drone Protocol:** MAVLink v2 (`pymavlink` 2.4.50) / UDP datagrams
- **Data Serialization:** JSON and CSV
- **Testing:** pytest 9.2.0

---

## 📂 Project Structure

```text
UAV Swarm System/
├── main.py                          # Root launcher script
├── requirements.txt                 # Project dependencies
├── README.md                        # Documentation
├── .gitignore
│
├── uav_swarm/                       # Primary application package
│   ├── config.py                    # Constants, DroneState, RGB color palettes
│   ├── main.py                      # Core entrypoint, CLI argument parser, loop
│   ├── simulation/
│   │   ├── environment.py           # 3D dark scene, ground grid, RGB reference axes
│   │   ├── drone.py                 # Quadcopter visual entity, spinning rotors, labels
│   │   └── camera.py                # Orbit, pan, zoom, preset angle controller
│   ├── swarm/
│   │   ├── manager.py               # SwarmManager, fleet lifecycle, replay
│   │   ├── formations.py            # Line, V, Circle, Square, Triangle, Helix
│   │   ├── trajectory.py            # Smoothstep interpolation & waypoints
│   │   └── collision.py             # Pairwise distance & conflict prediction
│   ├── communication/
│   │   ├── base.py                  # VehicleAdapterBase & telemetry dataclass
│   │   ├── simulator_adapter.py     # Local deterministic in-memory adapter
│   │   └── mavlink_adapter.py       # MAVLink / UDP SITL network adapter
│   └── dashboard/
│       └── controls.py              # Integrated HUD banner & interactive buttons
│
├── data/
│   └── formations/                  # Stored JSON/CSV trajectories
│       └── sample_helix_flight.json # Pre-generated sample trajectory
│
└── tests/                           # Comprehensive test suite
    ├── test_formations.py           # Mathematical formation tests
    ├── test_trajectory.py           # Interpolation & easing tests
    ├── test_collision.py            # Distance matrix & conflict prediction tests
    ├── test_manager_and_storage.py  # Fleet lifecycle, JSON/CSV I/O, playback tests
    ├── test_communication.py        # Adapter lifecycle and timeout tests
    └── test_simulation_entities.py  # Ursina headless 3D entity validation
```

---

## 🚀 Getting Started

### 1. Installation
Clone or navigate to the repository directory and install the requirements:
```bash
pip install -r requirements.txt
```

### 2. Launch the Simulation
From the workspace root, run:
```bash
python main.py
```

### 3. Custom Swarm Parameters
You can customize the fleet size, altitude, spacing, and flight speed via CLI flags:
```bash
# Launch a 25-drone swarm at 6.0m altitude with 3.5m spacing:
python main.py --drones 25 --altitude 6.0 --spacing 3.5 --speed 5.0

# Launch with external MAVLink UDP adapter:
python main.py --drones 8 --adapter mavlink
```

---

## 🎮 Controls and Shortcuts

### Mouse Navigation:
- **Right-Click Drag:** Orbit around swarm center
- **Middle-Click Drag** (or **Shift + Right-Click Drag**): Pan camera
- **Scroll Wheel:** Zoom in / out

### Hotkeys:
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

### Dashboard Buttons:
- **[Launch All]**: Arms all drones and ascends smoothly to configured hover altitude.
- **[Land All]**: Directs drones to touch down on their respective ground coordinates.
- **[Reset]**: Instantly resets fleet positions, velocities, and statuses back to initial ground state.
- **[Pause / Resume]**: Pauses or resumes simulation time.
- **[Line], [V Formation], [Circle], [Square], [Triangle], [Helix]**: Switches formation.
- **Spacing [ - ] / [ + ]**: Adjusts formation spacing by $0.5\,\text{m}$ increments.
- **Speed [ - ] / [ + ]**: Adjusts flight velocity by $1.0\,\text{m/s}$ increments.
- **[Save JSON] / [Save CSV]**: Exports live trajectory snapshot to `data/formations/`.
- **[Load & Replay]**: Loads latest trajectory file and replays flight path.

---

## 📐 Mathematical Formations

All formation calculations are implemented with pure NumPy in [`uav_swarm/swarm/formations.py`](uav_swarm/swarm/formations.py) with zero rendering engine dependencies:

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

## 🛡️ Proximity and Collision Detection

The safety engine in [`uav_swarm/swarm/collision.py`](uav_swarm/swarm/collision.py) executes two levels of validation:

1. **Real-Time Runtime Detection:**
   On every frame, pairwise Euclidean distances are calculated:
   $$D_{ij} = \|\mathbf{p}_i - \mathbf{p}_j\|$$
   - $D_{ij} < 1.2\,\text{m}$ $\rightarrow$ **Critical Collision Alarm**: HUD displays alert and affected drones illuminate in crimson red.
   - $1.2\,\text{m} \le D_{ij} < 2.2\,\text{m}$ $\rightarrow$ **Proximity Warning**: HUD displays warning message and affected drones highlight in amber/red.
2. **Pre-Transition Trajectory Conflict Prediction:**
   Before commanding a formation change, the trajectory is sampled at 25 intermediate time steps ($t \in [0, 1]$). If any two paths cross closer than the warning distance, the dashboard alerts the operator with the specific drone IDs and the exact timeline progress where the conflict will occur.

---

## 💾 Trajectory Recording & Playback

Formation trajectories can be exported and imported in both JSON and CSV formats.

### Data Format Specification:
Each record contains:
- `drone_id`: Integer ID of the drone (`0, 1, ...`)
- `timestamp`: Epoch or relative timestamp in seconds
- `x`, `y`, `z`: 3D Cartesian coordinates in meters
- `r`, `g`, `b`: Normalized RGB color values `[0.0, 1.0]`
- `state`: String representation of drone state (e.g. `IN_FLIGHT`)

Files are saved to `data/formations/`. Clicking **[Load & Replay]** inside the simulator automatically discovers the latest saved file and executes trajectory playback.

---

## 📡 MAVLink and SITL Integration

The communication architecture separates the simulation loop from networking adapters:

- **Local Simulation Adapter (`LocalSimulationAdapter`):** The default zero-overhead adapter executing deterministic in-memory kinematics.
- **MAVLink / SITL Adapter (`MAVLinkAdapter`):** Networked adapter that connects to external autopilot SITL instances (e.g. ArduPilot SITL or PX4 SITL) over localhost UDP ports.

### Port Allocation:
Each vehicle is addressed on a dedicated UDP port:
```text
Port = BASE_PORT + drone_id  (e.g., Drone 0: 14550, Drone 1: 14551, Drone 2: 14552 ...)
```

### SITL Setup:
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

## 🧪 Running Tests

The test suite thoroughly covers all mathematical formations, trajectory interpolation, collision detection, serialization, and communication adapters:

```bash
pytest -v
```

All 28 tests pass across unit and integration suites.

---

## 📄 License

MIT License. Designed and developed for lightweight, high-performance UAV swarm simulation and research.
