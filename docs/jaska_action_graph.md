# Jaska V2 — Isaac Sim Action Graphs

**File:** `usd/jaska_v2/jaska_v2.usda`  
**USD path:** `/jaska_v2/ActionGraph/`

Each OmniGraph Action Graph (AG) is an `execution`-mode graph that ticks every simulation step via `OnPlaybackTick`. All graphs share the same pattern: `ROS2Context → OnPlaybackTick → (work nodes) → ROS2 publisher/subscriber`.

---

## Overview

| AG | ROS2 Role | Subscribes | Publishes |
|----|-----------|------------|-----------|
| [DifferentialDrive](#1-differentialdrive) | Drive controller | `/cmd_vel` | — |
| [LidarPublisher](#2-lidarpublisher) | Sensor publisher | — | `/unilidar/cloud` |
| [OdometryPublisher](#3-odometrypublisher) | Odometry publisher | — | `/odom`, `/tf` |
| [ImuPublisher](#4-imupublisher) | IMU publisher | — | `/imu/data` |
| [JointStatePublisher](#5-jointstatepublisher) | Joint state publisher | — | `/joint_states` |
| [ZEDCamera](#6-zedcamera) | Camera streamer | — | ZED SDK stream (port 30000) |

> **TFPublisher removed.**  
> A `TFPublisher` AG was present in earlier versions. It was removed because `robot_state_publisher` (started by `jaska_bringup`) covers all static and joint TF from the URDF, eliminating duplicate frames.

---

## 1. DifferentialDrive

**Purpose:** Subscribes to velocity commands and drives the four wheel joints via Isaac Sim's articulation controller.

### ROS2 Topics

| Direction | Topic | Message Type | Notes |
|-----------|-------|-------------|-------|
| **SUB** | `/cmd_vel` | `geometry_msgs/Twist` | Default topic name (unset in USD = IS default `cmd_vel`) |

### Internal data flow

```
/cmd_vel (Twist)
  └─► ROS2SubscribeTwist
        ├─► linear.x  → BreakVector3 → Negate → scale_to_stage_units
        └─► angular.z → BreakVector3 → Negate
              └─► DifferentialController
                    │  wheelDistance = 0.60 m
                    │  wheelRadius   = 0.11 m
                    │  maxLinearSpeed  = 1.0 m/s
                    │  maxAngularSpeed = 2.0 rad/s
                    │
                    └─► velocityCommand[0,1]  (left / right wheel speeds)
                          └─► replicated to all 4 joints:
                                [front_left_wheel_joint,  → left speed
                                 front_right_wheel_joint, → right speed
                                 rear_left_wheel_joint,   → left speed
                                 rear_right_wheel_joint]  → right speed
                                └─► IsaacArticulationController → /jaska_v2/base_link
```

> **Note on negation:** Both linear X and angular Z are negated before the controller. This corrects the axis convention mismatch between ROS2 REP-103 (X forward, Z up) and the USD stage orientation.

### Key nodes

| Node | IS Type | Role |
|------|---------|------|
| `ros2_subscribe_twist` | `ROS2SubscribeTwist` | Receives `/cmd_vel` |
| `differential_controller` | `DifferentialController` | Computes per-wheel velocity |
| `articulation_controller` | `IsaacArticulationController` | Applies velocity to joints |

---

## 2. LidarPublisher

**Purpose:** Reads the RTX lidar render product and publishes a full-scan PointCloud2 to ROS2.

### ROS2 Topics

| Direction | Topic | Message Type | Notes |
|-----------|-------|-------------|-------|
| **PUB** | `/unilidar/cloud` | `sensor_msgs/PointCloud2` | Full 360° scan, TRANSIENT QoS default |

### Key parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| `frameId` | `unilidar_lidar` | Published as `header.frame_id` |
| `type` | `point_cloud` | PointCloud2 output (not LaserScan) |
| `fullScan` | `true` | Publish complete rotation per message |
| `renderProductPath` | `/Render/LidarProduct` | IS render product prim |
| `resetSimulationTimeOnStop` | `false` | Keep timestamps continuous |

### Lidar config (Unitree L2)

The `UnitreeL2Lidar` prim uses `OmniSensorGenericLidarCoreAPI` with `numberOfEmitters=128`. The 18 real L2 elevation angles (0°→90°) are padded to 128 slots to satisfy the IS schema's fixed-length array requirement.

### Internal data flow

```
IS Lidar simulation → /Render/LidarProduct
  └─► ROS2RtxLidarHelper
        └─► /unilidar/cloud  (PointCloud2, frame: unilidar_lidar)
```

> **Nav2 note:** Nav2 costmaps expect `sensor_msgs/LaserScan`.  
> `jaska_bringup` runs `pointcloud_to_laserscan` to convert `/unilidar/cloud` → `/scan`.

---

## 3. OdometryPublisher

**Purpose:** Integrates chassis pose from the physics simulation and publishes odometry + the `odom → base_footprint` TF transform.

### ROS2 Topics

| Direction | Topic | Message Type | Notes |
|-----------|-------|-------------|-------|
| **PUB** | `/odom` | `nav_msgs/Odometry` | `header.frame_id = odom`, `child_frame_id = base_footprint` |
| **PUB** | `/tf` | `tf2_msgs/TFMessage` | Dynamic transform `odom → base_footprint` |

### Key parameters

| Parameter | Value |
|-----------|-------|
| `chassisPrim` | `/jaska_v2/base_link` |
| `odomFrameId` | `odom` |
| `chassisFrameId` | `base_footprint` |

### Internal data flow

```
IS physics → IsaacComputeOdometry (chassisPrim: /jaska_v2/base_link)
  │  outputs: position (vec3d), orientation (quatd),
  │           linearVelocity (vec3d), angularVelocity (vec3d)
  │
  ├─► ROS2PublishOdometry
  │     └─► /odom  (nav_msgs/Odometry, child_frame_id: base_footprint)
  │
  └─► ROS2PublishRawTransformTree  [tf_odom_to_base]
        parentFrameId = "odom"
        childFrameId  = "base_footprint"
        staticPublisher = false
        └─► /tf  (tf2_msgs/TFMessage, dynamic, VOLATILE QoS)
```

> **Why `base_footprint`:** Nav2 REP-105 convention requires `odom → base_footprint` so the 2D navigation stack operates at ground level. `base_footprint → base_link` (z=+0.322m) is published by `robot_state_publisher` from the URDF.

---

## 4. ImuPublisher

**Purpose:** Reads the IMU sensor prim and publishes inertial measurements to ROS2.

### ROS2 Topics

| Direction | Topic | Message Type | Notes |
|-----------|-------|-------------|-------|
| **PUB** | `/imu/data` | `sensor_msgs/Imu` | ~24 Hz |

### Key parameters

| Parameter | Value |
|-----------|-------|
| `imuPrim` | `/jaska_v2/base_link/imu_sensor` |
| `frameId` | `imu_link` |
| `topicName` | `imu/data` |

### Internal data flow

```
IS IMU sensor → IsaacReadIMU (imuPrim: /jaska_v2/base_link/imu_sensor)
  └─► ROS2PublishImu
        └─► /imu/data  (sensor_msgs/Imu, frame: imu_link, ~24 Hz)
```

---

## 5. JointStatePublisher

**Purpose:** Reads all joint positions/velocities from the articulation under `base_link` and publishes them so `robot_state_publisher` can compute wheel TF.

### ROS2 Topics

| Direction | Topic | Message Type | Notes |
|-----------|-------|-------------|-------|
| **PUB** | `/joint_states` | `sensor_msgs/JointState` | All joints under `/jaska_v2/base_link` |

### Key parameters

| Parameter | Value |
|-----------|-------|
| `targetPrim` | `/jaska_v2/base_link` |
| `topicName` | `joint_states` |

### Internal data flow

```
IS articulation → IsaacReadSimulationTime (timestamp)
  └─► ROS2PublishJointState (targetPrim: /jaska_v2/base_link)
        └─► /joint_states  (sensor_msgs/JointState)
              joints: front_left_wheel_joint, front_right_wheel_joint,
                      rear_left_wheel_joint,  rear_right_wheel_joint
```

> **Consumed by:** `robot_state_publisher` listens to `/joint_states` and publishes `base_footprint → base_link → wheel` transforms on `/tf`.

---

## 6. ZEDCamera

**Purpose:** Streams the ZED-X virtual camera from Isaac Sim to the ZED SDK via the Stereolabs streaming protocol. The `zed-ros2-wrapper` connects to this stream and publishes RGB, depth, point cloud, and IMU topics to ROS2.

### USD prim

| Parameter | Value |
|-----------|-------|
| `cameraPrim` | `/jaska_v2/zed_camera_link` |
| `cameraModel` | `ZED_X` |
| `resolution` | `HD1200` |
| `fps` | `60` |
| `streamingPort` | `30000` |

> **Camera model file:** `usd/jaska_v2/ZED_X.usdc` — referenced on `zed_camera_link`, provides the `CameraLeft`, `CameraRight`, and `Imu_Sensor` prims.

> **Port note:** The ZED docs state streaming ports must be odd, but this restriction does not apply to simulation (`sim_mode`). Isaac Sim defaults to port **30000** (even) and it works correctly.

### Internal data flow

```
IS renderer → ZED_X.usdc (CameraLeft, CameraRight)
  └─► sl.sensor.camera.ZED_Camera node
        │  cameraPrim = /jaska_v2/zed_camera_link
        │  streamingPort = 30000
        │
        └─► ZED SDK simulation server (localhost:30000)
              └─► zed-ros2-wrapper
                    launch args: sim_mode:=true  sim_address:=127.0.0.1  sim_port:=30000
                    │
                    ├─► /zed/zed_node/rgb/color/rect/image         (sensor_msgs/Image)
                    ├─► /zed/zed_node/depth/depth_registered       (sensor_msgs/Image)
                    ├─► /zed/zed_node/point_cloud/cloud_registered (sensor_msgs/PointCloud2)
                    └─► /zed/zed_node/imu/data                     (sensor_msgs/Imu)
```
