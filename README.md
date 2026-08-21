# Jaska Robot Description

URDF description package for the Jaska 6-wheel rocker-bogie differential drive robot.

## Overview

The Jaska robot features:
- **6-wheel rocker-bogie suspension** - Inspired by Mars rovers for excellent terrain handling
- **Differential drive control** - Left 3 wheels synchronized, right 3 wheels synchronized
- **Real STL meshes** - All major components use actual 3D models for accurate visualization
- **Parameterized design** - Easy adjustment of mesh orientation and scale via xacro properties
- **Sensor mount at -45°** - Front-mounted forward-tilted plate for optimal sensor placement
- **Unitree L2 Lidar** - Mounted on upper position of sensor mount
- **ZED X Camera** - Mounted on lower position of sensor mount

## Package Structure

```
jaska_description/
├── CMakeLists.txt
├── package.xml
├── README.md
├── config/           # Configuration files
├── launch/           # Launch files
│   └── display.launch.py
├── meshes/           # 3D mesh files
│   ├── lidar_and_camera_mount.stl
│   ├── zedx.stl
│   ├── unitree_l2.stl
│   ├── trunk.stl
│   ├── rocker.stl
│   ├── bogie.stl
│   └── wheel.stl
├── rviz/             # RViz configuration files
│   └── jaska_robot.rviz
├── scripts/
│   └── isaac_sim/    # Isaac Sim utilities (see Isaac Sim Integration)
│       ├── isaac_graph_service.py
│       ├── prim_tool.py
│       ├── check_is_topics.py
│       └── jaska_test.py
└── urdf/             # URDF/xacro files
    ├── jaska_robot.xacro
    └── jaska_wheel.xacro
```

## Robot Components

### Base Platform
- Main body: 0.8m x 0.4m x 0.17m (L x W x H)
- Mass: 20kg
- Material: Blue colored body
- Visual: Uses `trunk.stl` mesh with scale 0.09

### Rocker-Bogie Suspension
- **Left/Right Rockers**: 0.3m length, pivots at 0.115m from base center
- **Left/Right Bogies**: 0.3m length, connects to rear of rockers
- **Track width**: 0.6m between left and right sides
- **Visual**: Uses `rocker.stl` (scale 0.06) and `bogie.stl` (scale 0.045) meshes
- **Joints**: Revolute joints allow suspension articulation
  - Rocker range: ±0.5 rad (±28.6°)
  - Bogie range: ±0.3 rad (±17.2°)

### Wheels (6 total)
- **Front wheels**: Mounted on front of rockers
- **Middle wheels**: Mounted on front of bogies
- **Rear wheels**: Mounted on rear of bogies
- Radius: 0.11m
- Width: 0.08m
- Mass: 2.5kg each
- Visual: Uses `wheel.stl` mesh with scale 0.023

### Sensor Mount
- **Mount**: Custom STL mesh `lidar_and_camera_mount.stl`
- **Angle**: -45° forward tilt (negative pitch)
- **Position**: Front of robot (0.36m forward, -0.04m left, 0.075m up from base center)
- **Scale**: 0.001 (millimeters to meters conversion)

### Sensors
1. **Unitree L2 Lidar**
   - Frame: `unitree_lidar_link`
   - Optical frame: `unitree_lidar_optical_frame`
   - Mass: 0.18kg
   - Position: Upper mounting point on sensor mount
   - Mesh: Uses local Unitree L2 STL from `meshes/unitree_l2.stl`

2. **ZED X Camera**
   - Frame: `zed_camera_link`
   - Center frame: `zed_camera_center`
   - Left/Right frames with optical frames (stereo)
   - Mass: 0.15kg
   - Position: Lower mounting point on sensor mount
   - Mesh: Uses local ZED X STL from `meshes/zedx.stl`

## Building

```bash
cd ~/haito_dev/ros2_ws
colcon build --packages-select jaska_description
source install/setup.bash
```

## Visualization

### Launch RViz2 with the robot model:

```bash
ros2 launch jaska_description display.launch.py
```

