#!/usr/bin/env python3
"""
Create a test world with sample objects and spawn the Jaska robot.

Run this in Isaac Sim Script Editor or as a standalone script.
"""

from omni.isaac.core.utils.stage import add_reference_to_stage, get_current_stage
from omni.isaac.core.utils.prims import create_prim
from pxr import UsdGeom, Gf, UsdPhysics
import numpy as np
import os


def create_test_world():
    """Create a world with various objects and the Jaska robot."""
    
    print("Creating test world with sample objects...")
    
    stage = get_current_stage()
    
    # Create physics scene (required for sensors and physics simulation)
    scene = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
    scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
    scene.CreateGravityMagnitudeAttr().Set(9.81)
    
    # Optimization: Use CPU solver (more efficient for robots)
    # Disable GPU dynamics and use MBP broadphase
    from pxr import PhysxSchema
    physx_scene = PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
    physx_scene.CreateEnableGPUDynamicsAttr().Set(False)
    physx_scene.CreateBroadphaseTypeAttr().Set("MBP")  # Multi Box Pruning
    
    print("✓ Physics scene created (CPU solver, MBP broadphase)")
    
    # Create ground plane
    print("Creating ground plane...")
    ground = create_prim(
        "/World/GroundPlane",
        "Xform",
        position=np.array([0, 0, 0])
    )
    
    # Add ground plane mesh
    ground_geom = UsdGeom.Mesh.Define(stage, "/World/GroundPlane/CollisionMesh")
    ground_geom.CreatePointsAttr([(-5, -5, 0), (5, -5, 0), (5, 5, 0), (-5, 5, 0)])
    ground_geom.CreateFaceVertexCountsAttr([4])
    ground_geom.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
    ground_geom.CreateDisplayColorAttr([(0.5, 0.5, 0.5)])
    
    # Add physics
    UsdPhysics.CollisionAPI.Apply(ground_geom.GetPrim())
    
    # Create cubes
    positions_cubes = [
        [-2.2, -2.0, 0.5],
        [-0.8, -2.0, 0.5],
        [0.6, -2.0, 0.5],
        [2.0, -2.0, 0.5],
    ]
    
    for i, pos in enumerate(positions_cubes):
        cube_prim = create_prim(
            f"/World/Cube_{i:02d}",
            "Cube",
            position=np.array(pos),
            scale=np.array([0.5, 0.5, 0.5])
        )
        UsdPhysics.RigidBodyAPI.Apply(cube_prim)
        UsdPhysics.CollisionAPI.Apply(cube_prim)
    
    print("✓ Created 4 cubes")
    
    # Create spheres
    positions_spheres = [
        [-2.0, 2.0, 0.25],
        [-1.0, 2.0, 0.25],
        [0.0, 2.0, 0.25],
        [1.0, 2.0, 0.25],
    ]
    
    for i, pos in enumerate(positions_spheres):
        sphere_prim = create_prim(
            f"/World/Sphere_{i:02d}",
            "Sphere",
            position=np.array(pos),
            scale=np.array([0.25, 0.25, 0.25])
        )
        UsdPhysics.RigidBodyAPI.Apply(sphere_prim)
        UsdPhysics.CollisionAPI.Apply(sphere_prim)
    
    print("✓ Created 4 spheres")
    
    # Create cylinders
    positions_cylinders = [
        [2.5, -1.0, 0.3],
        [3.5, -1.5, 0.3],
    ]
    
    for i, pos in enumerate(positions_cylinders):
        cyl_prim = create_prim(
            f"/World/Cylinder_{i:02d}",
            "Cylinder",
            position=np.array(pos),
            scale=np.array([0.2, 0.2, 0.3])
        )
        UsdPhysics.RigidBodyAPI.Apply(cyl_prim)
        UsdPhysics.CollisionAPI.Apply(cyl_prim)
    
    print("✓ Created 2 cylinders")
    
    # Create cones
    positions_cones = [
        [2.0, 2.0, 0.25],
        [3.0, 2.0, 0.25],
    ]
    
    for i, pos in enumerate(positions_cones):
        cone_prim = create_prim(
            f"/World/Cone_{i:02d}",
            "Cone",
            position=np.array(pos),
            scale=np.array([0.25, 0.25, 0.25])
        )
        UsdPhysics.RigidBodyAPI.Apply(cone_prim)
        UsdPhysics.CollisionAPI.Apply(cone_prim)
    
    print("✓ Created 2 cones")
    
    # Add tall cube
    tall_cube = create_prim(
        "/World/TallCube",
        "Cube",
        position=np.array([-3.0, 0.0, 0.5]),
        scale=np.array([0.25, 0.25, 0.5])
    )
    UsdPhysics.RigidBodyAPI.Apply(tall_cube)
    UsdPhysics.CollisionAPI.Apply(tall_cube)
    
    print("✓ Created tall cube")
    
    # Add disk
    disk = create_prim(
        "/World/Disk",
        "Cylinder",
        position=np.array([3.0, 0.0, 0.05]),
        scale=np.array([0.4, 0.4, 0.05])
    )
    UsdPhysics.RigidBodyAPI.Apply(disk)
    UsdPhysics.CollisionAPI.Apply(disk)
    
    print("✓ Created disk")
    
    # Add Jaska robot
    jaska_usd_path = "/home/haito/haito_dev/ros2_ws/src/jaska_description/usd/jaska_robot.usd"
    
    if not os.path.exists(jaska_usd_path):
        print(f"✗ Error: jaska_robot.usd not found at: {jaska_usd_path}")
        print("  Skipping robot spawn")
    else:
        print(f"Loading Jaska robot from: {jaska_usd_path}")
        
        try:
            jaska_prim_path = add_reference_to_stage(
                usd_path=jaska_usd_path,
                prim_path="/World/Jaska"
            )
            
            # Position robot above ground
            jaska_prim = stage.GetPrimAtPath("/World/Jaska")
            if jaska_prim:
                xform = UsdGeom.Xformable(jaska_prim)
                xform.ClearXformOpOrder()
                xform.AddTranslateOp().Set(Gf.Vec3d(0, 0, 0.4))
            
            print(f"✓ Jaska robot loaded at: {jaska_prim_path}")
        except Exception as e:
            print(f"✗ Error loading robot: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("TEST WORLD CREATED!")
    print("="*60)
    print("Press PLAY to start simulation")
    print("Objects created:")
    print("  - Ground plane")
    print("  - 4 cubes")
    print("  - 4 spheres")
    print("  - 2 cylinders")
    print("  - 2 cones")
    print("  - 1 tall cube")
    print("  - 1 disk")
    print("  - Jaska robot (if found)")
    print("="*60 + "\n")


if __name__ == "__main__":
    create_test_world()
