#!/usr/bin/env python3
"""Generic simulated ROS2 action server for robot arm examples."""
import sys
import time
from pathlib import Path

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.node import Node

from robot_arm_interfaces.action import AngleMode, MoveXyzRotation, LinearMove


def select_action():
    script = Path(sys.argv[0]).name
    if 'move_xyz' in script:
        return MoveXyzRotation, 'move_xyz_rotation'
    if 'linear_move' in script:
        return LinearMove, 'linear_move'
    return AngleMode, 'angle_mode'


class GenericActionServer(Node):
    def __init__(self, action_type, action_name):
        super().__init__(f'{action_name}_server')
        self.action_type = action_type
        self.declare_parameter('action_name', action_name)
        self.action_name = self.get_parameter('action_name').get_parameter_value().string_value or action_name
        self._server = ActionServer(
            self,
            action_type,
            self.action_name,
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
        )
        self.get_logger().info(f'{action_name} action server started')

    def goal_callback(self, goal_request):
        self.get_logger().info(f'收到 {self.action_name} 目标')
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.get_logger().info(f'收到 {self.action_name} 取消请求')
        return CancelResponse.ACCEPT

    def execute_callback(self, goal_handle):
        if self.action_type is AngleMode:
            return self.execute_angle(goal_handle)
        if self.action_type is MoveXyzRotation:
            return self.execute_move_xyz(goal_handle)
        return self.execute_linear_move(goal_handle)

    def execute_angle(self, goal_handle):
        target = [float(v) for v in goal_handle.request.angles]
        speed_ratio = max(0.05, min(1.0, float(goal_handle.request.speed_ratio)))
        steps = 10
        duration = 2.0 / speed_ratio
        start = time.perf_counter()
        result = AngleMode.Result()
        for i in range(steps + 1):
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                result.success = False
                result.message = 'AngleMode canceled'
                result.execution_time = time.perf_counter() - start
                result.final_angles = [0.0] * 6
                return result
            progress = i / steps
            feedback = AngleMode.Feedback()
            feedback.elapsed_time = time.perf_counter() - start
            feedback.progress = progress
            feedback.current_angles = [a * progress for a in target]
            feedback.status_message = f'Angle progress {int(progress * 100)}%'
            goal_handle.publish_feedback(feedback)
            if i < steps:
                time.sleep(duration / steps)
        result.success = True
        result.message = 'AngleMode completed (simulated)'
        result.execution_time = time.perf_counter() - start
        result.final_angles = target
        goal_handle.succeed()
        return result

    def execute_move_xyz(self, goal_handle):
        position = [float(v) for v in goal_handle.request.position]
        rotation = [float(v) for v in goal_handle.request.rotation]
        speed_ratio = max(0.05, min(1.0, float(goal_handle.request.speed_ratio)))
        solution = [0.0, 15.0, 30.0, 45.0, 60.0, 90.0]
        steps = 10
        duration = 2.0 / speed_ratio
        start = time.perf_counter()
        result = MoveXyzRotation.Result()
        for i in range(steps + 1):
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                result.success = False
                result.message = 'MoveXyzRotation canceled'
                result.execution_time = time.perf_counter() - start
                result.solution_angles = [0.0] * 6
                result.final_position = [0.0, 0.0, 0.0]
                result.final_rotation = [0.0, 0.0, 0.0]
                return result
            progress = i / steps
            feedback = MoveXyzRotation.Feedback()
            feedback.elapsed_time = time.perf_counter() - start
            feedback.progress = progress
            feedback.current_angles = [a * progress for a in solution]
            feedback.status_message = f'Move XYZ progress {int(progress * 100)}%'
            goal_handle.publish_feedback(feedback)
            if i < steps:
                time.sleep(duration / steps)
        result.success = True
        result.message = 'MoveXyzRotation completed (simulated)'
        result.execution_time = time.perf_counter() - start
        result.solution_angles = solution
        result.final_position = position
        result.final_rotation = rotation
        goal_handle.succeed()
        return result

    def execute_linear_move(self, goal_handle):
        position = [float(v) for v in goal_handle.request.position]
        total_steps = 10
        start = time.perf_counter()
        result = LinearMove.Result()
        for i in range(total_steps + 1):
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                result.success = False
                result.message = 'LinearMove canceled'
                result.execution_time = time.perf_counter() - start
                result.total_steps = i
                return result
            progress = i / total_steps
            feedback = LinearMove.Feedback()
            feedback.elapsed_time = time.perf_counter() - start
            feedback.progress = progress
            feedback.current_step = i
            feedback.total_steps = total_steps
            feedback.current_angles = [v * progress for v in [0.0, 15.0, 30.0, 45.0, 60.0, 90.0]]
            feedback.status_message = f'Linear move step {i}/{total_steps}'
            goal_handle.publish_feedback(feedback)
            if i < total_steps:
                time.sleep(0.15)
        result.success = True
        result.message = 'LinearMove completed (simulated)'
        result.execution_time = time.perf_counter() - start
        result.total_steps = total_steps
        goal_handle.succeed()
        return result


def main():
    action_type, action_name = select_action()
    rclpy.init()
    node = GenericActionServer(action_type, action_name)
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            if rclpy.ok():
                rclpy.shutdown()


if __name__ == '__main__':
    main()
