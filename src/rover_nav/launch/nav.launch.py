import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    config_file = os.path.join(get_package_share_directory('rover_nav'),'config','rover_params.yaml')
    return LaunchDescription([
    #     GroupAction(actions=[
    #      PushROSNamespace('turtlesim2'),
    #      IncludeLaunchDescription(PathJoinSubstitution([launch_dir, 'turtlesim_world_2_launch.py'])),
    #   ]),
    Node(package = 'rover_nav', executable='drive_node', name='drive_node', parameters = [config_file]),
    Node(package = 'rover_nav', executable='odom_node', name='odom_node', parameters = [config_file]),
    Node(package='rover_power', executable='power_node', name='power_node', parameters=[config_file]),
    Node(package = 'rover_power', executable  = 'health_node', name = 'health_node'),
    Node(package = 'rover_power', executable = 'monitor_node', name = 'monitor_node', output = 'screen'),
    Node(package = 'rover_nav', executable='navigator_node', name='navigator_node')
    ])