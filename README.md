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
  - `true`: Use simulation time (for Gazebo integration)
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

The robot has the following TF frame hierarchy:

```
base_link (robot base, main reference frame)
├── left_rocker (left rocker arm, revolute joint)
│   ├── front_left_wheel (left front wheel, continuous joint)
│   └── left_bogie (left bogie arm, revolute joint)
│       ├── middle_left_wheel (left middle wheel, continuous joint)
│       └── rear_left_wheel (left rear wheel, continuous joint)
│
├── right_rocker (right rocker arm, revolute joint)
│   ├── front_right_wheel (right front wheel, continuous joint)
│   └── right_bogie (right bogie arm, revolute joint)
│       ├── middle_right_wheel (right middle wheel, continuous joint)
│       └── rear_right_wheel (right rear wheel, continuous joint)
│
└── sensor_mount_base (-45° forward tilt, fixed joint)
    ├── unitree_lidar_link (Unitree L2 lidar body, fixed joint)
    │   └── unitree_lidar_optical_frame (lidar optical center, fixed joint)
    │
    └── zed_camera_link (ZED X camera mount point, fixed joint)
        └── zed_camera_center (camera center body, fixed joint)
            ├── zed_left_camera_frame (left camera frame, fixed joint)
            │   └── zed_left_camera_optical_frame (left optical frame, fixed joint)
            │
            └── zed_right_camera_frame (right camera frame, fixed joint)
                └── zed_right_camera_optical_frame (right optical frame, fixed joint)
```

### Displaying TF Frames in RViz2

To visualize the TF tree in RViz2:

1. **Launch the robot description**:
   ```bash
   ros2 launch jaska_description display.launch.py
   ```

2. **Enable TF display in RViz2**:
   - In the RViz2 window, click **"Add"** button in the Displays panel
   - Select **"By display type"** → **"TF"**
   - Click **"OK"**

3. **Configure TF display options**:
   - Expand the **TF** item in the Displays panel
   - Check **"Show Axes"** to display coordinate axes for each frame
   - Check **"Show Names"** to display frame names
   - Adjust **"Marker Scale"** (default: 1.0) to change axes size
   - Adjust **"Alpha"** (default: 1.0) for transparency

4. **View specific frames**:
   - Expand **"Frames"** under TF display
   - Check/uncheck individual frames to show/hide them
   - Common frames to monitor:
     - `base_link` - Robot base
     - `sensor_mount_base` - Sensor mount plate
     - `unitree_lidar_optical_frame` - Lidar scanning center
     - `zed_left_camera_optical_frame` - Left camera optical center
     - `zed_right_camera_optical_frame` - Right camera optical center

5. **View TF tree in terminal**:
   ```bash
   # View TF tree structure
   ros2 run tf2_tools view_frames

   # This generates frames.pdf showing the complete TF tree
   # Open it with:
   evince frames.pdf
   ```

6. **Monitor TF transforms**:
   ```bash
   # Echo transform between two frames
   ros2 run tf2_ros tf2_echo base_link zed_left_camera_optical_frame

   # List all active frames
   ros2 run tf2_ros tf2_monitor
   ```

### TF Frame Conventions

- **Coordinate system**: ROS REP 103 standard
  - X: Forward
  - Y: Left
  - Z: Up

- **Optical frames**: Follow camera convention (Z forward, X right, Y down)
  - `*_optical_frame` frames are rotated -90° around X, then -90° around Z

- **Joint types**:
  - `revolute`: Limited rotation joints (rockers, bogies)
  - `continuous`: Unlimited rotation joints (wheels)
  - `fixed`: No movement (sensors, mounts)

## Integration with ZED ROS2 Wrapper

The robot description is compatible with the ZED ROS2 wrapper. The camera frames match the expected naming convention:
- `zed_camera_link` - Main camera body
- `zed_camera_center` - Camera optical center
- `zed_left_camera_optical_frame` - Left camera optical frame
- `zed_right_camera_optical_frame` - Right camera optical frame

## Integration with Unitree Lidar ROS2

The lidar frame `unitree_lidar_link` and `unitree_lidar_optical_frame` are ready for integration with the Unitree L2 lidar ROS2 driver.

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

## License

Apache-2.0

## Author

RoboGarage