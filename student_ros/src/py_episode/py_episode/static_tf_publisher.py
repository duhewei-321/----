#!/usr/bin/env python3
"""Publish a configurable static TF transform."""
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from tf2_ros import StaticTransformBroadcaster


class StaticTfPublisher(Node):
    def __init__(self):
        super().__init__('static_tf_publisher')
        self.declare_parameter('parent_frame', 'world')
        self.declare_parameter('child_frame', 'base_link')
        self.declare_parameter('x', 0.0)
        self.declare_parameter('y', 0.0)
        self.declare_parameter('z', 0.0)

        self.broadcaster = StaticTransformBroadcaster(self)
        transform = TransformStamped()
        transform.header.stamp = self.get_clock().now().to_msg()
        transform.header.frame_id = self.get_parameter('parent_frame').value
        transform.child_frame_id = self.get_parameter('child_frame').value
        transform.transform.translation.x = float(self.get_parameter('x').value)
        transform.transform.translation.y = float(self.get_parameter('y').value)
        transform.transform.translation.z = float(self.get_parameter('z').value)
        transform.transform.rotation.w = 1.0
        self.broadcaster.sendTransform(transform)
        self.get_logger().info(
            f'Published static TF: {transform.header.frame_id} -> {transform.child_frame_id}, '
            f'xyz=({transform.transform.translation.x}, {transform.transform.translation.y}, '
            f'{transform.transform.translation.z})'
        )


def main():
    rclpy.init()
    node = StaticTfPublisher()
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