This will:
1. Load the robot description from URDF
2. Start `robot_state_publisher`
3. Start `joint_state_publisher_gui` for interactive joint control (default)
4. Launch RViz2 with custom configuration

#### Launch Arguments:

- **`use_gui`** (default: `true`)
  - `true`: Launch `joint_state_publisher_gui` with interactive sliders
  - `false`: Launch `joint_state_publisher` without GUI (publishes default joint states)

  ```bash
  # Launch without GUI
  ros2 launch jaska_description display.launch.py use_gui:=false
  ```

- **`use_sim_time`** (default: `false`)
  - `true`: Use simulation time (Isaac Sim publishes `/clock`)
  - `false`: Use system time

  ```bash
  # Launch with simulation time
  ros2 launch jaska_description display.launch.py use_sim_time:=true
  ```

### View the robot in RViz2:
- Use the joint_state_publisher_gui sliders to articulate the rocker-bogie suspension
- Observe how the 6 wheels adapt to terrain through the suspension system
- View TF frames for all components including sensors

## TF Frames

### jaska_v2 TF Tree

The full frame tree as published at runtime. `base_footprint` is at ground level (z=0); `base_link` is the robot body centre (z=+0.322m above ground).

```
map                              (Nav2 AMCL/SLAM — added at runtime)
 └── odom                        (odometry origin)
      └── base_footprint         (ground-level reference, REP-105)
           └── base_link         (robot body centre, z=+0.322m)
               │
               ├── front_left_wheel   [continuous] xyz=( 0.423,  0.302, -0.201)
               ├── front_right_wheel  [continuous] xyz=( 0.423, -0.301, -0.201)
               ├── rear_left_wheel    [continuous] xyz=(-0.427,  0.302, -0.201)
               ├── rear_right_wheel   [continuous] xyz=(-0.427, -0.301, -0.201)
               │
               └── lidar_and_camera_mount_link  [fixed] xyz=(0.350, -0.043, 0.160) pitch=+45°
                   │
                   ├── unitree_lidar_link       [fixed] xyz=(0.001,  0.005, 0.090) pitch=-45°
                   │   └── unilidar_lidar       [fixed] xyz=(0, 0, 0.030)
                   │                            ★ lidar scan-origin frame
                   │
                   └── zed_camera_link          [fixed] xyz=(0.130,  0.042, 0.060) pitch=-45°
                       └── zed_camera_center    (optional — --profile camera)
```

### What publishes what

| Frame transition | Published by | Topic | Notes |
|---|---|---|---|
| `map → odom` | Nav2 AMCL / slam_toolbox | `/tf` | Added at Nav2 runtime |
| `odom → base_footprint` | `OdometryPublisher` AG (`tf_odom_to_base` node) | `/tf` | Dynamic — updated every tick from physics |
| `base_footprint → base_link` | `robot_state_publisher` | `/tf_static` | Fixed joint, z=+0.322m, from URDF |
| `base_link → wheels` | `robot_state_publisher` | `/tf` | From `/joint_states` (continuous joints) |
| `base_link → sensors` | `robot_state_publisher` | `/tf_static` | Fixed joints from URDF |

> **Nav2 config:** `robot_base_frame: base_footprint`, `odom_frame_id: odom`, `global_frame_id: map`.

> **`robot_state_publisher` is required** — it publishes `base_footprint → base_link` and all sensor frames from the URDF.

### Inspect TF at runtime

```bash
# Live TF tree snapshot (generates frames.pdf)
source /opt/ros/jazzy/setup.bash
ros2 run tf2_tools view_frames

# Echo a specific transform
ros2 run tf2_ros tf2_echo base_link unilidar_lidar

# List all active frames
ros2 run tf2_ros tf2_monitor
```

### TF conventions

| Axis | Direction |
|---|---|
| X | Forward |
| Y | Left |
| Z | Up |

Optical frames (`zed_*_optical_frame`) follow the camera convention: **Z forward, X right, Y down** — rotated −90° around X then −90° around Z relative to their parent.

## Integration with ZED ROS2 Wrapper

