import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    config_file = os.path.join(get_package_share_directory('rover_nav'),'config','rover_params.yaml')
    return LaunchDescription([
        Node(package='rover_power', executable='power_node', name='power_node', parameters=[config_file]),
        Node(package = 'rover_power', executable  = 'health_node', name = 'health_node'),
        Node(package = 'rover_power', executable = 'monitor_node', name = 'monitor_node', output = 'screen')
    ])