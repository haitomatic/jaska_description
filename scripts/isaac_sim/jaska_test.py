#!/home/haito/haito_dev/ros2_ws/src/jaska_description/.venv/bin/python
"""
jaska_test.py — jaska_v2 full IS output smoke test.

  Section 0 — Topic Health (all IS output topics):
      • /odom            nav_msgs/Odometry          rate check
      • /tf              tf2_msgs/TFMessage          rate check
      • /tf_static       tf2_msgs/TFMessage          exists (TRANSIENT_LOCAL)
      • /joint_states    sensor_msgs/JointState      rate check
      • /unilidar/cloud  sensor_msgs/PointCloud2     rate check

  Section 1 — TF tree:
      • odom → base_link  transform present
      • /odom header.frame_id = "odom", child_frame_id = "base_link"
      • /tf_static has base_link → wheel frames

  Section 2 — Joint states:
      • All 4 wheel joints present in /joint_states

  Test 3 — Rotate left / CCW (4 s @ angular.z = +0.5 rad/s):
      • /odom is publishing
      • XY position drift < 0.15 m
      • Yaw change ≥ 10°

  Test 4 — Rotate right / CW (4 s @ angular.z = -0.5 rad/s):
      • /odom is publishing
      • XY position drift < 0.15 m
      • Yaw change ≥ 10°

  Test 5 — Drive forward (1 s):
      • Displacement ≥ 0.2 m

  Test 6 — Drive backward (1 s):
      • Displacement ≥ 0.2 m

  Test 7 — Lidar cloud (3 s listen):
      • /unilidar/cloud receives ≥ 1 message

Sim must be PLAYING. Script checks /sim/status and exits early if not.

PREREQS:
  • Isaac Sim open and PLAYING with jaska_v2.usda (or metropolia world)
  • isaac_graph_service.py running in IS Script Editor
  • source /opt/ros/jazzy/setup.bash

USAGE:
  python3 scripts/isaac_sim/jaska_test.py
"""

import atexit
import math
import os
import re
import signal
import subprocess
import sys
import time

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
IS_BASE_URL   = os.environ.get("IS_BASE_URL", "http://localhost:8011")
ROS_SETUP     = "/opt/ros/jazzy/setup.bash"

TURN_DURATION    = 4.0    # seconds per rotation test
ANGULAR_Z        = 0.5    # rad/s
MAX_DRIFT_M      = 0.15   # max allowed XY drift during turn
MIN_YAW_DEG      = 10.0   # minimum expected yaw change

DRIVE_SPEED      = 0.5    # m/s for forward/backward tests
DRIVE_DURATION   = 1.0    # seconds
MIN_DRIVE_M      = 0.2    # minimum displacement to count as moving
LIDAR_CHECK_SECS = 3      # seconds to sample /unilidar/cloud
RATE_CHECK_SECS  = 3      # seconds to measure topic rates

# Expected minimum rates (Hz) for IS output topics
MIN_ODOM_HZ      = 20.0
MIN_TF_HZ        = 20.0
MIN_JS_HZ        = 20.0
MIN_LIDAR_HZ     =  5.0

WHEEL_JOINTS = [
    "front_left_wheel_joint",
    "front_right_wheel_joint",
    "rear_left_wheel_joint",
    "rear_right_wheel_joint",
]

# ---------------------------------------------------------------------------
# ANSI helpers  (same as check_is_topics.py)
# ---------------------------------------------------------------------------

GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def _c(text: str, colour: str) -> str:
    return f"{colour}{text}{RESET}"


def _pad(s: str, width: int) -> str:
    visible = len(_ANSI_RE.sub("", s))
    return s + " " * max(0, width - visible)


SEP  = "=" * 72
DASH = "-" * 72


def _section(title: str) -> None:
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


# ---------------------------------------------------------------------------
# IS REST: play check  (same pattern as check_is_topics.py)
# ---------------------------------------------------------------------------