The robot description is compatible with the ZED ROS2 wrapper. The camera frames match the expected naming convention:
- `zed_camera_link` - Main camera body
- `zed_camera_center` - Camera optical center
- `zed_left_camera_optical_frame` - Left camera optical frame
- `zed_right_camera_optical_frame` - Right camera optical frame

## Integration with Unitree Lidar ROS2

The lidar frame `unitree_lidar_link` and `unitree_lidar_optical_frame` are ready for integration with the Unitree L2 lidar ROS2 driver.

### Lidar URDF plugin note

The Unitree L2 lidar link includes a `<gazebo>` sensor tag in the URDF with `gpu_lidar` plugin specs. This is **not used** — jaska_v2 runs exclusively in Isaac Sim, not Gazebo. The tag is retained for reference only.

In Isaac Sim, lidar data is published via the **LidarPublisher Action Graph** directly to `/unilidar/cloud`.

**To visualize in RViz2:**
1. Add → PointCloud2
2. Topic: `/lidar/points`
3. Fixed Frame: `base_footprint` or `unitree_lidar_optical_frame`

## Customization

### Physical Measurement Parameters

All physical dimensions that need to be measured and configured are defined at the top of `jaska_robot.xacro`. Here's the complete list:

#### 1. Base Platform Dimensions
| Parameter | Current Value | Description | How to Measure |
|-----------|--------------|-------------|----------------|
| `base_x_size` | 0.800 m | Length of main body | Front to back of chassis |
| `base_y_size` | 0.400 m | Width of main body | Left to right of chassis |
| `base_z_size` | 0.170 m | Height of main body | Bottom to top of chassis |
| `base_mass` | 20.0 kg | Mass of main body | Weigh the complete chassis |

#### 2. Rocker-Bogie Suspension
| Parameter | Current Value | Description | How to Measure |
|-----------|--------------|-------------|----------------|
| `rocker_length` | 0.300 m | Length of rocker arm | Distance from pivot to bogie connection |
| `bogie_length` | 0.300 m | Length of bogie arm | Distance between middle and rear wheel centers |
| `track_width` | 0.600 m | Distance between left/right sides | Center-to-center between left and right rockers |
| `rocker_pivot_offset_x` | 0.115 m | Rocker pivot X position from base center | Forward distance from base center to rocker pivot |
| `rocker_pivot_offset_z` | 0.0 m | Rocker pivot Z position from base center | Vertical distance (negative = below base center) |
| `rocker_mass` | 5.0 kg | Mass of each rocker | Weigh one rocker arm |
| `bogie_mass` | 3.0 kg | Mass of each bogie | Weigh one bogie arm |

#### 3. Wheel Specifications
| Parameter | Current Value | Description | How to Measure |
|-----------|--------------|-------------|----------------|
| `wheel_radius` | 0.110 m | Radius of wheel | Half of wheel diameter |
| `wheel_width` | 0.080 m | Width of wheel tire | Measure tire width |
| `wheel_mass` | 2.5 kg | Mass of each wheel | Weigh one complete wheel assembly |

#### 4. Sensor Mount Configuration
| Parameter | Current Value | Description | How to Measure |
|-----------|--------------|-------------|----------------|
| `sensor_mount_angle` | -π/4 rad (-45°) | Forward tilt angle (negative = forward) | Angle of sensor mount plate from vertical |
| `sensor_mount_x` | base_x_size/2 - 0.040 m | X position on base | Distance from base center to mount point |
| `sensor_mount_y` | -0.040 m | Y position on base | Left-right offset from center |
| `sensor_mount_z` | base_z_size/2 - 0.010 m | Z position on base | Height from base center (top surface) |
| `sensor_mount_mass` | 0.5 kg | Mass of sensor mount | Weigh the mounting plate |

#### 5. Unitree L2 Lidar
| Parameter | Current Value | Description | How to Measure |
|-----------|--------------|-------------|----------------|
| `lidar_radius` | 0.045 m (90mm) | Radius of lidar unit | Half of lidar diameter (spec sheet) |
| `lidar_height` | 0.060 m (60mm) | Height of lidar unit | Vertical size of lidar (spec sheet) |
| `lidar_mass` | 0.18 kg (180g) | Mass of lidar | From spec sheet or weigh |
| `lidar_mount_z` | 0.120 m | Z offset from sensor mount base | Vertical distance on mounting plate |
| `lidar_optical_offset_z` | 0.030 m | Optical center offset | Distance from base to optical center |

