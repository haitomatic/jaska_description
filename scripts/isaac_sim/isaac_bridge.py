"""
Isaac Bridge — TCP socket server for external script execution.

Run via --exec or once in Isaac Sim's Script Editor.
Schedules all scripts on Kit's main thread (required for USD/stage operations).

Listens on 127.0.0.1:9011
Protocol: send JSON {"script": "..."}, receive {"status":"ok","output":"..."}

⚠️  SECURITY WARNING ⚠️
This bridge executes arbitrary Python code via exec() with no authentication,
authorization, or sandboxing. Any local process on this machine can connect
and run arbitrary code with full Isaac Sim privileges.
This is intentionally a TEMPORARY DEVELOPER TOOL only. Do NOT run on shared
machines, in production, or in any security-sensitive environment.
"""
import socket, json, threading, io, contextlib, traceback, asyncio

BRIDGE_PORT = 9011


async def _async_execute(script: str) -> dict:
    """Runs on Kit's main thread — safe for all USD/omni operations."""
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(script, "<isaac_bridge>", "exec"), {"__builtins__": __builtins__})
        return {"status": "ok", "output": buf.getvalue()}
    except BaseException:
        return {"status": "error", "output": buf.getvalue(), "error": traceback.format_exc()}


def _handle_conn(conn, main_loop):
    try:
        data = b""
        while True:
            chunk = conn.recv(8192)
            if not chunk:
                break
            data += chunk
            try:
                payload = json.loads(data.decode())
                break
            except json.JSONDecodeError:
                continue

        # Schedule on main Kit thread and block until done
        future = asyncio.run_coroutine_threadsafe(
            _async_execute(payload.get("script", "")), main_loop
        )
        result = future.result(timeout=120)
        conn.sendall(json.dumps(result).encode())
    except Exception as e:
        try:
            conn.sendall(json.dumps({"status": "error", "error": str(e)}).encode())
        except Exception:
            pass
    finally:
        conn.close()


def _serve(port: int, main_loop):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        srv.bind(("127.0.0.1", port))
    except OSError as e:
        print(f"[isaac_bridge] Cannot bind to port {port}: {e}")
        return
    srv.listen(5)
    print(f"[isaac_bridge] Listening on 127.0.0.1:{port} — ready for action_graph_tool.sh")
    while True:
        try:
            conn, _ = srv.accept()
            threading.Thread(
                target=_handle_conn, args=(conn, main_loop), daemon=True
            ).start()
        except Exception:
            break


# Capture Kit's main event loop HERE (we are on the main thread at --exec time)
_main_loop = asyncio.get_event_loop()

_t = threading.Thread(target=_serve, args=(BRIDGE_PORT, _main_loop), daemon=True, name="isaac_bridge")
_t.start()
