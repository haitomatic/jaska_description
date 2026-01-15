"""
Jaska Viewport Setup Extension

Automatically creates dual viewport layout on startup.
"""

import omni.ext
import omni.kit.viewport.utility as vp_util
from omni.isaac.core.utils.stage import get_current_stage
import omni.usd
import omni.ui
import carb
import asyncio


class JaskaViewportSetupExtension(omni.ext.IExt):
    """Extension that sets up dual viewports automatically."""
    
    def on_startup(self, ext_id):
        """Called when extension starts."""
        print("[jaska.viewport.setup] Extension started")
        
        # Wait for stage to be ready, then setup viewports
        self._stage_event_sub = (
            omni.usd.get_context()
            .get_stage_event_stream()
            .create_subscription_to_pop(self._on_stage_event)
        )
        
        self._viewport_window = None
        self._camera_path = None
        self._auto_setup_enabled = True
    
    def on_shutdown(self):
        """Called when extension shuts down."""
        print("[jaska.viewport.setup] Extension shutdown")
        
        if self._stage_event_sub:
            self._stage_event_sub = None
        
        # Clean up viewport if created
        if self._viewport_window:
            self._viewport_window = None
    
    def _on_stage_event(self, event):
        """Handle stage events (load, close, etc)."""
        if event.type == int(omni.usd.StageEventType.OPENED):
            print("[jaska.viewport.setup] Stage opened, setting up viewports...")
            asyncio.ensure_future(self._setup_viewports_async())
    
    async def _setup_viewports_async(self):
        """Async viewport setup to allow stage to fully load."""
        # Wait a moment for stage to stabilize
        await asyncio.sleep(1.0)
        
        if not self._auto_setup_enabled:
            return
        
        try:
            # Create second viewport if not exists
            if self._viewport_window is None:
                print("[jaska.viewport.setup] Creating second viewport...")
                self._viewport_window = vp_util.create_viewport_window(
                    "Viewport 2", 
                    width=640, 
                    height=480,
                    visible=True,
                    docked=True
                )
                
                # Wait for viewport to be created
                await asyncio.sleep(0.5)
                
                # Arrange side by side
                self._arrange_viewports_side_by_side()
                print("[jaska.viewport.setup] ✓ Second viewport created")
            
            # Try to find and set camera
            camera_path = self._find_camera()
            if camera_path:
                print(f"[jaska.viewport.setup] Setting camera: {camera_path}")
                await asyncio.sleep(0.5)  # Let viewport initialize
                
                try:
                    self._viewport_window.viewport_api.set_active_camera(camera_path)
                    self._camera_path = camera_path
                    print("[jaska.viewport.setup] ✓ Camera view configured")
                except Exception as e:
                    print(f"[jaska.viewport.setup] Could not set camera: {e}")
            else:
                print("[jaska.viewport.setup] No camera found yet")
                
        except Exception as e:
            print(f"[jaska.viewport.setup] Error in viewport setup: {e}")
    
    def _arrange_viewports_side_by_side(self):
        """Arrange viewports in horizontal split (side by side)."""
        try:
            # Get both viewport windows
            main_vp = omni.ui.Workspace.get_window("Viewport")
            new_vp = self._viewport_window._window if self._viewport_window else None
            
            if main_vp and new_vp:
                # First undock the new viewport if it's docked elsewhere
                new_vp.undock()
                
                # Dock to the right with split
                new_vp.dock_in(main_vp, omni.ui.DockPosition.RIGHT, ratio=0.5)
                new_vp.dock_tab_bar_visible = False
                main_vp.dock_tab_bar_visible = False
                
                print("[jaska.viewport.setup] ✓ Viewports arranged side-by-side")
            else:
                print("[jaska.viewport.setup] ⚠ Could not find viewport windows for arrangement")
                
        except Exception as e:
            print(f"[jaska.viewport.setup] Error arranging viewports: {e}")
    
    def _find_camera(self):
        """Find first camera in the scene."""
        stage = get_current_stage()
        if stage is None:
            return None
        
        # Check common camera paths first
        common_paths = [
            "/World/Jaska/zed_camera_link/Camera",
            "/World/Jaska/sensor_mount_base/zed_camera_link/Camera",
            "/World/Camera",
            "/Camera",
        ]
        
        for path in common_paths:
            prim = stage.GetPrimAtPath(path)
            if prim.IsValid() and prim.GetTypeName() == "Camera":
                return path
        
        # Search entire stage
        for prim in stage.Traverse():
            if prim.GetTypeName() == "Camera":
                return str(prim.GetPath())
        
        return None
