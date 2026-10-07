#!/usr/bin/env python3
"""Gripper service clients: on/off and servo angle."""
import sys
from pathlib import Path as FilePath

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from robot_arm_interfaces.srv import GripperControl, ServoGripper


class GripperClient(Node):
    def __init__(self):
        super().__init__('gripper_client')
        self.declare_parameter('service_name', 'gripper_control')
        self.service_name = self.get_parameter('service_name').get_parameter_value().string_value
        self.cli = self.create_client(GripperControl, self.service_name)
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info(f'等待服务 {self.service_name} ...')

    def send(self, enable):
        request = GripperControl.Request()
        request.enable = enable
        future = self.cli.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        self.get_logger().info(f'enable={enable}, success={response.success}, message="{response.message}"')


class GripperCtrlClient(Node):
    def __init__(self):
        super().__init__('gripper_ctrl_client')
        self.declare_parameter('service_name', 'servo_gripper')
        self.service_name = self.get_parameter('service_name').get_parameter_value().string_value
        self.cli = self.create_client(ServoGripper, self.service_name)
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info(f'等待服务 {self.service_name} ...')

    def send_angle(self, angle):
        requested = int(angle)
        clamped = max(0, min(110, requested))
        request = ServoGripper.Request()
        request.angle = clamped
        future = self.cli.call_async(request)
        rclpy.spin_until_future_complete(self, future)
        response = future.result()
        self.get_logger().info(
            f'requested={requested}, sent={clamped}, success={response.success}, '
            f'actual_angle={response.actual_angle}, message="{response.message}"'
        )


def main():
    command = FilePath(sys.argv[0]).name
    if command == 'gripper_ctrl':
        if len(sys.argv) < 2:
            print('用法: ros2 run py_episode gripper_ctrl <0-110>')
            return 0
        angle = int(sys.argv[1])
        rclpy.init()
        node = GripperCtrlClient()
        try:
            node.send_angle(angle)
        except (KeyboardInterrupt, ExternalShutdownException):
            pass
        finally:
            node.destroy_node()
            if rclpy.ok():
                rclpy.shutdown()
        return 0

    rclpy.init()
    node = GripperClient()
    try:
        node.send(True)
        node.send(False)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
