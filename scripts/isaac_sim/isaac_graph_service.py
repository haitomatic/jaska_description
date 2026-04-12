"""
Isaac Graph Service — REST API server for external tool access to Isaac Sim.

Exposes a typed REST API (FastAPI / omni.services.core). No exec(), no arbitrary
code injection. Swagger UI at http://localhost:8011/docs

Start alongside Isaac Sim (add to launch command):
  ~/isaacsim/isaac-sim.sh \
      --enable omni.services.core \
      --enable omni.services.transport.server.http \
      --exec /path/to/isaac_graph_service.py

Swagger UI available at: http://localhost:8011/docs

Endpoints
---------
GET  /sim/status          Simulation timeline state (PLAYING / PAUSED / STOPPED)
POST /graph/save          Export an OmniGraph prim from the running stage to a USDA file
POST /graph/apply         Hot-reload a USDA file back into the running stage
"""

from omni.services.core import main


# ---------------------------------------------------------------------------
# GET /sim/status
# ---------------------------------------------------------------------------

def sim_status() -> dict:
    """Return current simulation timeline state and time."""
    import omni.timeline

    tl = omni.timeline.get_timeline_interface()
    if tl.is_playing():
        state = "PLAYING"
    elif tl.is_stopped():
        state = "STOPPED"
    else:
        state = "PAUSED"
    return {"state": state, "time": tl.get_current_time()}


# ---------------------------------------------------------------------------
# POST /graph/save
# ---------------------------------------------------------------------------

def graph_save(graph_path: str = "/Environment/ActionGraph", output_path: str = "") -> dict:
    """
    Export the OmniGraph prim at *graph_path* in the current stage to *output_path* (USDA).

    Parameters
    ----------
    graph_path:
        USD prim path of the OmniGraph to export, e.g. ``/Environment/ActionGraph``.
        If empty, all OmniGraph/ComputeGraph prims in the stage are exported.
    output_path:
        Absolute path on the host where the USDA file should be written.
    """
    import os

    import omni.usd
    from pxr import Sdf, Usd

    if not output_path:
        return {"status": "error", "error": "output_path is required"}

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    stage = omni.usd.get_context().get_stage()
    if stage is None:
        return {"status": "error", "error": "No stage is currently open in Isaac Sim"}

    if graph_path:
        prim = stage.GetPrimAtPath(graph_path)
        if not prim.IsValid():
            return {
                "status": "error",
                "error": f"No prim at '{graph_path}'. Check Stage panel for the correct path.",
            }
        graph_paths = [prim.GetPath()]
    else:
        graph_paths = [
            p.GetPath()
            for p in stage.Traverse()
            if p.GetTypeName() in ("OmniGraph", "ComputeGraph")
        ]

    if not graph_paths:
        return {"status": "error", "error": "No OmniGraph/ComputeGraph prims found in stage"}

    if os.path.exists(output_path):
        os.remove(output_path)

    new_stage = Usd.Stage.CreateNew(output_path)
    root_layer = new_stage.GetRootLayer()

    copied = []
    for gpath in graph_paths:
        for layer in stage.GetLayerStack():
            if layer.GetPrimAtPath(gpath):
                parent = gpath.GetParentPath()
                if str(parent) not in ("/", ""):
                    new_stage.OverridePrim(parent)
                Sdf.CopySpec(layer, Sdf.Path(gpath), root_layer, Sdf.Path(gpath))
                copied.append(str(gpath))
                break

    new_stage.Save()
    return {"status": "ok", "path": output_path, "graphs": copied}


# ---------------------------------------------------------------------------
# POST /graph/apply
# ---------------------------------------------------------------------------

