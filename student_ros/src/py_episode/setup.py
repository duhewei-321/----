from setuptools import find_packages, setup

package_name = 'py_episode'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/resource', ['resource/' + package_name]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='du',
    maintainer_email='du@todo.todo',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'simple_pub = py_episode.simple_publisher:main',
            'simple_sub = py_episode.simple_subscriber:main',
            'simple_service = py_episode.simple_service:main',
            'simple_client = py_episode.simple_client:main',
            'simple_srv = py_episode.simple_service:main',
            'simple_cli = py_episode.simple_client:main',
            'joint_pub = py_episode.joint_state_publisher:main',      # 新增
            'joint_sub = py_episode.joint_state_subscriber:main',
            'motor_pub = py_episode.motor_angles_publisher:main',
            'motor_sub = py_episode.motor_angles_subscriber:main',
            'angle_srv = py_episode.angle_mode_server:main',
            'angles_ctrl = py_episode.angles_control_client:main',
            'angle_cli = py_episode.angle_mode_client:main',
            'move_xyz_srv = py_episode.angle_mode_server:main',
            'move_xyz_cli = py_episode.angle_mode_client:main',
            'linear_move_srv = py_episode.angle_mode_server:main',
            'linear_move_cli = py_episode.angle_mode_client:main',
            'robot_interface_action = episode_controller.robot_interface_node:main',
            'robot_interface = py_episode.robot_interface_node:main',
            'robot_interface_srv = py_episode.robot_interface_with_action:main',
            'arm_monitor = py_episode.arm_monitor_node:main',
            'arm_monitor_node = py_episode.arm_monitor_node:main',
            'static_tf_pub = py_episode.static_tf_publisher:main',
            'robot_interface_service = py_episode.robot_interface_with_action:main',
            'gripper_srv = py_episode.gripper_service:main',
            'gripper_cli = py_episode.gripper_client:main',
            'gripper_service = py_episode.gripper_service:main',
            'gripper_client = py_episode.gripper_client:main',
            'gripper_ctrl = py_episode.gripper_client:main',

        ],
    },
)

