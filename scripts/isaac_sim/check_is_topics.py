#!/home/haito/haito_dev/ros2_ws/src/jaska_description/.venv/bin/python
"""
check_is_topics.py — Isaac Sim topic inspector for jaska_v2 (rates + QoS in one pass).

  Section 1 — Summary table (one row per topic):
      domain  topic  rate  AG QoS (from live IS stage)  DDS pub QoS  compatibility

  Section 2 — DDS endpoint detail (ros2 topic info --verbose per topic):
      per-topic: every publisher and subscriber node + per-endpoint QoS

  Section 3 — OmniGraph QoS profiles reference (from live IS stage, not a file):
      profile name → depth / durability / history / reliability

All ROS2 measurements run in parallel across domains.
Sim must be PLAYING for publisher topics and DDS QoS to be visible.

USAGE:
  python check_is_topics.py
  SAMPLE_TIME=10 python check_is_topics.py

ENV OVERRIDES:
  SAMPLE_TIME=8               Seconds to sample each topic rate (default: 8)
  IS_BASE_URL=http://localhost:8011  Isaac Sim REST service base URL
"""

import os
import re
import subprocess
import sys
from concurrent.futures import Future, ThreadPoolExecutor, as_completed

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
SAMPLE_TIME  = int(os.environ.get("SAMPLE_TIME", "8"))
IS_BASE_URL  = os.environ.get("IS_BASE_URL", "http://localhost:8011")
ROS_SETUP    = "/opt/ros/jazzy/setup.bash"
FASTDDS_XML  = os.path.join(SCRIPT_DIR, "fastdds_large_data.xml")

# (role, domain, topic, note)
# role "pub" = IS publishes, external node subscribes
# role "sub" = IS subscribes, external node publishes
TOPICS = [
    # IS subscribes (ROS2 → IS)
    ("sub", 0, "/cmd_vel",                  "diff drive command → jaska_v2"),
    # IS publishes (IS → ROS2)
    ("pub", 0, "/clock",                     "sim clock → use_sim_time consumers"),
    ("pub", 0, "/odom",                      "wheel odometry (IsaacComputeOdometry)"),
    ("pub", 0, "/joint_states",              "wheel joint positions/velocities"),
    ("pub", 0, "/tf",                        "robot TF tree (odom → base_link → joints)"),
    ("pub", 0, "/scan",                      "2D laser scan (RTX lidar → Nav2/SLAM)"),
    ("pub", 0, "/unilidar/cloud",            "3D point cloud — Uni-Lidar L1"),
]

# ---------------------------------------------------------------------------
# ANSI helpers
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
    """Left-justify *s* to *width* visible characters, ignoring ANSI escape codes."""
    visible = len(_ANSI_RE.sub("", s))
    return s + " " * max(0, width - visible)


# ---------------------------------------------------------------------------
# IS REST: sim status + live AG QoS
# ---------------------------------------------------------------------------

def _fetch_is_data() -> tuple[str, dict, dict]:
    """
    Returns (sim_status_str, ag_profiles, ag_topic_map).
    Falls back gracefully if the service is unreachable.
    """
    try:
        import httpx
    except ImportError:
        return "httpx not installed — run: pip install httpx", {}, {}

    try:
        with httpx.Client(timeout=5) as client:
            status_r = client.get(f"{IS_BASE_URL}/sim/status")
            qos_r    = client.get(f"{IS_BASE_URL}/graph/qos")

        d = status_r.json()
        sim_status = f"{d['state']} (t={d['time']:.2f}s)"

        if qos_r.status_code == 200:
            qos = qos_r.json()
            return sim_status, qos.get("profiles", {}), qos.get("topics", {})
        return sim_status, {}, {}

    except Exception:
        return "IS service unavailable", {}, {}


# ---------------------------------------------------------------------------
# ROS2 measurements
# ---------------------------------------------------------------------------

def _ros_env(domain: int) -> dict:
    env = os.environ.copy()
    env["FASTRTPS_DEFAULT_PROFILES_FILE"] = FASTDDS_XML
    env["RMW_FASTRTPS_USE_QOS_FROM_XML"]  = "1"
    env["FASTDDS_SHM_TRANSPORT_DISABLED"] = "1"
    env["ROS_DOMAIN_ID"]                  = str(domain)
    return env


def _measure_hz(domain: int, topic: str) -> float:
    """Run `ros2 topic hz` for SAMPLE_TIME seconds; return average rate or 0.0."""
    cmd = (
        f"source {ROS_SETUP} && "
        f"timeout {SAMPLE_TIME} ros2 topic hz --window 10 {topic} 2>/dev/null; true"
    )
    try:
        r = subprocess.run(
            ["bash", "-c", cmd],
            capture_output=True, text=True,
            env=_ros_env(domain), timeout=SAMPLE_TIME + 5,
        )
        m = re.search(r"average rate:\s*([\d.]+)", r.stdout)
        return float(m.group(1)) if m else 0.0
    except Exception:
        return 0.0


