#!/usr/bin/env python3
"""Simple AddTwoInts service server for chapter 6."""
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from example_interfaces.srv import AddTwoInts


class SimpleService(Node):
    def __init__(self):
        super().__init__('simple_service')
        self.srv = self.create_service(AddTwoInts, 'add_two_ints', self.add_two_ints_callback)
        self.get_logger().info('Service Server 已启动，等待请求...')

    def add_two_ints_callback(self, request, response):
        response.sum = request.a + request.b
        self.get_logger().info(f'收到请求: {request.a} + {request.b} = {response.sum}')
        return response


def main():
    rclpy.init()
    node = SimpleService()
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