#### 6. ZED X Camera
| Parameter | Current Value | Description | How to Measure |
|-----------|--------------|-------------|----------------|
| `camera_collision_x` | 0.030 m | Length of camera | Front to back of camera body |
| `camera_collision_y` | 0.163 m | Width of camera | Left to right of camera body |
| `camera_collision_z` | 0.030 m | Height of camera | Top to bottom of camera body |
| `camera_mass` | 0.15 kg (150g) | Mass of camera | From spec sheet or weigh |
| `camera_mount_z` | -0.050 m | Z offset from sensor mount base | Vertical distance on mounting plate |
| `camera_optical_center_x` | 0.020 m | Optical center offset | Distance from camera base to optical center |
| `camera_baseline` | 0.120 m | Stereo baseline | Distance between left and right cameras (2×0.03) |

#### 7. Suspension Joint Limits
| Parameter | Current Value | Description | Notes |
|-----------|--------------|-------------|-------|
| `rocker_joint_limit` | ±0.5 rad (±28.6°) | Rocker articulation range | Max rotation of rocker relative to base |
| `bogie_joint_limit` | ±0.3 rad (±17.2°) | Bogie articulation range | Max rotation of bogie relative to rocker |

#### 8. Mesh Orientation Parameters (RPY in radians)
| Parameter | Current Value | Description | Notes |
|-----------|--------------|-------------|-------|
| `trunk_mesh_rpy` | π/2, 0, 0 | Trunk mesh rotation | Adjust to align STL with URDF frame |
| `rocker_mesh_rpy` | π/2, 0, π | Rocker mesh rotation | 90° pitch + 180° yaw |
| `bogie_mesh_rpy` | π/2, 0, 0 | Bogie mesh rotation | 90° pitch rotation |
| `wheel_mesh_rpy` | π/2, 0, 0 | Wheel mesh rotation | 90° pitch for cylinder axis |

#### 9. Mesh Scale Parameters
| Parameter | Current Value | Description | Notes |
|-----------|--------------|-------------|-------|
| `trunk_mesh_scale` | 0.09, 0.09, 0.09 | Trunk mesh scale | Custom scaling for trunk STL |
| `rocker_mesh_scale` | 0.06, 0.06, 0.06 | Rocker mesh scale | Custom scaling for rocker STL |
| `bogie_mesh_scale` | 0.045, 0.045, 0.045 | Bogie mesh scale | Custom scaling for bogie STL |
| `wheel_mesh_scale` | 0.023, 0.023, 0.023 | Wheel mesh scale | Custom scaling for wheel STL |
| `sensor_mount_mesh_scale` | 0.001, 0.001, 0.001 | Sensor mount scale | 0.001 for mm to meters |
| `lidar_mesh_scale` | 0.001, 0.001, 0.001 | Lidar mesh scale | 0.001 for mm to meters |
| `camera_mesh_scale` | 1, 1, 1 | Camera mesh scale | 1:1 scale (already in meters) |

### How to Update Parameters

Edit the top section of `/home/haito/haito_dev/ros2_ws/src/jaska_description/urdf/jaska_robot.xacro`:

