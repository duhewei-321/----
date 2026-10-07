#!/usr/bin/env python3
"""
极简 Subscriber：接收单个关节角度（使用类风格）
"""
import rclpy                        # ROS2 Python 客户端库
from rclpy.node import Node         # 节点基类
from std_msgs.msg import Float64    # 标准消息类型：64位浮点数


class SimpleSubscriber(Node):
    """简单订阅者节点类"""
    
    def __init__(self):
        super().__init__('simple_subscriber')  # 调用父类构造函数，设置节点名称
        
        # 创建 Subscriber：订阅 /joint1_angle 话题，收到消息后调用 callback
        self.subscription = self.create_subscription(
            Float64,                           # 消息类型
            '/joint1_angle',                   # 话题名
            self.callback,                     # 回调函数
            10)                                # 队列长度
        
        self.get_logger().info('Subscriber 已启动，等待数据...')
    
    def callback(self, msg: Float64):
        """回调函数：每次收到消息时自动执行"""
        self.get_logger().info(f'收到: joint1 = {msg.data:.1f}°')


def main():
    rclpy.init()                     # 初始化 ROS2
    node = SimpleSubscriber()        # 创建节点实例
    
    try:
        rclpy.spin(node)             # 保持节点运行，处理回调
    except (KeyboardInterrupt, ExternalShutdownException):
        pass                         # Ctrl	+C 优雅退出
    finally:
        node.destroy_node()          # 销毁节点
        if rclpy.ok():
            rclpy.shutdown()             # 关闭 ROS2


if __name__ == '__main__':           # Python 入口点
    main()