def _check_is_playing() -> bool:
    try:
        import httpx
    except ImportError:
        print(_c("[warn] httpx not installed — skipping IS play check.", YELLOW))
        return True

    try:
        with httpx.Client(timeout=5) as client:
            r = client.get(f"{IS_BASE_URL}/sim/status")
        d     = r.json()
        state = d.get("state", "").upper()
        t     = d.get("time", 0.0)
        if state == "PLAYING":
            print(f"  Sim: {_c(f'PLAYING (t={t:.2f}s)', GREEN)}")
            return True
        print(f"\n  {_c(f'Sim is {state} — not PLAYING.', RED)}")
        print(f"  {_c('Press ▶ Play in Isaac Sim, then re-run this script.', YELLOW)}\n")
        return False
    except Exception:
        print(f"\n  {_c(f'Cannot reach IS REST service at {IS_BASE_URL}.', RED)}")
        print(f"  {_c('Run isaac_graph_service.py in IS Script Editor first.', YELLOW)}\n")
        return False


# ---------------------------------------------------------------------------
# ROS2 helpers  (same pattern as check_is_topics.py)
# ---------------------------------------------------------------------------

def _ros_env(domain: int = 0) -> dict:
    env = os.environ.copy()
    env["ROS_DOMAIN_ID"] = str(domain)
    return env


def _ros_cmd(cmd: str, timeout: int = 15) -> str:
    """Run a bash ROS2 command, return stdout."""
    try:
        r = subprocess.run(
            ["bash", "-c", f"source {ROS_SETUP} && {cmd}"],
            capture_output=True, text=True,
            env=_ros_env(), timeout=timeout,
        )
        return r.stdout
    except Exception:
        return ""


def _read_odom_once() -> tuple[float, float, float] | None:
    """Return (x, y, yaw_rad) from a single /odom message, or None."""
    out = _ros_cmd("timeout 3 ros2 topic echo --once --field pose.pose /odom 2>/dev/null; true", timeout=5)
    if not out:
        return None
    try:
        vals = {}
        section = None
        for line in out.splitlines():
            line = line.strip()
            if line == "position:":
                section = "pos"
            elif line == "orientation:":
                section = "ori"
            elif ":" in line:
                key, _, val = line.partition(":")
                key = key.strip()
                if section == "pos" and key in ("x", "y"):
                    vals[f"pos_{key}"] = float(val.strip())
                elif section == "ori" and key in ("x", "y", "z", "w"):
                    vals[f"q{key}"] = float(val.strip())
        x   = vals["pos_x"]
        y   = vals["pos_y"]
        qx, qy, qz, qw = vals["qx"], vals["qy"], vals["qz"], vals["qw"]
        yaw = math.atan2(2*(qw*qz + qx*qy), 1 - 2*(qy*qy + qz*qz))
        return x, y, yaw
    except Exception:
        return None


def _measure_hz(topic: str, secs: int) -> float:
    """Return average Hz of a topic over `secs` seconds."""
    out = _ros_cmd(
        f"timeout {secs} ros2 topic hz --window 10 {topic} 2>/dev/null; true",
        timeout=secs + 5,
    )
    m = re.search(r"average rate:\s*([\d.]+)", out)
    return float(m.group(1)) if m else 0.0


