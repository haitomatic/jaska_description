# Jaska Robot USD Assets for Isaac Sim

This directory contains USD (Universal Scene Description) representations of the Jaska robot for use with NVIDIA Isaac Sim.

## Files

### Robot Assets
- `jaska_robot.usd` - Main robot USD file converted from URDF
- `ZED_X.usdc` - ZED X camera asset
- `configuration/` - Additional configuration files

### Setup Scripts

Python utilities for Isaac Sim setup are now in `../scripts/isaac_sim/`:
- `setup_lidar_once.py` - ⭐ Run once to configure the rotary lidar, then save USD
- `create_test_world.py` - Create test environment with obstacles and robot
- See [../scripts/isaac_sim/README.md](../scripts/isaac_sim/README.md) for usage

### Reference Code
- `lidar_examples.py` - Code snippets and configuration examples

## Converting URDF to USD

The USD files are generated from the URDF files in `../urdf/`. To regenerate or update:

**Step 0: Process xacro to URDF** (required for all methods)

Isaac Sim requires a processed URDF file. Generate it first:
```bash
cd /home/haito/haito_dev/ros2_ws/src/jaska_description
xacro urdf/jaska_robot.xacro > urdf/jaska_robot.urdf
```

### Method 1: Using Isaac Sim GUI
1. Open Isaac Sim
2. Go File - Import and select the Jaska urdf
3. Configure movable base
4. Click Import

### Method 2: Using Python Script

```python
from omni.isaac.urdf import _urdf

config = _urdf.ImportConfig()
config.merge_fixed_joints = False
config.fix_base = False  # Mobile robot
config.convex_decompose = True
config.import_inertia_tensor = True

# Process xacro first if needed
import subprocess
subprocess.run([
    "xacro",
    "../urdf/jaska_robot.xacro",
    "-o", "/tmp/jaska_robot.urdf"
])

# Convert to USD
_urdf.acquire_urdf_interface().parse_urdf(
    "/tmp/jaska_robot.urdf",
    "jaska_robot.usd",
    config
)
```

### Method 3: Using Isaac Sim CLI (Standalone)

```bash
# From Isaac Sim installation directory
./python.sh -c "
from omni.isaac.urdf import _urdf
import omni.isaac.core
_urdf.acquire_urdf_interface().parse_urdf(
    '/path/to/urdf/jaska_robot.urdf',
    '/path/to/usd/jaska_robot.usd'
)
"
```

## Adding Pre-existing Isaac Sim Sensors

If your sensor is already available in Isaac Sim's asset library (like ZED X camera), add it directly instead of importing from URDF:

### Method 1: Using Isaac Sim GUI

1. **Open your robot USD** in Isaac Sim
2. **Find the asset**:
   - Window → Browser → Asset Browser
   - Search for "ZED X" or navigate to sensor categories
3. **Add to scene**:
   - Drag asset into Stage panel
   - Position it relative to robot link (e.g., attach to `camera_link`)
4. **Create attachment**:
   - Select the camera prim in Stage panel
   - Right-click → Create → Physics → Fixed Joint (to attach to robot link)
   - Or use Xform operations to position it
5. **Save** the updated USD

### Method 2: Programmatic Reference (Python)

Add the sensor via Python script for automation:

```python
from pxr import Usd, UsdGeom, Gf

# Open your robot stage
stage = Usd.Stage.Open("jaska_robot.usd")

# Create a reference to Isaac Sim's ZED X asset
# Find asset path in Isaac Sim: typically in omniverse://localhost/NVIDIA/Assets/...
camera_prim = stage.DefinePrim("/World/Robot/camera_link/zedx_camera", "Xform")
camera_prim.GetReferences().AddReference(
    "omniverse://localhost/NVIDIA/Assets/Isaac/2023.1.1/Isaac/Sensors/ZED/zedx.usd"
)

# Position the camera relative to camera_link
xform = UsdGeom.Xformable(camera_prim)
xform.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.0, 0.05))  # 5cm forward
xform.AddRotateXYZOp().Set(Gf.Vec3f(0, 0, 0))

stage.Save()
```

**Finding Asset Paths:**

To find the exact path of Isaac Sim assets:

1. In Isaac Sim: Window → Browser → Content Browser
2. Navigate to NVIDIA Assets → Isaac → Sensors
3. Right-click asset → Copy Path
4. Use this path in references

## Adding Rotary Lidar Sensor

Configure the lidar **ONCE**, save the USD, and it's permanently embedded:

1. **Open Isaac Sim**
2. **Load your robot**: File > Open > `jaska_robot.usd`
3. **Run in Script Editor**:
   ```python
   exec(open('/home/haito/haito_dev/ros2_ws/src/jaska_description/usd/setup_lidar_once.py').read())
   ```
4. **Save**: Press `Ctrl+S`
5. **Done!** ✓

After this, the lidar is embedded in your USD - just load and use!

```python
from omni.isaac.core.utils.stage import open_stage
open_stage("/path/to/jaska_robot.usd")  # Lidar already configured!
```

**How it works**: Sensor APIs (`OmniSensorGenericLidarCoreAPI`) and properties (rotation rate, FOV, range) are stored as USD attributes. Isaac Sim reads these automatically on load.

**Current Configuration (Unitree L2)**:
- Rotation: 10 Hz
- Horizontal FOV: 360°
- Vertical FOV: ±7° (14° total)
- Range: 0.03m - 30m
- Resolution: 0.2° (1800 pts/rotation)

**To change settings later**:
- Edit in Isaac Sim GUI (Property panel), or
- Re-run `setup_lidar_once.py`, or
- Edit USD directly:
  ```python
  from pxr import Usd
  stage = Usd.Stage.Open("jaska_robot.usd")
  sensor = stage.GetPrimAtPath("/jaska_robot/unitree_lidar_link/Rotary_lidar")
  sensor.GetAttribute("rotationRate").Set(20.0)  # Change to 20 Hz
  stage.Save()
  ```

**Troubleshooting**:
- No sensor after loading? → Did you save the USD?
- No point cloud? → Press spacebar to start simulation
- Need to reconfigure? → Re-run the setup script and save again

## Using in Isaac Sim

### Loading the Robot
```python
from omni.isaac.core.robots import Robot
from omni.isaac.core.utils.stage import add_reference_to_stage

# Add robot to stage
jaska_robot_path = add_reference_to_stage(
    usd_path="/path/to/jaska_description/usd/jaska_robot.usd",
    prim_path="/World/Jaska"
)
```

### With ROS2 Bridge
```python
from omni.isaac.core import World
from omni.isaac.core.articulations import Articulation

world = World()
world.scene.add(
    Articulation(
        prim_path="/World/Jaska",
        name="jaska_robot"
    )
)
```


## USD toolset installation

https://docs.nvidia.com/learn-openusd/latest/usdview-install-instructions.html

To use:
```
cd /home/haito/haito_dev/usd_root/
source /home/haito/haito_dev/usd_root/python-usd-venv/bin/activate
./scripts/usdedit.sh ..
./scripts/usdview_gui.sh
deactivate
```


## Notes

- STL meshes from `../meshes/` are referenced by the USD file
- Collision meshes are auto-generated with convex decomposition
- Physics properties (mass, inertia) are imported from URDF
- Joint limits and dynamics are preserved

## Updating

When the URDF changes:
1. Update `../urdf/jaska_robot.xacro`
2. Re-run the conversion process above
3. Commit both URDF and USD changes together
