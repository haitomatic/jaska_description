#!/usr/bin/env python3

"""
Launch file to visualize the Jaska robot in RViz2.
Loads the robot description and starts robot_state_publisher and joint_state_publisher_gui.
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, Command
from launch_ros.actions import Node


def generate_launch_description():
    """Generate launch description for Jaska robot visualization."""
    
    # Get the package directory
    pkg_jaska_description = get_package_share_directory('jaska_description')
    
    # Path to the xacro file
    xacro_file = os.path.join(pkg_jaska_description, 'urdf', 'jaska_robot.xacro')
    
    # Path to RViz config
    rviz_config_file = os.path.join(pkg_jaska_description, 'rviz', 'jaska_robot.rviz')
    
    # Declare arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    use_gui = LaunchConfiguration('use_gui', default='true')
    
    # Robot description
    robot_description = Command(['xacro ', xacro_file])
    
    # Robot state publisher node
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            {
                'robot_description': robot_description,
                'use_sim_time': use_sim_time
            }
        ]
    )
    
    # Joint state publisher GUI node
    joint_state_publisher_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        output='screen',
        parameters=[
            {
                'use_sim_time': use_sim_time
            }
        ]
    )
    
    # RViz2 node
    rviz2_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
        parameters=[
            {
                'use_sim_time': use_sim_time
            }
        ]
    )
    
    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation time'),
        
        DeclareLaunchArgument(
            'use_gui',
            default_value='true',
            description='Start joint_state_publisher_gui'),
        
        robot_state_publisher_node,
        joint_state_publisher_gui_node,
        rviz2_node,
    ])
