# Isaac Sim Scripts for Jaska Robot

Python utilities and custom extensions for working with the Jaska robot in NVIDIA Isaac Sim.

## Custom Extensions

### exts/jaska.viewport.setup
Auto-configures dual viewport layout on Isaac Sim startup. See [exts/README.md](exts/README.md) for installation.

**Quick Install:**
1. Window → Extensions → ⚙️ (gear icon)
2. Add extension search path: `/home/haito/haito_dev/ros2_ws/src/jaska_description/scripts/isaac_sim/exts`
3. Search "Jaska Viewport" and toggle ON

## Available Scripts

### 1. default_view_setup.py
**Automatically configure dual viewport layout (Perspective + Camera view).**

**Usage:**
1. Open Isaac Sim
2. Load your scene (robot with camera)
3. Run this script in Script Editor
4. Viewports will be arranged automatically

Can also be integrated into other scripts for automatic layout setup.

### 2. setup_lidar_once.py
**One-time setup script to configure the Unitree L2 lidar sensor.**

**Usage:**
1. Open Isaac Sim
2. Load `../../usd/jaska_robot.usd`
3. Open Script Editor (Window → Script Editor)
4. Run this script
5. Save the USD file (Ctrl+S)

The lidar will be permanently configured with Unitree L2 specifications:
- Max Range: 30m
- Vertical FOV: 90°
- Horizontal FOV: 360°
- Angular Resolution: 0.64°
- Rotation Rate: 5.55Hz

### 3. create_test_world.py
**Creates a test environment with various objects and spawns the Jaska robot.**

**Usage:**
1. Open Isaac Sim
2. Open Script Editor (Window → Script Editor)
3. Run this script
4. Press PLAY to start simulation

**Creates:**
- Ground plane
- Various geometric obstacles (cubes, spheres, cylinders, cones)
- Jaska robot at world center

Perfect for testing navigation, lidar scanning, and perception algorithms.

## Requirements

All scripts require Isaac Sim to be running with the following Python APIs:
- `omni.isaac.core`
- `omni.isaac.sensor`
- `pxr` (USD Python API)

## File Structure

```
jaska_description/
├── scripts/
│   └── isaac_sim/
│       ├── README.md                  (this file)
│       ├── setup_lidar_once.py        (lidar configuration)
│       └── create_test_world.py       (test environment)
└── usd/
    ├── jaska_robot.usd                (robot asset)
    ├── lidar_examples.py              (reference code)
    └── README.md                      (USD documentation)
```

## Tips

- Run `setup_lidar_once.py` only once, then save the USD
- Use `create_test_world.py` to quickly set up test scenarios
- Modify object positions/types in `create_test_world.py` for different tests
- Check the usd/README.md for more detailed Isaac Sim workflow information