def graph_apply(file_path: str = "") -> dict:
    """
    Hot-reload OmniGraph prims from a USDA file into the running stage.

    The prims are matched by name — the parent prim (e.g. ``/Environment``) is
    **not** overwritten, only the OmniGraph child spec is replaced.

    Parameters
    ----------
    file_path:
        Absolute path to the USDA file to load (produced by ``/graph/save``).
    """
    import omni.usd
    from pxr import Sdf

    if not file_path:
        return {"status": "error", "error": "file_path is required"}

    stage = omni.usd.get_context().get_stage()
    if stage is None:
        return {"status": "error", "error": "No stage is currently open in Isaac Sim"}

    src_layer = Sdf.Layer.FindOrOpen(file_path)
    if not src_layer:
        return {"status": "error", "error": f"Cannot open file: {file_path}"}

    edit_layer = stage.GetEditTarget().GetLayer()

    existing = {
        p.GetName(): p.GetPath()
        for p in stage.Traverse()
        if p.GetTypeName() in ("OmniGraph", "ComputeGraph")
    }

    applied = []
    for root_spec in src_layer.rootPrims:
        for child_spec in root_spec.nameChildren.values():
            if child_spec.typeName not in ("OmniGraph", "ComputeGraph"):
                continue
            src_path = Sdf.Path(f"/{root_spec.name}/{child_spec.name}")
            dst_path = existing.get(child_spec.name, src_path)
            parent_path = Sdf.Path(f"/{root_spec.name}")
            if not edit_layer.GetPrimAtPath(parent_path):
                Sdf.CreatePrimInLayer(edit_layer, parent_path)
            Sdf.CopySpec(src_layer, src_path, edit_layer, Sdf.Path(dst_path))
            applied.append(str(dst_path))

    if not applied:
        return {"status": "error", "error": "No OmniGraph prims found in source file"}

    return {"status": "ok", "applied": applied}


# ---------------------------------------------------------------------------
# GET /graph/qos
# ---------------------------------------------------------------------------

def graph_qos() -> dict:
    """
    Return QoS profiles and topic→profile mapping from the *live* running stage.

    Traverses all OmniGraphNode prims in the current USD stage and collects:
    - ``profiles``: dict of QoS profile node name → {depth, durability, history, reliability}
    - ``topics``: dict of topic name → QoS profile node name
    """
    import omni.usd

    stage = omni.usd.get_context().get_stage()
    if stage is None:
        return {"status": "error", "error": "No stage is currently open in Isaac Sim"}

    profiles: dict = {}
    topic_profile: dict = {}

    for prim in stage.Traverse():
        if prim.GetTypeName() != "OmniGraphNode":
            continue

        prim_name = prim.GetName()

        # ── QoS profile definition nodes ──────────────────────────────────
        if prim_name.startswith("ros2_qos_profile"):
            def _get_attr(name: str) -> str:
                a = prim.GetAttribute(name)
                v = a.Get() if a.IsValid() else None
                return str(v) if v is not None else "?"

            profiles[prim_name] = {
                "depth":       _get_attr("inputs:depth"),
                "durability":  _get_attr("inputs:durability"),
                "history":     _get_attr("inputs:history"),
                "reliability": _get_attr("inputs:reliability"),
            }

        # ── Publisher / subscriber nodes ──────────────────────────────────
        topic_attr = prim.GetAttribute("inputs:topicName")
        if not topic_attr.IsValid():
            continue
        topic_name = topic_attr.Get()
        if not topic_name:
            continue

        qos_attr = prim.GetAttribute("inputs:qosProfile")
        if qos_attr.IsValid():
            connections = qos_attr.GetConnections()
            if connections:
                # Connection path: /World/ActionGraph/ros2_qos_profile_xxx.outputs:qosProfile
                qos_prim_name = str(connections[0]).rsplit("/", 1)[-1].split(".")[0]
                topic_profile[str(topic_name)] = qos_prim_name

    return {"status": "ok", "profiles": profiles, "topics": topic_profile}


# ---------------------------------------------------------------------------
# POST /scene/save
# ---------------------------------------------------------------------------

def _find_robot_layer(stage, prim_path: str):
    """
    Return the non-anonymous Sdf.Layer that is the authoritative source for
    *prim_path* — i.e. the robot USDA file (e.g. ``jaska_v2.usda``), not the
    world file or the anonymous session layer.

    Strategy: walk ``prim.GetPrimStack()`` which traverses all composition arcs
    (sublayers, references, payloads) in strength order.  We want the DEEPEST
    non-anonymous layer that has a ``def`` spec for the prim — that is the payload
    source file, not the session layer or the world file's ``def-with-payload``.
    Falls back to the first non-anonymous layer if no pure ``def`` is found.
    """
    import os
    from pxr import Sdf

    prim = stage.GetPrimAtPath(Sdf.Path(prim_path))
    if not prim.IsValid():
        return None, f"No prim at '{prim_path}'"

    leaf = Sdf.Path(prim_path).name  # "jaska_v2"

    # Collect all non-anonymous specs in composition order (strongest first)
    non_anon = [
        spec for spec in prim.GetPrimStack()
        if not spec.layer.anonymous
    ]
    if not non_anon:
        return None, f"No authored (non-anonymous) layer found for '{prim_path}'"

    # Prefer: layer whose basename matches the prim leaf name (most specific)
    for spec in non_anon:
        basename = os.path.splitext(os.path.basename(spec.layer.realPath))[0]
        if basename == leaf:
            return spec.layer, None

    # Fallback: deepest (weakest) non-anonymous def spec — the payload source
    defs = [s for s in non_anon if s.specifier == Sdf.SpecifierDef]
    if defs:
        return defs[-1].layer, None

    # Last resort: first non-anonymous layer
    return non_anon[0].layer, None