```xml
<!-- Vehicle Geometries - Rocker-Bogie Configuration -->
<xacro:property name="base_x_size" value="0.800" />
<xacro:property name="base_y_size" value="0.400" />
<xacro:property name="base_z_size" value="0.170" />

<!-- Rocker-Bogie specific measurements -->
<xacro:property name="rocker_length" value="0.300" />
<xacro:property name="bogie_length" value="0.300" />
<xacro:property name="track_width" value="0.600" />

<!-- Wheel properties -->
<xacro:property name="wheel_radius" value="0.110" />
<xacro:property name="wheel_width" value="0.080" />
<xacro:property name="wheel_mass" value="2.5" />

<!-- Rocker-bogie angles and positions -->
<xacro:property name="rocker_pivot_offset_x" value="0.115" />
<xacro:property name="rocker_pivot_offset_z" value="0.0" />

<!-- Sensor mount properties -->
<xacro:property name="sensor_mount_angle" value="${-M_PI/4}" />
<xacro:property name="sensor_mount_x" value="${base_x_size/2 - 0.040}" />
<xacro:property name="sensor_mount_y" value="-0.040" />
<xacro:property name="sensor_mount_z" value="${base_z_size/2 - 0.010}" />

<!-- Mesh orientation adjustments (RPY in radians) -->
<xacro:property name="trunk_mesh_rpy" value="${M_PI/2} 0 0" />
<xacro:property name="rocker_mesh_rpy" value="${M_PI/2} 0 ${M_PI}" />
<xacro:property name="bogie_mesh_rpy" value="${M_PI/2} 0 0" />
<xacro:property name="wheel_mesh_rpy" value="${M_PI/2} 0 0" />

<!-- Mesh scale adjustments -->
<xacro:property name="trunk_mesh_scale" value="0.09 0.09 0.09" />
<xacro:property name="rocker_mesh_scale" value="0.06 0.06 0.06" />
<xacro:property name="bogie_mesh_scale" value="0.045 0.045 0.045" />
<xacro:property name="wheel_mesh_scale" value="0.023 0.023 0.023" />
<xacro:property name="sensor_mount_mesh_scale" value="0.001 0.001 0.001" />
<xacro:property name="lidar_mesh_scale" value="0.001 0.001 0.001" />
<xacro:property name="camera_mesh_scale" value="1 1 1" />
```

After updating, rebuild the package:
```bash
cd ~/haito_dev/ros2_ws
colcon build --packages-select jaska_description
source install/setup.bash
```

### Adjusting Mesh Orientation and Scale

All mesh files have separate orientation (RPY) and scale parameters for easy adjustment without editing the mesh files themselves.

#### To fix mesh alignment in RViz:

1. **Rotation issues**: Adjust the `*_mesh_rpy` parameters (values in radians)
   ```xml
   <!-- Example: Rotate trunk mesh 90° around X-axis -->
   <xacro:property name="trunk_mesh_rpy" value="${M_PI/2} 0 0" />
   ```

2. **Scale issues**: Adjust the `*_mesh_scale` parameters (X Y Z scale factors)
   ```xml
   <!-- Example: Scale wheel mesh uniformly -->
   <xacro:property name="wheel_mesh_scale" value="0.023 0.023 0.023" />

   <!-- Example: Non-uniform scaling (stretch along X) -->
   <xacro:property name="trunk_mesh_scale" value="0.10 0.09 0.09" />
   ```

**Note**: Remember that RPY rotations in URDF are in **radians**, not degrees!
- 90° = π/2 ≈ 1.5708
- 180° = π ≈ 3.14159
- -90° = -π/2 ≈ -1.5708

### Adjusting Sensor Mount Positions

Edit `/home/haito/haito_dev/ros2_ws/src/jaska_description/urdf/jaska_robot.xacro`:

```xml
<!-- For Unitree L2 Lidar position (around line 400) -->
<origin xyz="0.003 0.005 0.090" rpy="0 ${sensor_mount_angle} 0"/>

<!-- For ZED Camera position (around line 470) -->
<origin xyz="0.125 0.042 0.060" rpy="0 ${sensor_mount_angle} 0"/>
```

Adjust the xyz coordinates based on your actual mounting points on the STL mesh.

### Using Custom Meshes

All major components now use STL meshes for visual representation:

1. **Robot body parts**: `trunk.stl`, `rocker.stl`, `bogie.stl`, `wheel.stl`
2. **Sensor mount**: `lidar_and_camera_mount.stl`
3. **Sensors**: `unitree_l2.stl`, `zedx.stl`

Place your STL files in the `meshes/` directory and reference them:

```xml
<visual>
    <origin xyz="0 0 0" rpy="${component_mesh_rpy}" />
    <geometry>
        <mesh filename="package://jaska_description/meshes/your_mesh.stl"
              scale="${component_mesh_scale}"/>
    </geometry>
</visual>
```

