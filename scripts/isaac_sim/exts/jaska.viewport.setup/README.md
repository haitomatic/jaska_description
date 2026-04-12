# Jaska Viewport Setup Extension

Custom Isaac Sim extension that automatically configures dual viewport layout on startup.

## Features

- Automatically creates second viewport when stage opens
- Searches for camera in scene and configures camera view
- Runs on Isaac Sim startup (no manual script execution needed)

## Installation

### Method 1: Add to Isaac Sim Extension Search Path

1. Open Isaac Sim
2. Go to **Window → Extensions**
3. Click the **gear icon** (⚙️) in top right
4. Under **Extension Search Paths**, click the **+** button
5. Add this path:
   ```
   /home/haito/haito_dev/ros2_ws/src/jaska_description/scripts/isaac_sim/exts
   ```
6. Click **Apply**
7. In Extensions window, search for "Jaska Viewport"
8. Toggle it **ON**

### Method 2: Using isaac.toml Configuration

Add to your `~/.local/share/ov/pkg/isaac-sim-*/user.config.json` or create `isaac.toml`:

```toml
[settings]
exts."jaska.viewport.setup".enabled = true

[[app.extensions.search_paths]]
path = "/home/haito/haito_dev/ros2_ws/src/jaska_description/scripts/isaac_sim/exts"
```

### Method 3: Command Line

Launch Isaac Sim with extension path:

```bash
./isaac-sim.sh --ext-folder /home/haito/haito_dev/ros2_ws/src/jaska_description/scripts/isaac_sim/exts --enable jaska.viewport.setup
```

## How It Works

1. Extension loads on Isaac Sim startup
2. Listens for stage open events
3. When a USD stage is loaded:
   - Creates second viewport
   - Searches for camera prim
   - Configures camera view automatically

## File Structure

```
exts/jaska.viewport.setup/
├── extension.toml           # Extension metadata
├── README.md                # This file
└── jaska/
    └── viewport/
        └── setup/
            ├── __init__.py
            └── extension.py  # Main extension code
```

## Customization

Edit `extension.py` to customize:

- Camera search paths (modify `common_paths` in `_find_camera()`)
- Viewport layout
- Auto-setup behavior

## Disable Auto-Setup

In Extensions window, toggle "Jaska Viewport Setup" OFF.

## Troubleshooting

**Extension doesn't appear:**
- Check extension search path is correct
- Restart Isaac Sim after adding path

**Camera view not set:**
- Extension waits 1 second for stage to load
- Camera must be named "Camera" in USD
- Check console for error messages

**Multiple viewports created:**
- Extension only creates one additional viewport
- Check if other extensions are also creating viewports
