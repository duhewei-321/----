#!/usr/bin/env python3
"""
角度模式控制客户端 - 通过命令行参数控制机械臂运动到指定角度
演示如何在独立节点中使用 Action Client
"""
import sys
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.action import ActionClient
from robot_arm_interfaces.action import AngleMode


class AnglesControlClient(Node):
    """角度模式控制客户端节点"""
    
    def __init__(self):
        super().__init__('angles_control_client')
        
        # 创建 Action Client
        self.declare_parameter('action_name', 'angle_mode')
        action_name = self.get_parameter('action_name').get_parameter_value().string_value
        self.action_client = ActionClient(self, AngleMode, action_name)
        
        # 等待 Action Server 可用
        self.get_logger().info('等待角度模式 Action Server...')
        while not self.action_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().info('服务不可用，继续等待...')
        
        self.get_logger().info('角度模式 Action Server 已连接')
        
        # 用于跟踪目标句柄
        self._goal_handle = None
    
    def send_goal(self, angles, speed_ratio=0.5):
        """
        发送角度模式目标
        
        参数:
            angles: 6 个关节的目标角度列表
            speed_ratio: 运动速度比例（0.0-1.0）
        """
        # 创建目标消息
        goal_msg = AngleMode.Goal()
        goal_msg.angles = angles
        goal_msg.speed_ratio = speed_ratio
        
        self.get_logger().info(f'发送目标: angles={angles}, speed_ratio={speed_ratio}')
        
        # 异步发送目标，注册反馈回调
        self._send_goal_future = self.action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        
        # 注册目标响应回调
        self._send_goal_future.add_done_callback(self.goal_response_callback)
    
    def goal_response_callback(self, future):
        """目标响应回调：处理目标是否被接受"""
        self._goal_handle = future.result()
        
        if not self._goal_handle.accepted:
            self.get_logger().error('✗ 目标被拒绝')
            if rclpy.ok():
                rclpy.shutdown()
            return
        
        self.get_logger().info('✓ 目标被接受，等待执行...')
        
        # 获取结果
        self._get_result_future = self._goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)
    
    def feedback_callback(self, feedback_msg):
        """反馈回调：处理执行过程中的进度更新"""
        feedback = feedback_msg.feedback
        
        # 显示进度条
        progress_bar = self._create_progress_bar(feedback.progress)
        
        self.get_logger().info(
            f'反馈: {progress_bar} {feedback.progress*100:.0f}% | '
            f'已用时: {feedback.elapsed_time:.1f}s | '
            f'{feedback.status_message}'
        )
    
    def get_result_callback(self, future):
        """结果回调：处理任务完成后的最终结果"""
        result = future.result().result
        
        self.get_logger().info('='*50)
        
        if result.success:
            self.get_logger().info('✓ 任务成功！')
            self.get_logger().info(f'  消息: {result.message}')
            self.get_logger().info(f'  执行时间: {result.execution_time:.2f} 秒')
            self.get_logger().info(f'  最终角度: {list(result.final_angles)}')
        else:
            self.get_logger().error('✗ 任务失败！')
            self.get_logger().error(f'  消息: {result.message}')
        
        self.get_logger().info('='*50)
        
        # 任务完成，关闭节点
        if rclpy.ok():
            rclpy.shutdown()
    
    def _create_progress_bar(self, progress, width=20):
        """创建文本进度条"""
        filled = int(width * progress)
        bar = '█' * filled + '░' * (width - filled)
        return f'[{bar}]'


def main():
    # 解析命令行参数
    if len(sys.argv) < 7:
        print('用法: ros2 run py_episode angles_ctrl <j1> <j2> <j3> <j4> <j5> <j6> [speed_ratio]')
        print()
        print('参数说明:')
        print('  j1-j6: 6 个关节的目标角度（单位：度）')
        print('  speed_ratio: 运动速度比例 0.0-1.0（可选，默认 0.5）')
        print()
        print('示例:')
        print('  ros2 run py_episode angles_ctrl 150 80 90 45 100 60       # 默认速度')
        print('  ros2 run py_episode angles_ctrl 150 80 90 45 100 60 0.3   # 慢速')
        print('  ros2 run py_episode angles_ctrl 180 90 83 30 110 30 0.8   # 快速回到 Home')
        sys.exit(1)
    
    # 解析角度参数
    try:
        angles = [float(sys.argv[i]) for i in range(1, 7)]
    except ValueError as e:
        print(f'错误: 角度参数必须是数字，但收到: {sys.argv[1:7]}')
        sys.exit(1)
    
    # 解析速度比例（可选）
    speed_ratio = 0.5
    if len(sys.argv) >= 8:
        try:
            speed_ratio = float(sys.argv[7])
            if not (0.0 < speed_ratio <= 1.0):
                print(f'警告: 速度比例应在 0.0-1.0 之间，已自动限制')
                speed_ratio = max(0.1, min(speed_ratio, 1.0))
        except ValueError:
            print(f'警告: 无法解析速度比例 "{sys.argv[7]}"，使用默认值 0.5')
    
    # 初始化节点
    rclpy.init()
    node = AnglesControlClient()
    
    try:
        # 发送目标
        node.send_goal(angles, speed_ratio)
        
        # 保持节点运行，等待回调
        rclpy.spin(node)
        
    except (KeyboardInterrupt, ExternalShutdownException):
        # 用户按 Ctrl+C 取消
        node.get_logger().warn('\n检测到 Ctrl+C，正在取消任务...')
        if node._goal_handle is not None:
            # 发送取消请求
            cancel_future = node._goal_handle.cancel_goal_async()
            # 等待取消完成
            rclpy.spin_until_future_complete(node, cancel_future, timeout_sec=2.0)
            if cancel_future.result():
                node.get_logger().info('取消请求已发送')
            else:
                node.get_logger().error('取消请求发送失败')
    finally:
        if rclpy.ok():
            node.destroy_node()
            if rclpy.ok():
                rclpy.shutdown()


if __name__ == '__main__':
    main()