# ---------------------------------------------------------------------------
# POST /scene/save
# ---------------------------------------------------------------------------

def scene_save(output_path: str = "", prim_path: str = "/World/jaska_v2") -> dict:
    """
    Save the source USDA layer that defines the prim at *prim_path* to *output_path*.

    Uses ``prim.GetPrimStack()`` to traverse all composition arcs (sublayers,
    references, payloads) and locate the deepest non-anonymous layer — i.e. the
    robot USDA file, not the world file or the session-layer delta.  The layer is
    exported verbatim via ``shutil.copy2``.

    Parameters
    ----------
    output_path:
        Absolute path to write the USDA file.
    prim_path:
        USD prim path whose source layer to locate (default: ``/World/jaska_v2``).
    """
    import os
    import shutil

    import omni.usd

    if not output_path:
        return {"status": "error", "error": "output_path is required"}

    stage = omni.usd.get_context().get_stage()
    if stage is None:
        return {"status": "error", "error": "No stage is currently open in Isaac Sim"}

    source_layer, err = _find_robot_layer(stage, prim_path)
    if err:
        return {"status": "error", "error": err}

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    shutil.copy2(source_layer.realPath, output_path)
    return {
        "status": "ok",
        "path": output_path,
        "prim": prim_path,
        "source_layer": source_layer.realPath,
    }

# ---------------------------------------------------------------------------
# POST /scene/load
# ---------------------------------------------------------------------------

def scene_load(file_path: str = "", prim_path: str = "/World/jaska_v2") -> dict:
    """
    Load any robot USDA file into the running stage at *prim_path*.

    Prepends *file_path* as a payload on *prim_path* in the session edit layer.
    USD composition gives it the strongest opinion, so the wip file's content
    overrides the existing base payload — no CopySpec, no stage crash.

    The file does NOT need to be already loaded in the stage.  The original
    base USDA (e.g. ``jaska_v2_ori.usda``) is never modified on disk.

    To clear the override and return to the base: call ``/scene/unload``.

    Parameters
    ----------
    file_path:
        Absolute path to any robot USDA (e.g. ``jaska_v2.usda``).
    prim_path:
        USD prim path in the running stage to override (default: ``/World/jaska_v2``).
    """
    import os

    import omni.usd
    from pxr import Sdf

    if not file_path:
        return {"status": "error", "error": "file_path is required"}
    if not os.path.exists(file_path):
        return {"status": "error", "error": f"File not found: {file_path}"}

    stage = omni.usd.get_context().get_stage()
    if stage is None:
        return {"status": "error", "error": "No stage is currently open in Isaac Sim"}

    abs_path = os.path.abspath(file_path)
    dst = Sdf.Path(prim_path)
    edit_layer = stage.GetEditTarget().GetLayer()

    with Sdf.ChangeBlock():
        # Ensure parent stub exists in the edit layer
        parent = dst.GetParentPath()
        if str(parent) not in ("/", "") and not edit_layer.GetPrimAtPath(parent):
            Sdf.CreatePrimInLayer(edit_layer, parent)

        # Get or create the prim spec in the edit layer
        spec = edit_layer.GetPrimAtPath(dst)
        if not spec:
            spec = Sdf.CreatePrimInLayer(edit_layer, dst)

        # Prepend the new USDA as the strongest payload — overrides the base
        spec.payloadList.prependedItems = [Sdf.Payload(abs_path)]

    return {
        "status": "ok",
        "loaded": abs_path,
        "dst_prim": prim_path,
    }


# ---------------------------------------------------------------------------
# Register endpoints
# ---------------------------------------------------------------------------

main.register_endpoint("get",  "/sim/status",  sim_status)
main.register_endpoint("get",  "/graph/qos",   graph_qos)
main.register_endpoint("post", "/graph/save",   graph_save)
main.register_endpoint("post", "/graph/apply",  graph_apply)
main.register_endpoint("post", "/scene/save",   scene_save)
main.register_endpoint("post", "/scene/load",   scene_load)
