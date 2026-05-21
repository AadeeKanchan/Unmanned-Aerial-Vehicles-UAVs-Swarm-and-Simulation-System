# 🛸Unmanned Aerial Vehicles (UAVs) Swarm and Simulation System🛩️

A high-performance, lightweight 3D simulation environment and control dashboard for synchronized multi-drone swarms. This project bypasses the need for expensive physical hardware by building a pure-software virtual sandbox designed for testing distributed robotics, autonomous fleet coordination, and complex spatial drone light shows.
---

> 🚧 **Work in Progress (WIP)**: This project is under active development. The core simulation layer and async communication loop are being iteratively updated. Contributions, feedback, and architectural discussions are welcome!

---

##   Project Overview

Developing a physical drone swarm introduces steep barriers to entry: high hardware costs, complex electronics troubleshooting, risk of catastrophic crashes, and strict airspace regulatory frameworks. 

This repository provides a **purely software-driven approach** to multi-UAV orchestration. By utilizing a **centralized command broadcast architecture**, the system treats the fleet as a single distributed network. The software scales seamlessly from a few drones up to large fleets, executing smooth, mathematical transitions between complex 3D shapes without physical hardware limitations.

---

##   System Architecture

The project is built around a decoupled, three-tier architecture running completely inside a local environment:

[ 3D Animation Layer / Math Engine ]
                ⬇️
(Trajectory & Coordinate Mapping)
[ Central Control Dashboard (Backend) ]
                ⬇️
(Asynchronous Network Broadcast via MAVLink/UDP)
[ 3D Visual Sandbox (Ursina Engine Engine) ] ◄──► [ Virtual Flight Stacks (SITL) ]


1. **The Control Dashboard (Backend):** Built with Python utilizing asynchronous I/O (`asyncio`). It manages concurrent network connections to every virtual vehicle, coordinates unified states (arming, geofencing), and broadcasts telemetry.
2. **The Visual Sandbox:** A native 3D simulation window built using **Ursina Engine** (powered by Panda3D). Drones are represented as 3D spatial points capable of dynamic RGB/LED color states and continuous spatial translation.
3. **The Flight Engine (SITL):** Software-in-the-Loop drone instances running real-world autopilot firmware logic, exposing unique UDP network ports for precision coordinate tracking.

---

##   Key Features & Capabilities

*   **One-Click Fleet Synchronization:** Multi-threaded command dispatching that arms, launches, and lands an entire fleet concurrently, mitigating network propagation delays.
*   **True 3D Spatial Formations:** Real-time geometric rendering of fleets in true X, Y, Z coordinate planes. 
*   **Fluid Trajectory Interpolation:** Mathematical path-planning that computes smooth transitions from one 3D shape to another, preventing overlapping collision lines or sudden position teleportation.
*   **Interactive 3D Camera Controls:** A fully navigable visual viewport allowing users to orbit, zoom, and inspect swarm formations from any angle in real-time.
*   **Hardware-Agnostic Core:** The control protocols map precisely to industry-standard robotics telemetry, making the software logic highly transferrable to actual hardware in the future.

---

##   Tech Stack

*   **Primary Language:** Python 3.10+
*   **3D Graphics & Rendering Engine:** Ursina Engine (Panda3D framework)
*   **Concurrency & Networking:** Python `asyncio` & UDP Network Protocols
*   **Target Communication Protocol:** MAVLink / MAVSDK-Python
*   **Math & Data Management:** NumPy (for high-speed coordinate transformations)

---

##   Development Roadmap

### Phase 1: The Core Visual Sandbox (Current Focus) 
*  Set up the Ursina 3D dark sky and grid coordinates layout.
*  Program basic 3D entity spawning for multiple virtual drone nodes.
*  Integrate camera movement mechanics (`EditorCamera`) for flexible viewports.

### Phase 2: Asynchronous Swarm Logic 
*  Implement an `asyncio` event loop to broadcast commands across multiple targets.
*  Create a minimalist desktop dashboard overlay for universal execution commands ("Launch All", "Land All").
*  Develop a database lookup table mapping each vehicle to its custom home coordinate.

### Phase 3: Trajectory Parsing & Show Generation 
*  Define a structured `.json`/`.csv` playback timeline standard for coordinates and color properties.
*  Integrate mathematical path generation (Sine waves, helixes, and polygon structures).
*  Add automated proximity-alert scripts to flag intersecting vectors before a collision path occurs.

---

##   Getting Started (Local Development)

### Prerequisites
Ensure you have Python installed along with standard package management tools:
```bash
python --version
