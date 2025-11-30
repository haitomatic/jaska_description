# Jaska Robot Description

URDF description package for the Jaska 6-wheel rocker-bogie differential drive robot.

## Overview

The Jaska robot features:
- **6-wheel rocker-bogie suspension** - Inspired by Mars rovers for excellent terrain handling
- **Differential drive control** - Left 3 wheels synchronized, right 3 wheels synchronized
- **Sensor mount at 45°** - Front-mounted angled plate for optimal sensor placement
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
- Main body: 1.2m x 0.6m x 0.3m
- Mass: 50kg
- Material: Blue colored body

### Rocker-Bogie Suspension
- **Left/Right Rockers**: 0.8m length, pivots at base
- **Left/Right Bogies**: 0.5m length, connects to rear of rockers
- **Joints**: Revolute joints allow suspension articulation
  - Rocker range: ±0.5 rad
  - Bogie range: ±0.3 rad

### Wheels (6 total)
- **Front wheels**: Mounted on front of rockers
- **Middle wheels**: Mounted on front of bogies
- **Rear wheels**: Mounted on rear of bogies
- Radius: 0.15m
- Width: 0.10m
- Mass: 2.5kg each

### Sensor Mount
- **Mount**: Custom STL mesh `lidar_and_camera_mount.stl`
- **Angle**: 45° forward tilt
- **Position**: Front of robot, top surface

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
3. Start `joint_state_publisher_gui` for interactive joint control
4. Launch RViz2 with custom configuration

### View the robot in RViz2:
- Use the joint_state_publisher_gui sliders to articulate the rocker-bogie suspension
- Observe how the 6 wheels adapt to terrain through the suspension system
- View TF frames for all components including sensors

## TF Frames

```
base_link
├── left_rocker
│   ├── front_left_wheel
│   ├── middle_left_wheel
│   └── left_bogie
│       └── rear_left_wheel
├── right_rocker
│   ├── front_right_wheel
│   ├── middle_right_wheel
│   └── right_bogie
│       └── rear_right_wheel
└── sensor_mount_base (45° angled)
    ├── unitree_lidar_link
    │   └── unitree_lidar_optical_frame
    └── zed_camera_link
        └── zed_camera_center
            ├── zed_left_camera_frame
            │   └── zed_left_camera_optical_frame
            └── zed_right_camera_frame
                └── zed_right_camera_optical_frame
```

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
| `rocker_pivot_offset_x` | 0.150 m | Rocker pivot X position from base center | Forward distance from base center to rocker pivot |
| `rocker_pivot_offset_z` | 0.000 m | Rocker pivot Z position from base center | Vertical distance (negative = below base center) |
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
| `sensor_mount_angle` | π/4 rad (45°) | Forward tilt angle | Angle of sensor mount plate from vertical |
| `sensor_mount_x` | base_x_size/2 - 0.050 m | X position on base | Distance from base center to mount point |
| `sensor_mount_z` | base_z_size/2 - 0.020 m | Z position on base | Height from base center (top surface) |
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

### How to Update Parameters

Edit the top section of `/home/haito/haito_dev/ros2_ws/src/jaska_description/urdf/jaska_robot.xacro`:

```xml
<!-- Vehicle Geometries - Rocker-Bogie Configuration -->
<xacro:property name="base_x_size" value="1.200000" />
<xacro:property name="base_y_size" value="0.600000" />
<xacro:property name="base_z_size" value="0.300000" />

<!-- Rocker-Bogie specific measurements -->
<xacro:property name="rocker_length" value="0.800" />
<xacro:property name="bogie_length" value="0.500" />
<xacro:property name="track_width" value="0.700" />

<!-- Wheel properties -->
<xacro:property name="wheel_radius" value="0.150" />
<xacro:property name="wheel_width" value="0.100" />
<xacro:property name="wheel_mass" value="2.5" />

<!-- ... etc ... -->
```

After updating, rebuild the package:
```bash
cd ~/haito_dev/ros2_ws
colcon build --packages-select jaska_description
source install/setup.bash
```

### Adjusting Sensor Mount Positions

Edit `/home/haito/haito_dev/ros2_ws/src/jaska_description/urdf/jaska_robot.xacro`:

```xml
<!-- For Unitree L2 Lidar position -->
<origin xyz="0 0 0.120" rpy="0 0 0"/>  <!-- Line ~283 -->

<!-- For ZED Camera position -->
<origin xyz="0 0 -0.050" rpy="0 0 0"/>  <!-- Line ~304 -->
```

Adjust the z-coordinate based on your actual mounting points on the STL mesh.

### Using Custom Meshes

Place your STL files in the `meshes/` directory and reference them:

```xml
<mesh filename="package://jaska_description/meshes/your_mesh.stl" scale="0.001 0.001 0.001"/>
```

Note: STL files are typically in mm, so scale by 0.001 to convert to meters.

## Dependencies

- ROS2 Jazzy
- `robot_state_publisher`
- `joint_state_publisher_gui`
- `xacro`
- `rviz2`

## License

Apache-2.0

## Author

Haito Development Team