**Best Practices**:
- Use STL meshes for **visual** geometry (high detail)
- Use simplified shapes (box, cylinder, sphere) for **collision** geometry (better performance)
- Always define separate `*_mesh_rpy` and `*_mesh_scale` xacro properties for each new mesh
- STL files in millimeters: use scale `0.001 0.001 0.001`
- STL files in meters: use scale `1 1 1`

## Dependencies

- ROS2 Jazzy
- `robot_state_publisher`
- `joint_state_publisher_gui`
- `xacro`
- `rviz2`

## Isaac Sim Integration

The Jaska v2 robot (`jaska_v2`) is imported into NVIDIA Isaac Sim 5.1 for high-fidelity PhysX simulation, RTX lidar/sensor simulation, and ROS2 Nav2 integration. USD assets are stored in the `usd/` and `urdf/jaska_v2/` directories.

### URDF Import into Isaac Sim (GUI)

> **Important:** The import settings below are required for the robot to move correctly in simulation. Using wrong settings will anchor the robot to the world.

1. **Open Isaac Sim** and go to **Isaac Utils → Workflows → URDF Importer**

2. **Set the Input File** to:
   ```
   <path_to_package>/urdf/jaska_v2.urdf
   ```

3. **Import Settings — critical options:**

   | Setting | Value | Reason |
   |---|---|---|
   | **Fix Base Link** | ☐ **UNCHECKED** | Must be off — checking this creates a `root_joint` that anchors the robot to the world and prevents movement |
   | **Joint Drive Type** | **Velocity** | Wheel joints must use velocity control so `cmd_vel` commands translate to wheel velocities via damping |
   | **Joint Drive Strength** (damping) | ~1025 | Applied per wheel joint as the velocity gain |

4. **Click Import** — Isaac Sim generates the USD hierarchy under `urdf/jaska_v2/`:
   ```
   urdf/jaska_v2/
   ├── jaska_v2.usd                  # Top-level robot USD (visual + structure)
   └── configuration/
       ├── jaska_v2_physics.usd      # Physics: articulation root, joint drives, collision
       └── jaska_v2_instanceable_meshes.usd
   ```

5. **Verify physics structure** after import using `usdcat`:
   ```bash
   ~/haito_dev/usd_root/bin/usdcat urdf/jaska_v2/configuration/jaska_v2_physics.usd \
     --flatten -o /tmp/jaska_v2_physics.usda
   grep -A5 "PhysicsArticulationRootAPI\|root_joint\|stiffness" /tmp/jaska_v2_physics.usda
   ```
   Expected output — **no `root_joint`**, `PhysicsArticulationRootAPI` on `base_link`, `stiffness = 0`:
   ```usda
   def Xform "base_link" (
       prepend apiSchemas = ["PhysicsArticulationRootAPI", "PhysxArticulationAPI"]
   )
   # drive:angular:physics:stiffness = 0   ← velocity control confirmed
   # drive:angular:physics:damping   = ~1025
   ```

### Loading in a World Scene

`jaska_v2.usda` (in `usd/`) is the main scene file that references the URDF-imported USD as a payload and adds all OmniGraph ActionGraphs for ROS2 topics. It is loaded into a world scene as a payload at `/World/jaska_v2`.

```usda
# metropolia_myyrmaki.usda (excerpt)
def Xform "jaska_v2" (
    payload = @./jaska_v2.usda@</World>
)
```

> **Path remapping note:** When `jaska_v2.usda` (defaultPrim `World`) is loaded as a payload at `/World/jaska_v2`, USD remaps all prim paths. The articulation root ends up at `/World/jaska_v2/jaska_v2/base_link` on the composed stage. String attributes like `inputs:robotPath` must use this full stage path — they are **not** automatically remapped.

### OmniGraph ActionGraphs (ROS2 Bridge)

`jaska_v2.usda` contains 6 OmniGraph ActionGraphs for ROS2 topic publishing:

