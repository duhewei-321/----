
#!/usr/bin/env python3
"""
机械臂监控节点 - 订阅电机角度
实时显示机械臂各关节的角度状态
"""
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from robot_arm_interfaces.msg import MotorAngles


class ArmMonitorNode(Node):
    """机械臂监控节点：订阅并显示关节角度"""
    
    def __init__(self):
        super().__init__('arm_monitor_node')
        
        # ========== 创建 Subscriber ==========
        self.subscription = self.create_subscription(
            MotorAngles,           # 消息类型
            'motor_angles',        # 话题名称
            self.angles_callback,  # 回调函数
            10                     # 队列大小
        )
        
        # 统计信息
        self.msg_count = 0
        self.error_count = 0
        
        self.get_logger().info('机械臂监控节点已启动，等待数据...')
    
    def angles_callback(self, msg: MotorAngles):
        """回调函数：处理接收到的电机角度消息"""
        self.msg_count += 1
        
        if not msg.success:
            self.error_count += 1
            self.get_logger().warn(f'接收到错误消息: {msg.message}')
            return
        
        # 格式化角度显示
        angles_str = ' | '.join([
            f'J{i+1}: {angle:6.2f}°' 
            for i, angle in enumerate(msg.angles)
        ])
        
        # 每 30 条消息打印一次
        if self.msg_count % 30 == 0:
            self.get_logger().info(f'{angles_str}')
            self.get_logger().info(f'[已接收: {self.msg_count} 条, 错误: {self.error_count} 条]')


def main():
    rclpy.init()
    node = ArmMonitorNode()
    
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        node.get_logger().info(f'统计: 总接收 {node.msg_count} 条, 错误 {node.error_count} 条')
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
