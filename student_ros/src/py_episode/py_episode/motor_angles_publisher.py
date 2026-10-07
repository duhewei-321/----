#!/usr/bin/env python3
"""
使用自定义消息发布电机角度
对比 joint_state_publisher.py，代码更加简洁且语义更清晰
"""
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from robot_arm_interfaces.msg import MotorAngles  # 导入自定义消息
import math


class MotorAnglesPublisher(Node):
    """电机角度发布者（使用自定义消息）"""
    
    def __init__(self):
        super().__init__('motor_angles_publisher')
        
        # 创建 Publisher：使用自定义消息类型
        self.pub = self.create_publisher(MotorAngles, '/motor_angles', 10)
        
        # 创建定时器：10Hz
        self.timer = self.create_timer(0.1, self.timer_callback)
        
        self.step = 0
        self.get_logger().info('电机角度发布器已启动（使用自定义消息）')
    
    def timer_callback(self):
        """定时器回调：发布电机角度"""
        msg = MotorAngles()
        
        # 设置 6 个电机角度（角度制，正弦波模拟）
        msg.angles = [math.sin(self.step * 0.05 * (i + 1)) * 30.0 for i in range(6)]
        
        # 设置时间戳
        msg.timestamp = self.get_clock().now().to_msg()
        
        # 设置状态标志
        msg.success = True
        msg.message = 'OK'
        
        self.pub.publish(msg)
        
        # 日志（每秒打印一次）
        if self.step % 10 == 0:
            angles_str = [f'{a:.1f}°' for a in msg.angles]
            self.get_logger().info(f'发布: {angles_str}')
        
        self.step += 1


def main():
    rclpy.init()
    node = MotorAnglesPublisher()
    
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