def _topic_info_raw(domain: int, topic: str) -> str:
    """Run `ros2 topic info --verbose`; return stdout."""
    cmd = (
        f"source {ROS_SETUP} && "
        f"ros2 topic info --verbose --spin-time 5 '{topic}' 2>/dev/null"
    )
    try:
        r = subprocess.run(
            ["bash", "-c", cmd],
            capture_output=True, text=True,
            env=_ros_env(domain), timeout=15,
        )
        return r.stdout
    except Exception:
        return ""


def _parse_endpoints(raw: str) -> list[dict]:
    """Parse `ros2 topic info --verbose` into a list of endpoint dicts.

    In Jazzy, ros2 topic info outputs fields in this order per endpoint:
        Node name: ...
        Node namespace: ...
        Topic type: ...
        Endpoint type: PUBLISHER | SUBSCRIPTION
        GID: ...
        QoS profile:
          Reliability: ...
          Durability: ...
    """
    endpoints: list[dict] = []
    cur: dict = {}

    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("Node name:"):
            # Start of a new endpoint block
            if cur.get("type"):
                endpoints.append(cur)
            cur = {
                "type": "",
                "node": line.split("Node name:", 1)[1].strip() or "_UNKNOWN_",
                "reliability": "",
                "durability": "",
            }
        elif "Endpoint type: PUBLISHER" in line:
            cur["type"] = "PUBLISHER"
        elif "Endpoint type: SUBSCRIPTION" in line:
            cur["type"] = "SUBSCRIBER"
        elif line.startswith("Reliability:"):
            cur["reliability"] = line.split("Reliability:", 1)[1].strip()
        elif line.startswith("Durability:"):
            cur["durability"] = line.split("Durability:", 1)[1].strip()

    if cur.get("type"):
        endpoints.append(cur)
    return endpoints


# ---------------------------------------------------------------------------
# QoS compatibility helper
# ---------------------------------------------------------------------------

def _compat(ag_rel: str, dds_pub_rel: str) -> str:
    """
    DDS QoS compatibility rule:
      publisher BEST_EFFORT + subscriber RELIABLE → subscriber receives NO data.
    Here we check if the AG-coded QoS (what IS uses) matches the observed DDS publisher QoS,
    and whether the combination would be problematic for subscribers.
    """
    if not ag_rel or not dds_pub_rel:
        return ""
    ag_reliable  = "reliable" in ag_rel.lower()
    dds_reliable = dds_pub_rel == "RELIABLE"
    if ag_reliable == dds_reliable:
        return _c("✓ match", GREEN)
    return _c("⚠ mismatch", RED)


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

SEP  = "=" * 82
DASH = "-" * 82


def _section(title: str) -> None:
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


def _print_summary_table(
    section_role: str,
    label: str,
    hz_results: dict,
    endpoints_map: dict,
    ag_profiles: dict,
    ag_topic_map: dict,
    is_online: bool,
) -> None:
    _section(label)
    print(
        f"  {'D':<4} "
        f"{'TOPIC':<52} "
        f"{'RATE':<11} "
        f"{'AG QoS':<16} "
        f"{'DDS PUB QoS':<16} "
        f"STATUS"
    )
    print(f"  {DASH}")

    for entry in TOPICS:
        role, domain, topic, note = entry
        if role != section_role:
            continue

        # Rate
        hz = hz_results.get(entry, 0.0)
        rate_str = _c(f"{hz:.1f} Hz", GREEN if hz > 0.0 else RED)

        # AG QoS (from live IS stage)
        ag_rel = ""
        if is_online:
            profile_name = ag_topic_map.get(topic, "")
            if profile_name and profile_name in ag_profiles:
                ag_rel = ag_profiles[profile_name].get("reliability", "?")
                ag_str = _c(ag_rel, GREEN if "reliable" in ag_rel.lower() else YELLOW)
            else:
                ag_str = _c("--", DIM)
        else:
            ag_str = _c("offline", YELLOW)

        # DDS publisher QoS (from live ros2 topic info)
        eps     = endpoints_map.get(entry, [])
        pub_eps = [e for e in eps if e["type"] == "PUBLISHER"]
        if pub_eps:
            dds_rel = pub_eps[0]["reliability"]
            dds_str = _c(dds_rel, GREEN if dds_rel == "RELIABLE" else YELLOW)
        else:
            dds_rel = ""
            dds_str = _c("--", DIM)

        compat = _compat(ag_rel, dds_rel)

        print(
            f"  {domain:<4} "
            f"{_pad(topic, 52)} "
            f"{_pad(rate_str, 19)} "
            f"{_pad(ag_str, 24)} "
            f"{_pad(dds_str, 24)} "
            f"{compat}"
        )
        print(f"  {_c('     ' + note, DIM)}")


