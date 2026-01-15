#!/usr/bin/env python3
"""
ONE-TIME SETUP: Configure the rotary lidar in your USD file.

Run this script ONCE in Isaac Sim, then save the USD file.
After that, the lidar will be automatically configured every time you load the robot.
"""

from omni.isaac.core.utils.stage import get_current_stage
from omni.isaac.sensor import RotatingLidarPhysX


def setup_lidar_permanently():
    """
    Configure the Unitree L2 lidar and embed it in the USD file.
    This only needs to be run ONCE.
    """
    
    stage = get_current_stage()
    
    if stage is None:
        print("ERROR: Please load jaska_robot.usd first!")
        return False
    
    print("\n" + "="*60)
    print("ONE-TIME LIDAR SETUP")
    print("="*60)
    
    # Find the unitree_lidar_link in the stage (don't hardcode the path)
    lidar_link_path = None
    for prim in stage.Traverse():
        if prim.GetName() == "unitree_lidar_link":
            lidar_link_path = str(prim.GetPath())
            break
    
    if not lidar_link_path:
        print("ERROR: Could not find unitree_lidar_link in the stage!")
        print("Make sure jaska_robot.usd is loaded.")
        return False
    
    print(f"Found lidar link at: {lidar_link_path}")
    
    # Create sensor as a child of the lidar link
    sensor_path = f"{lidar_link_path}/Rotary_lidar"
    
    # Check if already configured
    sensor_prim = stage.GetPrimAtPath(sensor_path)
    if sensor_prim.IsValid() and sensor_prim.HasAPI("OmniSensorGenericLidarCoreAPI"):
        print(f"\n✓ Sensor already configured at {sensor_path}")
        print("No changes needed!")
        return True
    
    print(f"\nCreating rotary lidar sensor at {sensor_path}...")
    
    # Create the sensor as a child prim
    try:
        rotary_lidar = RotatingLidarPhysX(
            prim_path=sensor_path,
            name="unitree_l2_lidar",
            rotation_frequency=5.55  # From datasheet: Horizontal Scanning Frequency
        )
        
        # Verify and get the sensor prim
        sensor_prim = stage.GetPrimAtPath(sensor_path)
        applied_schemas = sensor_prim.GetAppliedSchemas()
        
        print(f"✓ Sensor created at {sensor_path}!")
        print(f"  Applied schemas: {applied_schemas}")
        
        # Apply Unitree L2 specifications from datasheet
        print("\nApplying Unitree L2 specifications from datasheet...")
        
        # Set attributes directly on the prim
        if sensor_prim.HasAttribute("maxRange"):
            sensor_prim.GetAttribute("maxRange").Set(30.0)  # 30M max range
        if sensor_prim.HasAttribute("minRange"):
            sensor_prim.GetAttribute("minRange").Set(0.05)  # 0.05m near blind zone
        if sensor_prim.HasAttribute("horizontalFov"):
            sensor_prim.GetAttribute("horizontalFov").Set(360.0)  # 360° FOV
        if sensor_prim.HasAttribute("verticalFov"):
            sensor_prim.GetAttribute("verticalFov").Set(90.0)  # 90° vertical FOV
        if sensor_prim.HasAttribute("horizontalResolution"):
            sensor_prim.GetAttribute("horizontalResolution").Set(0.64)  # 0.64° angular resolution
        if sensor_prim.HasAttribute("rotationRate"):
            sensor_prim.GetAttribute("rotationRate").Set(5.55)  # 5.55Hz scanning frequency
        
        # Enable visualization
        if sensor_prim.HasAttribute("drawPoints"):
            sensor_prim.GetAttribute("drawPoints").Set(True)
        if sensor_prim.HasAttribute("drawLines"):
            sensor_prim.GetAttribute("drawLines").Set(True)
        if sensor_prim.HasAttribute("highLod"):
            sensor_prim.GetAttribute("highLod").Set(True)
        if sensor_prim.HasAttribute("enabled"):
            sensor_prim.GetAttribute("enabled").Set(True)
        
        print("✓ Unitree L2 parameters applied:")
        print("  - Max Range: 30.0m")
        print("  - Min Range: 0.05m (Near Blind Zone)")
        print("  - Horizontal FOV: 360°")
        print("  - Vertical FOV: 90°")
        print("  - Angular Resolution: 0.64°")
        print("  - Rotation Rate: 5.55Hz")
        print("  - Visualization: ENABLED (drawPoints & drawLines)")
        
        # Check for lidar-specific schemas
        has_lidar_api = any('Lidar' in s or 'Sensor' in s for s in applied_schemas)
        if not has_lidar_api:
            print("  ⚠ Warning: No lidar sensor schemas found!")
        else:
            print("  ✓ Lidar sensor APIs successfully applied!")
            
    except Exception as e:
        print(f"✗ Error creating sensor: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*60)
    print("CONFIGURATION COMPLETE!")
    print("="*60)
    print("\nNow SAVE the USD file:")
    print("  • Press Ctrl+S")
    print("  • Or File > Save")
    print("\nAfter saving, the lidar will be automatically configured")
    print("every time you load jaska_robot.usd!")
    print("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    setup_lidar_permanently()
