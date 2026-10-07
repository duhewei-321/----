#!/usr/bin/env python3
"""
机械臂关节状态发布器：发布 6 个关节角度（使用类风格）
"""
import rclpy                              # ROS2 Python 客户端库
from rclpy.node import Node               # 节点基类
from sensor_msgs.msg import JointState    # 机械臂关节状态消息类型
import math                               # 数学库，用于 sin 函数


class JointStatePublisher(Node):
    """关节状态发布者节点类"""
    
    def __init__(self):
        super().__init__('joint_state_publisher')  # 调用父类构造函数
        
        # 创建 Publisher：话题名 /joint_states，消息类型 JointState
        self.pub = self.create_publisher(JointState, '/joint_states', 10)
        
        # 创建定时器：每 0.1 秒（10Hz）调用一次 timer_callback
        self.timer = self.create_timer(0.1, self.timer_callback)
        
        # 定义 6 个关节名称（与 URDF 模型中的关节名对应）
        self.joint_names = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']
        self.step = 0                      # 步数计数器，用于生成正弦波
        
        self.get_logger().info('关节状态发布器已启动')
    
    def timer_callback(self):
        """定时器回调函数：每次被调用时发布一条消息"""
        # 构建 JointState 消息
        msg = JointState()                              # 创建消息对象
        msg.header.stamp = self.get_clock().now().to_msg()  # 设置时间戳
        msg.name = self.joint_names                     # 设置关节名称列表
        
        # 模拟 6 个关节的运动（正弦波，每个关节频率不同）
        msg.position = [math.sin(self.step * 0.05 * (i + 1)) * 0.5 for i in range(6)]
        msg.velocity = []                  # 速度字段，可选，这里留空
        msg.effort = []                    # 力矩字段，可选，这里留空
        
        self.pub.publish(msg)              # 发布消息
        
        # 日志（每秒打印一次，10Hz 所以每 10 步打印）
        if self.step % 10 == 0:
            angles = [f'{math.degrees(p):.1f}°' for p in msg.position]
            self.get_logger().info(f'发布: {angles}')
        
        self.step += 1                     # 步数 +1


def main():
    rclpy.init()                           # 初始化 ROS2
    node = JointStatePublisher()           # 创建节点实例
    
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
