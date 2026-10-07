#!/usr/bin/env python3
"""
极简 Publisher：发布单个关节角度（使用 Timer 回调模式）
"""
import rclpy                        # ROS2 Python 客户端库
from rclpy.node import Node         # 节点基类
from std_msgs.msg import Float64    # 标准消息类型：64位浮点数


class SimplePublisher(Node):        # 继承 Node 类，获得其所有方法
    """简单发布者节点类"""
    
    def __init__(self):
        # super() 调用父类 Node 的构造函数，完成节点初始化
        # 这样我们才能使用 self.create_publisher()、self.get_logger() 等父类方法
        super().__init__('simple_publisher')  # 参数是节点名称，ros2 node list 会显示这个名字
        
        # 创建 Publisher：话题名 /joint1_angle，消息类型 Float64，队列长度 10
        # 队列长度 10 表示：如果 Subscriber 处理消息太慢，最多缓存 10 条消息
        # 超过 10 条后，最旧的消息会被丢弃（防止内存无限增长）
        self.pub = self.create_publisher(Float64, '/joint1_angle', 10)
        
        # 创建定时器：每 0.5 秒（2Hz）调用一次 timer_callback
        self.timer = self.create_timer(0.5, self.timer_callback)
        
        self.angle = 0.0            # 初始角度
        self.get_logger().info('Publisher 已启动，开始发布 joint1 角度...')
    
    def timer_callback(self):
        """定时器回调函数：每次被调用时发布一条消息"""
        msg = Float64()             # 创建消息对象
        msg.data = self.angle       # 设置消息内容
        self.pub.publish(msg)       # 发布消息到话题
        self.get_logger().info(f'发布: joint1 = {self.angle:.1f}°')
        
        self.angle += 5.0           # 每次增加 5 度
        if self.angle > 90.0:       # 超过 90 度后重置
            self.angle = 0.0


def main():
    rclpy.init()                    # 初始化 ROS2
    node = SimplePublisher()        # 创建节点实例
    
    try:
        rclpy.spin(node)            # 保持节点运行，处理回调
    except (KeyboardInterrupt, ExternalShutdownException):
        pass                        # Ctrl+C 优雅退出
    finally:
        node.destroy_node()         # 销毁节点
        if rclpy.ok():
            rclpy.shutdown()            # 关闭 ROS2


if __name__ == '__main__':          # Python 入口点
    main()