def _print_dds_detail(endpoints_map: dict) -> None:
    _section("DDS Endpoint Detail  (ros2 topic info --verbose)")

    for entry in TOPICS:
        role, domain, topic, note = entry
        eps = endpoints_map.get(entry, [])
        if not eps:
            continue

        print(f"\n  [D{domain}] {topic}  {_c('(' + note + ')', DIM)}")
        print(f"  {'TYPE':<12}  {'NODE':<48}  {'RELIABILITY':<14}  DURABILITY")
        print(f"  {'-' * 82}")

        pub_rel = ""
        for ep in eps:
            rel  = ep["reliability"]
            dur  = ep["durability"] or "VOLATILE"
            col  = GREEN if rel == "RELIABLE" else (YELLOW if rel == "BEST_EFFORT" else RESET)
            flag = ""
            if ep["type"] == "PUBLISHER" and not pub_rel:
                pub_rel = rel
            if ep["type"] == "SUBSCRIBER" and pub_rel == "BEST_EFFORT" and rel == "RELIABLE":
                flag = _c("  ⚠ pub=BEST_EFFORT → subscriber receives no data", RED)

            print(f"  {ep['type']:<12}  {ep['node']:<48}  {_pad(_c(rel, col), 22)}  {dur}{flag}")

        print()
        if pub_rel == "BEST_EFFORT":
            print(f"  {_c('⚠  Publisher BEST_EFFORT — RELIABLE subscribers will receive NO data', RED)}")
        elif pub_rel == "RELIABLE":
            print(f"  {_c('✓  Publisher RELIABLE — compatible with all subscribers', GREEN)}")
        else:
            print(f"  {_c('⚠  Publisher not visible — IS may not be PLAYING', YELLOW)}")


def _print_ag_profiles(ag_profiles: dict) -> None:
    if not ag_profiles:
        return
    _section("OmniGraph QoS Profiles  (live IS stage — not from USDA file)")
    print(f"  {'PROFILE':<40}  {'RELIABILITY':<14}  {'DURABILITY':<12}  {'HISTORY':<12}  DEPTH")
    print(f"  {DASH}")
    for name, p in sorted(ag_profiles.items()):
        rel = p.get("reliability", "?")
        col = GREEN if "reliable" in rel.lower() else YELLOW
        print(
            f"  {name:<40}  "
            f"{_pad(_c(rel, col), 22)}  "
            f"{p.get('durability','?'):<12}  "
            f"{p.get('history','?'):<12}  "
            f"{p.get('depth','?')}"
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"\n{SEP}")

    # ── Fetch IS status + live AG QoS (fast REST call) ───────────────────
    sim_status, ag_profiles, ag_topic_map = _fetch_is_data()
    is_online = bool(ag_profiles or "PLAYING" in sim_status or "PAUSED" in sim_status or "STOPPED" in sim_status)

    playing = sim_status.startswith("PLAYING")
    status_col = GREEN if playing else (YELLOW if "unavailable" not in sim_status else RED)
    print(f"  {_c('Isaac Sim Topic Inspector', BOLD)}  |  Sim: {_c(sim_status, status_col)}")
    print(SEP)

    if not playing:
        print(f"\n  {_c('WARNING: Sim is not PLAYING — publisher topics and DDS QoS will not be visible.', YELLOW)}\n")

    # ── Run all ROS2 measurements in parallel ─────────────────────────────
    print(f"\n  Sampling {len(TOPICS)} topics for {SAMPLE_TIME}s (hz + QoS in parallel)...")

    hz_results:    dict[tuple, float]      = {}
    endpoints_map: dict[tuple, list[dict]] = {}

    hz_futures:   dict[Future, tuple] = {}
    info_futures: dict[Future, tuple] = {}

    with ThreadPoolExecutor() as pool:
        for entry in TOPICS:
            _, domain, topic, _ = entry
            hz_futures[pool.submit(_measure_hz,       domain, topic)] = entry
            info_futures[pool.submit(_topic_info_raw, domain, topic)] = entry

        all_futures = list(hz_futures) + list(info_futures)
        hz_set = set(hz_futures)

        for f in as_completed(all_futures):
            if f in hz_set:
                hz_results[hz_futures[f]]    = f.result()
            else:
                endpoints_map[info_futures[f]] = _parse_endpoints(f.result())

    # ── Section 1: Summary tables ─────────────────────────────────────────
    _print_summary_table(
        "pub", "IS PUBLISHES  (external node subscribes)",
        hz_results, endpoints_map, ag_profiles, ag_topic_map, is_online,
    )
    _print_summary_table(
        "sub", "IS SUBSCRIBES (external node must publish)",
        hz_results, endpoints_map, ag_profiles, ag_topic_map, is_online,
    )

    # ── Section 2: DDS endpoint detail ────────────────────────────────────
    _print_dds_detail(endpoints_map)

    # ── Section 3: AG QoS profiles reference ─────────────────────────────
    _print_ag_profiles(ag_profiles)

    print(f"\n{SEP}\n")


if __name__ == "__main__":
    main()