def _publish_twist(linear_x: float = 0.0, angular_z: float = 0.0) -> subprocess.Popen:
    """Start a background ros2 topic pub process in its own process group."""
    msg = "{" + f"linear: {{x: {linear_x}}}, angular: {{z: {angular_z}}}" + "}"
    cmd = f"source {ROS_SETUP} && ros2 topic pub /cmd_vel geometry_msgs/msg/Twist '{msg}' --rate 20 2>/dev/null"
    return subprocess.Popen(
        ["bash", "-c", cmd],
        env=_ros_env(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid,   # new process group → kills bash + ros2 child together
    )


def _kill_twist_proc(proc: subprocess.Popen) -> None:
    """Kill an entire process group started by _publish_twist."""
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except ProcessLookupError:
        pass
    proc.wait()


def _stop_robot() -> None:
    """Send zero velocity several times to ensure the AG receives it."""
    for _ in range(3):
        _ros_cmd(
            "ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "
            "'{linear: {x: 0.0}, angular: {z: 0.0}}' 2>/dev/null; true",
            timeout=5,
        )
        time.sleep(0.1)


# Register atexit so robot always stops even on crash or Ctrl+C
atexit.register(_stop_robot)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def _print_row(label: str, detail: str, ok: bool | None) -> None:
    if ok is None:
        mark = _c("?", YELLOW)
    else:
        mark = _c("✓", GREEN) if ok else _c("✗", RED)
    print(f"  [{mark}]  {_pad(label, 34)}  {detail}")


def test_stationary_turn(test_num: int, direction: str, angular_z: float) -> bool:
    _section(f"TEST {test_num} — Rotate {direction}  ({TURN_DURATION}s  angular.z={angular_z} rad/s)")
    # Snapshot odom before turn
    pose_before = _read_odom_once()

    # Start turn
    proc = _publish_twist(angular_z=angular_z)
    try:
        time.sleep(TURN_DURATION)
    finally:
        _kill_twist_proc(proc)
        _stop_robot()

    # Brief settle, then snapshot odom after
    time.sleep(0.3)
    pose_after = _read_odom_once()

    results: list[tuple[str, str, bool]] = []

    # odom publishing?
    odom_ok = pose_before is not None or pose_after is not None
    results.append(("/odom publishing", "yes" if odom_ok else "no messages received", odom_ok))

    if pose_before and pose_after:
        x0, y0, yaw0 = pose_before
        x1, y1, yaw1 = pose_after

        drift = math.hypot(x1 - x0, y1 - y0)
        drift_ok = drift <= MAX_DRIFT_M
        results.append((
            f"XY drift  (max {MAX_DRIFT_M} m)",
            f"{drift:.3f} m",
            drift_ok,
        ))

        dyaw = abs(math.degrees(math.atan2(math.sin(yaw1 - yaw0), math.cos(yaw1 - yaw0))))
        yaw_ok = dyaw >= MIN_YAW_DEG
        results.append((
            f"Yaw change  (min {MIN_YAW_DEG}°)",
            f"{dyaw:.1f}°",
            yaw_ok,
        ))

        print(f"\n  Before:  x={x0:.3f} m  y={y0:.3f} m  yaw={math.degrees(yaw0):.1f}°")
        print(f"  After :  x={x1:.3f} m  y={y1:.3f} m  yaw={math.degrees(yaw1):.1f}°\n")
    else:
        results.append(("odom pose data", "could not read before/after", False))

    for label, detail, ok in results:
        _print_row(label, detail, ok)

    return all(r[2] for r in results)


def test_drive(test_num: int, direction: str) -> bool:
    """Drive forward or backward and verify odom displacement ≥ MIN_DRIVE_M."""
    sign    = 1.0 if direction == "forward" else -1.0
    label   = f"TEST {test_num} — Drive {direction}  ({DRIVE_DURATION}s  linear.x={sign * DRIVE_SPEED} m/s)"
    _section(label)

    pose_before = _read_odom_once()

    proc = _publish_twist(linear_x=sign * DRIVE_SPEED)
    try:
        time.sleep(DRIVE_DURATION)
    finally:
        _kill_twist_proc(proc)
        _stop_robot()

    time.sleep(0.3)
    pose_after = _read_odom_once()

    if pose_before and pose_after:
        x0, y0, _ = pose_before
        x1, y1, _ = pose_after
        dist = math.hypot(x1 - x0, y1 - y0)
        ok   = dist >= MIN_DRIVE_M
        print(f"\n  Before:  x={x0:.3f} m  y={y0:.3f} m")
        print(f"  After :  x={x1:.3f} m  y={y1:.3f} m\n")
        _print_row(f"Displacement  (min {MIN_DRIVE_M} m)", f"{dist:.3f} m", ok)
        return ok
    else:
        _print_row("odom pose data", "could not read before/after", False)
        return False


def test_lidar() -> bool:
    _section(f"TEST 7 — Lidar cloud  ({LIDAR_CHECK_SECS}s listen on /unilidar/cloud)")

    hz = _measure_hz("/unilidar/cloud", LIDAR_CHECK_SECS)
    ok = hz > 0.0
    _print_row("/unilidar/cloud rate", f"{hz:.1f} Hz" if ok else "0 Hz — no messages", ok)
    return ok


# ---------------------------------------------------------------------------
# Section 0: Topic health
# ---------------------------------------------------------------------------

def _topic_exists(topic: str) -> bool:
    out = _ros_cmd(f"timeout 3 ros2 topic info {topic} 2>/dev/null; true", timeout=5)
    return "Publisher count:" in out and "Publisher count: 0" not in out


def test_topic_health() -> bool:
    _section("SECTION 0 — IS Output Topic Health")

    results: list[tuple[str, str, bool]] = []

    # Rate-based topics (published dynamically while sim plays)
    for topic, min_hz, label in [
        ("/odom",           MIN_ODOM_HZ,  "nav_msgs/Odometry"),
        ("/tf",             MIN_TF_HZ,    "tf2_msgs/TFMessage  (dynamic)"),
        ("/joint_states",   MIN_JS_HZ,    "sensor_msgs/JointState"),
        ("/unilidar/cloud", MIN_LIDAR_HZ, "sensor_msgs/PointCloud2"),
    ]:
        hz = _measure_hz(topic, RATE_CHECK_SECS)
        ok = hz >= min_hz
        results.append((
            f"{topic}",
            f"{hz:.1f} Hz  (min {min_hz:.0f})  [{label}]",
            ok,
        ))

    # /tf_static — TRANSIENT_LOCAL, not rate-checkable; just verify publisher exists
    tf_static_ok = _topic_exists("/tf_static")
    results.append((
        "/tf_static",
        "publisher present" if tf_static_ok else "no publisher found",
        tf_static_ok,
    ))

    for label, detail, ok in results:
        _print_row(label, detail, ok)

    return all(r[2] for r in results)


# ---------------------------------------------------------------------------
# Section 1: TF tree
# ---------------------------------------------------------------------------

def _read_tf_dynamic() -> list[tuple[str, str]]:
    """Return list of (frame_id, child_frame_id) from a single /tf message."""
    out = _ros_cmd("timeout 3 ros2 topic echo --once /tf 2>/dev/null; true", timeout=5)
    pairs: list[tuple[str, str]] = []
    frame_id = child_frame_id = None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("frame_id:"):
            frame_id = line.split(":", 1)[1].strip().strip("'\"")
        elif line.startswith("child_frame_id:"):
            child_frame_id = line.split(":", 1)[1].strip().strip("'\"")
            if frame_id and child_frame_id:
                pairs.append((frame_id, child_frame_id))
                frame_id = child_frame_id = None
    return pairs


def _read_tf_static() -> list[tuple[str, str]]:
    """Return list of (frame_id, child_frame_id) from /tf_static (TRANSIENT_LOCAL)."""
    out = _ros_cmd(
        "timeout 3 ros2 topic echo --once --qos-durability transient_local /tf_static 2>/dev/null; true",
        timeout=5,
    )
    pairs: list[tuple[str, str]] = []
    frame_id = child_frame_id = None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("frame_id:"):
            frame_id = line.split(":", 1)[1].strip().strip("'\"")
        elif line.startswith("child_frame_id:"):
            child_frame_id = line.split(":", 1)[1].strip().strip("'\"")
            if frame_id and child_frame_id:
                pairs.append((frame_id, child_frame_id))
                frame_id = child_frame_id = None
    return pairs


def _read_odom_frames() -> tuple[str, str] | None:
    """Return (frame_id, child_frame_id) from /odom header, or None."""
    out = _ros_cmd("timeout 3 ros2 topic echo --once /odom 2>/dev/null; true", timeout=5)
    frame_id = child_frame_id = None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("frame_id:"):
            frame_id = line.split(":", 1)[1].strip().strip("'\"")
        elif line.startswith("child_frame_id:"):
            child_frame_id = line.split(":", 1)[1].strip().strip("'\"")
    if frame_id and child_frame_id:
        return frame_id, child_frame_id
    return None


def test_tf_tree() -> bool:
    _section("SECTION 1 — TF Tree")

    results: list[tuple[str, str, bool]] = []

    # Check /odom frame IDs
    frames = _read_odom_frames()
    if frames:
        fid, cfid = frames
        fid_ok  = fid  == "odom"
        cfid_ok = cfid == "base_link"
        results.append(("/odom frame_id",       f'"{fid}"',  fid_ok))
        results.append(("/odom child_frame_id",  f'"{cfid}"', cfid_ok))
    else:
        results.append(("/odom frames", "could not read message", False))

    # Check /tf has odom→base_link
    tf_pairs = _read_tf_dynamic()
    odom_bl = ("odom", "base_link") in tf_pairs
    results.append((
        "/tf  odom → base_link",
        "present" if odom_bl else f"not found  (got: {tf_pairs or 'none'})",
        odom_bl,
    ))

    # Check /tf_static has base_link→wheel frames
    static_pairs = _read_tf_static()
    static_children = {c for _, c in static_pairs}
    for joint in WHEEL_JOINTS:
        link = joint.replace("_joint", "").replace("front_left_wheel", "front_left_wheel") \
                     .replace("front_right_wheel", "front_right_wheel") \
                     .replace("rear_left_wheel", "rear_left_wheel") \
                     .replace("rear_right_wheel", "rear_right_wheel")
        # RSP publishes TF for the child link of each joint
        wheel_link = joint.replace("_joint", "")
        present = wheel_link in static_children
        results.append((
            f"/tf_static  base_link → {wheel_link}",
            "present" if present else f"missing  (got: {sorted(static_children)})",
            present,
        ))

    for label, detail, ok in results:
        _print_row(label, detail, ok)

    if static_pairs:
        print(f"\n  All /tf_static frames:")
        for parent, child in sorted(static_pairs):
            print(f"    {DIM}{parent} → {child}{RESET}")

    return all(r[2] for r in results)


# ---------------------------------------------------------------------------
# Section 2: Joint states
# ---------------------------------------------------------------------------

def _read_joint_names() -> list[str]:
    """Return joint names from a single /joint_states message."""
    out = _ros_cmd("timeout 3 ros2 topic echo --once /joint_states 2>/dev/null; true", timeout=5)
    names: list[str] = []
    in_name_block = False
    for line in out.splitlines():
        line = line.strip()
        if line == "name:":
            in_name_block = True
            continue
        if in_name_block:
            if line.startswith("-"):
                names.append(line.lstrip("- ").strip().strip("'\""))
            else:
                in_name_block = False
    return names


def test_joint_states() -> bool:
    _section("SECTION 2 — Joint States")

    results: list[tuple[str, str, bool]] = []

    names = _read_joint_names()
    if not names:
        _print_row("/joint_states", "no message received", False)
        return False

    print(f"\n  Published joints: {_c(', '.join(names), DIM)}\n")

    for joint in WHEEL_JOINTS:
        present = joint in names
        results.append((joint, "present" if present else "MISSING", present))

    for label, detail, ok in results:
        _print_row(label, detail, ok)

    return all(r[2] for r in results)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"\n{SEP}")
    print(f"  {_c('jaska_v2 IS output smoke test', BOLD)}")
    print(SEP)

    if not _check_is_playing():
        sys.exit(1)

    # Warm up DDS discovery so first topic echo isn't slow
    print(f"  {_c('Warming up DDS...', DIM)}", end="", flush=True)
    _ros_cmd("timeout 2 ros2 topic echo --once /odom 2>/dev/null; true", timeout=4)
    print(_c(" done", DIM))

    passed = []
    passed.append(("Topic Health",    test_topic_health()))
    passed.append(("TF Tree",         test_tf_tree()))
    passed.append(("Joint States",    test_joint_states()))
    passed.append(("Rotate CCW",      test_stationary_turn(3, "left / CCW",  +ANGULAR_Z)))
    passed.append(("Rotate CW",       test_stationary_turn(4, "right / CW",  -ANGULAR_Z)))
    passed.append(("Drive forward",   test_drive(5, "forward")))
    passed.append(("Drive backward",  test_drive(6, "backward")))
    passed.append(("Lidar cloud",     test_lidar()))

    n_pass = sum(1 for _, r in passed if r)
    total  = len(passed)
    colour = GREEN if n_pass == total else RED

    print(f"\n{SEP}")
    print(f"  {'Test':<22}  Result")
    print(DASH)
    for name, ok in passed:
        mark = _c("✓ PASS", GREEN) if ok else _c("✗ FAIL", RED)
        print(f"  {name:<22}  {mark}")
    print(SEP)
    print(f"  Overall: {_c(f'{n_pass}/{total} passed', colour)}")
    print(f"{SEP}\n")
    sys.exit(0 if all(r for _, r in passed) else 1)


if __name__ == "__main__":
    main()
