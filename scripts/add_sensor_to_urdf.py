#!/usr/bin/env python3
"""
Interactive script to add a sensor to a base robot URDF.

Usage:
    python3 add_sensor_to_urdf.py [--urdf <path>] [--meshes-dir <path>]

If --urdf or --meshes-dir are not provided, the script will prompt
interactively with a list of discovered files/directories.
"""

import argparse
import os
import re
import xml.etree.ElementTree as ET

# ── helpers ──────────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
PKG_ROOT = os.path.join(SCRIPT_DIR, "..")   # .../jaska_description/
PKG_NAME = "jaska_description"


def _prompt_choice(prompt: str, choices: list[str]) -> str:
    """Present a numbered list and return the chosen string."""
    print(f"\n{prompt}")
    for i, c in enumerate(choices, 1):
        print(f"  {i:2d}. {c}")
    while True:
        raw = input("Enter number: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(choices):
            return choices[int(raw) - 1]
        print(f"  Please enter a number between 1 and {len(choices)}.")


def _prompt_float(prompt: str, default: float = 0.0) -> float:
    while True:
        raw = input(f"{prompt} [{default}]: ").strip()
        if raw == "":
            return default
        try:
            return float(raw)
        except ValueError:
            print("  Please enter a valid number (e.g. 0.1 or -0.05).")


def _prompt_str(prompt: str, default: str = "") -> str:
    raw = input(f"{prompt} [{default}]: ").strip()
    return raw if raw else default


# ── URDF helpers ─────────────────────────────────────────────────────────────

def get_links(urdf_path: str) -> list[str]:
    """Return all link names from a URDF file."""
    tree = ET.parse(urdf_path)
    root = tree.getroot()
    return [link.attrib["name"] for link in root.findall("link")]


def build_sensor_xml(
    sensor_name: str,
    mesh_file: str,
    parent_link: str,
    joint_name: str,
    xyz: tuple[float, float, float],
    rpy: tuple[float, float, float],
    scale: tuple[float, float, float],
    mass: float,
    pkg_name: str,
    meshes_rel_path: str,   # e.g. meshes/jaska_v2/sensors
) -> str:
    """Return the XML snippet (link + joint) for the sensor."""
    mesh_pkg_path = f"package://{pkg_name}/{meshes_rel_path}/{mesh_file}"
    xyz_str = " ".join(f"{v:.6f}" for v in xyz)
    rpy_str = " ".join(f"{v:.6f}" for v in rpy)
    scale_str = " ".join(f"{v}" for v in scale)

    # Simple box inertia placeholder (1 cm cube)
    side = 0.01
    ixx = iyy = izz = mass * side**2 / 6

    return f"""
  <!-- Sensor: {sensor_name} -->
  <link name="{sensor_name}">
    <visual>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry>
        <mesh filename="{mesh_pkg_path}" scale="{scale_str}"/>
      </geometry>
    </visual>
    <collision>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <geometry>
        <mesh filename="{mesh_pkg_path}" scale="{scale_str}"/>
      </geometry>
    </collision>
    <inertial>
      <mass value="{mass:.4f}"/>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <inertia ixx="{ixx:.6e}" ixy="0" ixz="0"
               iyy="{iyy:.6e}" iyz="0"
               izz="{izz:.6e}"/>
    </inertial>
  </link>

  <joint name="{joint_name}" type="fixed">
    <parent link="{parent_link}"/>
    <child link="{sensor_name}"/>
    <origin xyz="{xyz_str}" rpy="{rpy_str}"/>
  </joint>
"""


def inject_into_urdf(urdf_path: str, xml_snippet: str, output_path: str) -> None:
    """Insert xml_snippet before </robot> and write to output_path."""
    with open(urdf_path, "r") as f:
        content = f.read()

    if "</robot>" not in content:
        raise ValueError(f"Could not find </robot> closing tag in {urdf_path}")

    updated = content.replace("</robot>", xml_snippet + "\n</robot>", 1)

    with open(output_path, "w") as f:
        f.write(updated)


# ── main ─────────────────────────────────────────────────────────────────────

def _prompt_urdf_path() -> str:
    """Discover available URDF files and let user pick or enter a custom path."""
    urdf_dir = os.path.join(PKG_ROOT, "urdf")
    available = sorted(
        f for f in os.listdir(urdf_dir) if f.endswith(".urdf")
    ) if os.path.isdir(urdf_dir) else []

    print("\nAvailable URDF files in package urdf/ directory:")
    if available:
        for i, f in enumerate(available, 1):
            print(f"  {i:2d}. {f}")
        print(f"  {len(available)+1:2d}. Enter a custom path")
        while True:
            raw = input("Enter number: ").strip()
            if raw.isdigit():
                n = int(raw)
                if 1 <= n <= len(available):
                    return os.path.join(urdf_dir, available[n - 1])
                if n == len(available) + 1:
                    break
            print(f"  Please enter a number between 1 and {len(available)+1}.")
    else:
        print("  (none found)")

    while True:
        raw = input("Enter full path to URDF file: ").strip()
        if raw:
            return raw
        print("  Path cannot be empty.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Interactively add sensors to a robot URDF.")
    parser.add_argument(
        "--urdf",
        default=None,
        help="Path to the base robot URDF file (will prompt if not given).",
    )
    parser.add_argument(
        "--meshes-dir",
        default=None,
        help="Directory containing sensor mesh files (will prompt if not given).",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  URDF Sensor Addition Tool")
    print("=" * 60)

    # ── URDF selection ────────────────────────────────────────────────────────
    if args.urdf:
        urdf_path = os.path.realpath(args.urdf)
    else:
        urdf_path = os.path.realpath(_prompt_urdf_path())

    if not os.path.isfile(urdf_path):
        print(f"ERROR: URDF file not found: {urdf_path}")
        return

    # ── Meshes dir selection ──────────────────────────────────────────────────
    if args.meshes_dir:
        meshes_dir = os.path.realpath(args.meshes_dir)
    else:
        # Auto-detect: look for sensors/ dirs under meshes/
        meshes_root = os.path.join(PKG_ROOT, "meshes")
        sensor_dirs = sorted(
            os.path.join(root, d)
            for root, dirs, _ in os.walk(meshes_root)
            for d in dirs if d == "sensors"
        ) if os.path.isdir(meshes_root) else []

        if sensor_dirs:
            print("\nAvailable sensor mesh directories:")
            for i, d in enumerate(sensor_dirs, 1):
                print(f"  {i:2d}. {os.path.relpath(d, PKG_ROOT)}")
            print(f"  {len(sensor_dirs)+1:2d}. Enter a custom path")
            while True:
                raw = input("Enter number: ").strip()
                if raw.isdigit():
                    n = int(raw)
                    if 1 <= n <= len(sensor_dirs):
                        meshes_dir = os.path.realpath(sensor_dirs[n - 1])
                        break
                    if n == len(sensor_dirs) + 1:
                        meshes_dir = os.path.realpath(input("Enter full path to sensor meshes directory: ").strip())
                        break
                print(f"  Please enter a number between 1 and {len(sensor_dirs)+1}.")
        else:
            meshes_dir = os.path.realpath(input("Enter full path to sensor meshes directory: ").strip())

    if not os.path.isdir(meshes_dir):
        print(f"ERROR: Sensor meshes directory not found: {meshes_dir}")
        return

    # Derive package-relative path for mesh URIs
    pkg_root_real = os.path.realpath(PKG_ROOT)
    meshes_rel = os.path.relpath(meshes_dir, pkg_root_real)   # e.g. meshes/jaska_v2/sensors

    # Derive default output name: jaska_v2.urdf → jaska_with_sensors_v2.urdf
    urdf_dir = os.path.dirname(urdf_path)
    urdf_basename = os.path.basename(urdf_path)                # jaska_v2.urdf
    match = re.match(r"^(.+?)(_v\d+)?\.urdf$", urdf_basename)
    if match:
        base_part = match.group(1)                             # jaska_v2  → jaska
        version_part = match.group(2) or ""                    # _v2
        default_output_name = f"{base_part}_with_sensors{version_part}.urdf"
    else:
        default_output_name = urdf_basename.replace(".urdf", "_with_sensors.urdf")

    print(f"\n  Base URDF    : {urdf_path}")
    print(f"  Sensor meshes: {meshes_dir}")
    print("=" * 60)

    # Discover available sensor meshes
    mesh_extensions = {".stl", ".dae", ".obj"}
    available_meshes = sorted(
        f for f in os.listdir(meshes_dir)
        if os.path.splitext(f)[1].lower() in mesh_extensions
    )

    if not available_meshes:
        print("\nNo mesh files found in the sensors directory.")
        print("Add .stl/.dae/.obj files to:")
        print(f"  {meshes_dir}")
        return

    # Read available links from the URDF
    available_links = get_links(urdf_path)

    accumulated_snippets: list[str] = []
    added_links: list[str] = []

    while True:
        print(f"\n{'─'*60}")
        action = _prompt_choice(
            "What would you like to do?",
            ["Add a sensor", "Finish and save output URDF"],
        )

        if action == "Finish and save output URDF":
            break

        # ── Select sensor mesh ────────────────────────────────────────────
        mesh_file = _prompt_choice("Select sensor mesh file:", available_meshes)
        stem = os.path.splitext(mesh_file)[0]   # default sensor name

        # ── Sensor name ───────────────────────────────────────────────────
        sensor_name = _prompt_str(
            "Sensor link name (no spaces, e.g. lidar, zed_camera)",
            default=stem,
        )
        sensor_name = sensor_name.replace(" ", "_")

        # Check for duplicate link name
        all_links = available_links + added_links
        if sensor_name in all_links:
            print(f"  WARNING: A link named '{sensor_name}' already exists.")
            sensor_name = _prompt_str("Enter a different sensor name", default=sensor_name + "_2")

        # ── Joint name ────────────────────────────────────────────────────
        joint_name = _prompt_str(
            "Joint name",
            default=f"{sensor_name}_joint",
        )

        # ── Parent link ───────────────────────────────────────────────────
        print("\nAvailable parent links (from base URDF + sensors added so far):")
        all_links = available_links + added_links
        parent_link = _prompt_choice("Select parent link:", all_links)

        # ── Placement ─────────────────────────────────────────────────────
        print("\nEnter placement relative to parent link:")
        x = _prompt_float("  x (m)", 0.0)
        y = _prompt_float("  y (m)", 0.0)
        z = _prompt_float("  z (m)", 0.0)
        print("Enter orientation (roll/pitch/yaw in radians):")
        roll  = _prompt_float("  roll  (rad)", 0.0)
        pitch = _prompt_float("  pitch (rad)", 0.0)
        yaw   = _prompt_float("  yaw   (rad)", 0.0)

        # ── Scale ─────────────────────────────────────────────────────────
        print("\nMesh scale (use 0.001 for mm-exported STLs, 1.0 for m-exported STLs):")
        scale_uniform = input("  Uniform scale (leave blank to set per-axis) [1.0]: ").strip()
        if scale_uniform:
            try:
                sv = float(scale_uniform)
                scale = (sv, sv, sv)
            except ValueError:
                print("  Invalid value, defaulting to 1.0")
                scale = (1.0, 1.0, 1.0)
        else:
            sx = _prompt_float("  scale x", 1.0)
            sy = _prompt_float("  scale y", 1.0)
            sz = _prompt_float("  scale z", 1.0)
            scale = (sx, sy, sz)

        # ── Mass ──────────────────────────────────────────────────────────
        mass = _prompt_float("Sensor mass (kg)", 0.1)

        # ── Build snippet ─────────────────────────────────────────────────
        snippet = build_sensor_xml(
            sensor_name=sensor_name,
            mesh_file=mesh_file,
            parent_link=parent_link,
            joint_name=joint_name,
            xyz=(x, y, z),
            rpy=(roll, pitch, yaw),
            scale=scale,
            mass=mass,
            pkg_name=PKG_NAME,
            meshes_rel_path=meshes_rel,
        )
        accumulated_snippets.append(snippet)
        added_links.append(sensor_name)

        print(f"\n  ✓ Queued sensor '{sensor_name}' attached to '{parent_link}'.")

    # ── Save output ───────────────────────────────────────────────────────────
    if not accumulated_snippets:
        print("\nNo sensors added. Exiting without saving.")
        return

    output_name = _prompt_str(
        "\nOutput URDF filename (in same directory as base URDF)",
        default=default_output_name,
    )
    output_path = os.path.join(urdf_dir, output_name)

    combined_snippet = "".join(accumulated_snippets)
    inject_into_urdf(urdf_path, combined_snippet, output_path)

    print(f"\n{'='*60}")
    print(f"  Saved: {output_path}")
    print(f"  Added sensors: {', '.join(added_links)}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
