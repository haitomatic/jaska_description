# Isaac Sim Custom Extensions

Custom extensions for Isaac Sim development with Jaska robot.

## Available Extensions

### jaska.viewport.setup
Automatically configures dual viewport layout (Perspective + Camera view) on startup.

See [jaska.viewport.setup/README.md](jaska.viewport.setup/README.md) for installation and usage.

## Creating New Extensions

Basic extension structure:
```
exts/
└── your.extension.name/
    ├── extension.toml        # Metadata and dependencies
    ├── README.md             # Documentation
    └── your/
        └── extension/
            └── name/
                ├── __init__.py
                └── extension.py  # Main extension code
```

## Adding Extension Search Path to Isaac Sim

1. **Window → Extensions**
2. Click **gear icon** (⚙️)
3. Under **Extension Search Paths**, click **+**
4. Add: `/home/haito/haito_dev/ros2_ws/src/jaska_description/scripts/isaac_sim/exts`
5. Click **Apply**

## Resources

- [Isaac Sim Extension Documentation](https://docs.omniverse.nvidia.com/extensions/latest/index.html)
- [Omniverse Extension Development](https://docs.omniverse.nvidia.com/py/kit/docs/guide/extensions.html)
