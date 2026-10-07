#!/usr/bin/env python3
"""
机械臂关节状态监听器：接收 6 个关节角度（使用类风格）
"""
import rclpy                              # ROS2 Python 客户端库
from rclpy.node import Node               # 节点基类
from sensor_msgs.msg import JointState    # 机械臂关节状态消息类型
import math                               # 数学库，用于弧度转角度


class JointStateSubscriber(Node):
    """关节状态订阅者节点类"""
    
    def __init__(self):
        super().__init__('joint_state_subscriber')  # 调用父类构造函数
        
        # 创建 Subscriber：订阅 /joint_states 话题
        self.subscription = self.create_subscription(
            JointState,                    # 消息类型
            '/joint_states',               # 话题名
            self.callback,                 # 回调函数
            10)                            # 队列长度
        
        self.get_logger().info('关节状态监听器已启动，等待数据...')
    
    def callback(self, msg: JointState):
        """回调函数：每次收到 JointState 消息时执行"""
        # 将弧度转为角度，方便阅读
        angles = [f'{math.degrees(p):.1f}°' for p in msg.position]
        # 格式化输出：joint1: 10.0° | joint2: 20.0° | ...
        output = ' | '.join([f'{n}: {a}' for n, a in zip(msg.name, angles)])
        self.get_logger().info(output)     # 打印到终端


def main():
    rclpy.init()                           # 初始化 ROS2
    node = JointStateSubscriber()          # 创建节点实例
    
    try:
        rclpy.spin(node)                   # 保持节点运行，处理回调
    except (KeyboardInterrupt, ExternalShutdownException):
        pass                               # Ctrl+C 优雅退出
    finally:
        node.destroy_node()                # 销毁节点
        if rclpy.ok():
            rclpy.shutdown()                   # 关闭 ROS2


if __name__ == '__main__':                 # Python 入口点
    main()
