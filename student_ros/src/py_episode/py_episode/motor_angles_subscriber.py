#!/usr/bin/env python3
"""
使用自定义消息接收电机角度
"""
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from robot_arm_interfaces.msg import MotorAngles  # 导入自定义消息


class MotorAnglesSubscriber(Node):
    """电机角度订阅者（使用自定义消息）"""
    
    def __init__(self):
        super().__init__('motor_angles_subscriber')
        
        # 创建 Subscriber：使用自定义消息类型
        self.subscription = self.create_subscription(
            MotorAngles,
            '/motor_angles',
            self.callback,
            10)
        
        self.get_logger().info('电机角度监听器已启动（使用自定义消息）')
    
    def callback(self, msg: MotorAngles):
        """回调函数：处理接收到的角度"""
        # 检查读取状态
        if not msg.success:
            self.get_logger().warn(f'读取失败: {msg.message}')
            return
        
        # 直接访问 msg.angles（已经是角度制）
        angles_str = [f'M{i+1}: {a:.1f}°' for i, a in enumerate(msg.angles)]
        self.get_logger().info(' | '.join(angles_str))


def main():
    rclpy.init()
    node = MotorAnglesSubscriber()
    
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
