#!/home/haito/haito_dev/ros2_ws/src/jaska_description/.venv/bin/python
"""
prim_tool.py — save or hot-reload /World/jaska_v2 from any open IS scene.

PREREQUISITE
  Isaac Sim must be running with the graph service (use the `is` alias).
  Swagger UI: http://localhost:8011/docs

WHAT IT DOES
  Scoped to the /World/jaska_v2 prim subtree only — works whether you have
  jaska_v2.usda, obstacle_world_with_jaska_v2.usda, or any other world open.

  save    Extract the source layer for /World/jaska_v2 from the running stage
          and write it to jaska_v2_wip.usda on disk.

  load    Inject any robot USDA into /World/jaska_v2 in the running stage.
          The file does NOT need to be already loaded — works with any USDA.

USAGE
  python prim_tool.py save
  python prim_tool.py save   /path/to/output.usda

  python prim_tool.py reload
  python prim_tool.py reload /path/to/file.usda

WORKFLOW
  1.  Start IS with `is` alias, open any world that includes jaska_v2
  2.  Tweak prims / nodes in the IS GUI
  3.  python prim_tool.py save          ← write source layer → jaska_v2_wip.usda
  4.  code ../../usd/jaska_v2_wip.usda  ← inspect / hand-edit
  5.  python prim_tool.py load          ← inject edited USDA into /World/jaska_v2

ENV OVERRIDES
  IS_BASE_URL=http://localhost:8011    Isaac Sim REST service base URL
  PRIM_PATH=/World/jaska_v2           USD prim path to save/reload
  SCENE_FILE=<auto>                   Override default jaska_v2.usda path
"""

import argparse
import os
import sys

try:
    import httpx
except ImportError:
    sys.exit("ERROR: httpx not installed.  Run: pip install httpx --break-system-packages")

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
IS_BASE_URL  = os.environ.get("IS_BASE_URL", "http://localhost:8011")
PRIM_PATH    = os.environ.get("PRIM_PATH",   "/World/jaska_v2")
_PKG_ROOT    = os.path.dirname(os.path.dirname(SCRIPT_DIR))   # .../jaska_description/
DEFAULT_USDA = os.environ.get(
    "SCENE_FILE",
    os.path.join(_PKG_ROOT, "usd", "jaska_v2", "jaska_v2.usda"),
)


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------

def _post(endpoint: str, payload: dict) -> dict:
    """POST to an omni.services.core endpoint (query params, not JSON body)."""
    url = f"{IS_BASE_URL}{endpoint}"
    try:
        r = httpx.post(url, params=payload, timeout=120)
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        sys.exit(
            f"ERROR: Cannot connect to Isaac Sim at {IS_BASE_URL}.\n"
            "  -> Launch Isaac Sim with the `is` alias (starts REST service on port 8011)."
        )
    except httpx.HTTPStatusError as e:
        sys.exit(f"ERROR: HTTP {e.response.status_code} from {url}:\n{e.response.text}")


def _resolve_path(raw: str | None) -> str:
    if not raw:
        return DEFAULT_USDA
    path = raw if os.path.isabs(raw) else os.path.join(os.getcwd(), raw)
    if not path.endswith(".usda"):
        path += ".usda"
    return path


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_save(usda_file: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(usda_file)), exist_ok=True)
    print(f"[prim_tool] Saving  {PRIM_PATH}  →  {usda_file}")

    result = _post("/scene/save", {"output_path": usda_file, "prim_path": PRIM_PATH})

    if result.get("status") != "ok":
        sys.exit(f"ERROR: {result.get('error', result)}")

    print(f"[prim_tool] Saved:  {result['path']}")
    print(f"[prim_tool] Prim:   {result['prim']}")
    print(f"[prim_tool] Edit:   code {usda_file}")


def cmd_load(usda_file: str) -> None:
    if not os.path.exists(usda_file):
        sys.exit(
            f"ERROR: File not found:\n  {usda_file}"
        )

    print(f"[prim_tool] Loading  {usda_file}  →  {PRIM_PATH}")

    result = _post("/scene/load", {"file_path": usda_file, "prim_path": PRIM_PATH})

    if result.get("status") != "ok":
        sys.exit(f"ERROR: {result.get('error', result)}")

    print(f"[prim_tool] Loaded:  {result['loaded']}")
    print(f"[prim_tool] Source prim: {result['src_prim']}  →  {result['dst_prim']}")
    print("[prim_tool] Done — rest of the world unchanged.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"Save or hot-reload {PRIM_PATH} in Isaac Sim.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "command",
        choices=["save", "load"],
        help="save: running stage → file.   load: any USDA file → running stage.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        help=f"USDA path (default: {DEFAULT_USDA})",
    )
    args = parser.parse_args()
    usda_file = _resolve_path(args.file)

    if args.command == "save":
        cmd_save(usda_file)
    elif args.command == "load":
        cmd_load(usda_file)


if __name__ == "__main__":
    main()
