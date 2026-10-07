#!/usr/bin/env python3
"""Generic simulated ROS2 action client for robot arm examples."""
import sys
from pathlib import Path

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from robot_arm_interfaces.action import AngleMode, MoveXyzRotation, LinearMove


def select_action():
    script = Path(sys.argv[0]).name
    if 'move_xyz' in script:
        return MoveXyzRotation, 'move_xyz_rotation'
    if 'linear_move' in script:
        return LinearMove, 'linear_move'
    return AngleMode, 'angle_mode'


class GenericActionClient(Node):
    def __init__(self, action_type, action_name):
        super().__init__(f'{action_name}_client')
        self.action_type = action_type
        self.declare_parameter('action_name', action_name)
        self.action_name = self.get_parameter('action_name').get_parameter_value().string_value or action_name
        self._client = ActionClient(self, action_type, self.action_name)

    def feedback_callback(self, feedback_msg):
        fb = feedback_msg.feedback
        values = []
        for name in ('progress', 'elapsed_time', 'current_step', 'total_steps'):
            if hasattr(fb, name):
                values.append(f'{name}={getattr(fb, name)}')
        if hasattr(fb, 'current_angles'):
            values.append(f'angles={[round(v, 1) for v in fb.current_angles]}')
        self.get_logger().info('反馈: ' + ', '.join(values))

    def send_goal(self):
        self.get_logger().info(f'等待 {self.action_name} action server...')
        self._client.wait_for_server()

        goal = self.action_type.Goal()
        if self.action_type is AngleMode:
            goal.angles = [0.0, 15.0, 30.0, 45.0, 60.0, 90.0]
            goal.speed_ratio = 1.0
        elif self.action_type is MoveXyzRotation:
            goal.position = [200.0, 0.0, 150.0]
            goal.rotation = [0.0, 0.0, 0.0]
            goal.ik_mode = 'xyz'
            goal.speed_ratio = 1.0
        else:
            goal.position = [200.0, 0.0, 150.0]
            goal.rotation = [0.0, 0.0, 0.0]
            goal.rotation_mode = 'zyx'
            goal.step_size = 8.0

        self.get_logger().info(f'发送 {self.action_name} 目标')
        send_future = self._client.send_goal_async(goal, feedback_callback=self.feedback_callback)
        rclpy.spin_until_future_complete(self, send_future)
        goal_handle = send_future.result()
        if goal_handle is None or not goal_handle.accepted:
            self.get_logger().error('目标被拒绝')
            return

        self.get_logger().info('目标已接受，等待结果...')
        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        result = result_future.result().result
        self.get_logger().info(
            f'结果: success={result.success}, message="{result.message}", '
            f'execution_time={result.execution_time}'
        )


def main():
    action_type, action_name = select_action()
    rclpy.init()
    node = GenericActionClient(action_type, action_name)
    try:
        node.send_goal()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