| Graph | Published Topics |
|---|---|
| `DifferentialDrive` | Subscribes `/cmd_vel`, drives wheel joints |
| `OdometryPublisher` | `/odom` (nav_msgs/Odometry) |
| `JointStatePublisher` | `/joint_states` |
| `TFPublisher` | `/tf` |
| `LidarPublisher` | `/unilidar/cloud` (PointCloud2) |

All graphs require `fabricCacheBacking = "Shared"` to execute in Isaac Sim 5.1.

### Isaac Sim Scripts

Python utilities for interacting with the running simulation live in `scripts/isaac_sim/`.

**Prerequisites for all scripts:**
- Isaac Sim running with `isaac_graph_service.py` loaded in the Script Editor (REST on `localhost:8011`)
- ROS2 Jazzy sourced: `source /opt/ros/jazzy/setup.bash`

#### `isaac_graph_service.py`

REST API server that exposes Isaac Sim stage operations. Must be running inside IS for the other tools to work.

**Setup (once per IS session):**
1. Open Isaac Sim → Window → Script Editor
2. Open `scripts/isaac_sim/isaac_graph_service.py`
3. Click **Run** — service starts on `http://localhost:8011`
4. Verify: `curl http://localhost:8011/docs`

---

#### `prim_tool.py`

Save GUI edits from the live IS stage to disk, or hot-reload a USDA file into the running stage. Scoped to `/World/jaska_v2`.

```bash
cd ~/haito_dev/ros2_ws/src/jaska_description

# Save live stage edits → usd/jaska_v2/jaska_v2.usda
python3 scripts/isaac_sim/prim_tool.py save

# Save to a staging file first
python3 scripts/isaac_sim/prim_tool.py save usd/jaska_v2_wip.usda

# Hot-reload an edited file into the running stage
python3 scripts/isaac_sim/prim_tool.py load
python3 scripts/isaac_sim/prim_tool.py load usd/jaska_v2_wip.usda
```

---

#### `check_is_topics.py`

Inspect ROS2 topic rates and QoS from a running IS simulation.

```bash
source /opt/ros/jazzy/setup.bash
python3 scripts/isaac_sim/check_is_topics.py

# Faster sample (3 s per topic):
SAMPLE_TIME=3 python3 scripts/isaac_sim/check_is_topics.py
```

Sim must be **playing**. Outputs topic Hz rates, AG QoS, DDS QoS, and compatibility.

> **Note:** `ros2 node list` will always be empty — Isaac Sim uses anonymous DDS endpoints and does not register named ROS2 nodes. This is expected.

---

#### `jaska_test.py`

Smoke test for the live simulation: stationary turn + odometry verification + lidar cloud check.

```bash
source /opt/ros/jazzy/setup.bash
python3 scripts/isaac_sim/jaska_test.py
```

| Test | Pass criteria |
|------|---------------|
| Stationary turn (3 s, ω = 0.5 rad/s) | `/odom` publishing, XY drift < 0.15 m, yaw change ≥ 15° |
| Lidar cloud (3 s listen) | `/unilidar/cloud` receives ≥ 1 message |

Sim must be **playing** — the script checks `/sim/status` and exits if not.

---

#### Manual drive with teleop

Drive the robot interactively from the keyboard using `teleop_twist_keyboard`.

**Install (once):**
```bash
sudo apt install ros-jazzy-teleop-twist-keyboard
```

