#!/usr/bin/env python3
"""Demo GripperControl service server."""
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from robot_arm_interfaces.srv import GripperControl


class GripperService(Node):
    def __init__(self):
        super().__init__('gripper_service')
        self.declare_parameter('service_name', 'gripper_control')
        service_name = self.get_parameter('service_name').get_parameter_value().string_value
        self.srv = self.create_service(GripperControl, service_name, self.callback)
        self.get_logger().info(f'Gripper service ready: {service_name}')

    def callback(self, request, response):
        response.success = True
        response.message = 'Gripper ON' if request.enable else 'Gripper OFF'
        self.get_logger().info(response.message)
        return response


def main():
    rclpy.init()
    node = GripperService()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
