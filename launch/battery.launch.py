from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def float_arg(name):
    """Pass a launch argument to a node as a float parameter."""
    return ParameterValue(LaunchConfiguration(name), value_type=float)


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('discharge_rate', default_value='0.02',
                              description='Discharge speed [fraction of charge / s]'),
        DeclareLaunchArgument('warn_level', default_value='0.3',
                              description='Below this charge level -> WARN'),
        DeclareLaunchArgument('error_level', default_value='0.1',
                              description='Below this charge level -> ERROR'),
        Node(
            package='var_zfe_kisbead',
            executable='battery_sim',
            name='battery_sim',
            output='screen',
            parameters=[{'discharge_rate': float_arg('discharge_rate')}],
        ),
        Node(
            package='var_zfe_kisbead',
            executable='battery_monitor',
            name='battery_monitor',
            output='screen',
            parameters=[{
                'warn_level': float_arg('warn_level'),
                'error_level': float_arg('error_level'),
            }],
        ),
    ])