**Run:**
```bash
source /opt/ros/jazzy/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

| Key | Motion |
|-----|--------|
| `i` | Forward |
| `,` | Backward |
| `j` | Rotate left (CCW) |
| `l` | Rotate right (CW) |
| `u` / `o` | Forward + turn |
| `k` | Stop |
| `q` / `z` | Increase / decrease speed |

Publishes to `/cmd_vel`. Sim must be **playing**.

---

### Typical Edit Workflow

```
1. Open IS, load usd/metropolia_myyrmaki/metropolia_myyrmaki.usda
2. Run isaac_graph_service.py in Script Editor
3. Make edits in the IS GUI
4. python3 scripts/isaac_sim/prim_tool.py save
5. git diff usd/jaska_v2/jaska_v2.usda
6. git commit
```

### Simulation Environments

| Environment | File | Description |
|---|---|---|
| **Metropolia Myyrmäki** | `usd/metropolia_myyrmaki/metropolia_myyrmaki.usda` | Real 1st-floor layout of the Metropolia Myyrmäki campus building. Walls, corridors and rooms for realistic indoor navigation. |

To use: **File → Open** in Isaac Sim, navigate to the `.usda` file, then press **Play**.

---

#### Metropolia Myyrmäki — Build Log

Step-by-step record of how `metropolia_myyrmaki.usda` was constructed from scratch.

**Source file**

The building geometry came from an FBX export of the Myyrmäki campus 1st floor (`1FloorMyyr.usd`, renamed to `Floor1.usd`). The FBX was imported into Isaac Sim which produced a binary USDC with a single mesh prim at `/World/Foor1/path1` (note the FBX-importer typo "Foor1"). The FBX coordinate system is **centimetres + Y-up**, which requires correction in the world USDA.

**Step 1 — Create the world USDA**

Created `metropolia_myyrmaki.usda` with correct world settings:

```usda
(
    defaultPrim  = "World"
    metersPerUnit = 1
    upAxis       = "Z"
)
```

**Step 2 — Load the building as a payload with coordinate fixes**

```usda
def "Floor1" (
    prepend payload = @./Floor1.usd@
)
{
    # cm → m conversion
    double3 xformOp:scale:unitsResolve = (0.01, 0.01, 0.01)
    # Y-up (FBX) → Z-up (USD/ROS)
    double xformOp:rotateX:unitsResolve = 90
    uniform token[] xformOpOrder = [
        "xformOp:translate", "xformOp:rotateXYZ",
        "xformOp:scale", "xformOp:rotateX:unitsResolve",
        "xformOp:scale:unitsResolve"
    ]
}
```

After both transforms the building is ~129 m × 125 m at real scale — the robot (0.5 m wide) will look tiny in a top-down view; this is correct.

**Step 3 — Add PhysicsScene**

```usda
def PhysicsScene "PhysicsScene" (
    prepend apiSchemas = ["PhysxSceneAPI"]
) {}
```

Required for any PhysX simulation. Without it the robot falls through the ground.

**Step 4 — Add jaska\_v2 as a payload**

```usda
def Xform "jaska_v2" (
    prepend payload = @../../jaska_v2/jaska_v2.usda@
)
{
    double3 xformOp:translate = (1.8, 1.9, 0.32)
    ...
}
```

The spawn position places the robot inside the building entrance area at ~floor height.

**Step 5 — Add a GroundPlane with collision**

The building mesh does not include a physics floor slab, so an infinite collision plane was added:

```usda
def Xform "GroundPlane" {
    def Plane "CollisionPlane" (
        prepend apiSchemas = ["PhysicsCollisionAPI"]
    ) {
        uniform token axis = "Z"
    }
}
```

**Step 6 — Add LidarProduct render product**

Required by the `LidarPublisher` OmniGraph to produce RTX lidar point-cloud data:

```usda
def "Render" {
    def RenderProduct "LidarProduct" {
        rel camera    = </World/jaska_v2/unitree_lidar_link/UnitreeL2>
        int2 resolution = (1, 1)
    }
}
```

**Step 7 — Add a DistantLight**

```usda
def DistantLight "defaultLight" (
    prepend apiSchemas = ["ShapingAPI"]
) {
    float inputs:intensity = 3000
    ...
}
```

**Step 8 — Enable wall collision on the building mesh**

The FBX import creates only visual meshes — the robot would pass through walls. Fixed by adding `PhysicsCollisionAPI` via an `over` block (no modification to `Floor1.usd` needed):

```usda
over "Floor1" {
    over "Foor1" {
        over "path1" (
            prepend apiSchemas = ["PhysicsCollisionAPI", "PhysicsMeshCollisionAPI"]
        ) {
            # exact triangle mesh — most accurate, higher CPU cost
            uniform token physics:approximation = "none"
        }
    }
}
```

> If physics feels sluggish on a large map, change `physics:approximation` to `"meshSimplification"`.

## License

Apache-2.0

## Author

RoboGarage