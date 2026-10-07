#!/usr/bin/env python3
"""
机械臂接口节点 - 初始化 + 发布电机角度 + 舵机夹爪服务 + 角度模式动作
在上一章基础上新增 Action Server 功能
演示 Topic + Service + Action 三种通信方式的综合应用
"""
import time
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse  # 新增：取消和目标响应
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor

from robot_arm_interfaces.msg import MotorAngles           # Topic 消息
from robot_arm_interfaces.srv import ServoGripper          # Service 接口
from robot_arm_interfaces.action import AngleMode          # Action 接口（新增）

# 导入电机控制核心库
from episode_controller_core.controller_core import MotorControl


class RobotInterfaceNode(Node):
    """机械臂接口节点：Topic + Service + Action 完整演示"""
    
    def __init__(self):
        super().__init__('robot_interface_node')
        
        # ========== 新增：可重入回调组（支持 Action 取消） ==========
        self.callback_group = ReentrantCallbackGroup()
        
        # ========== 配置参数 ==========
        self.declare_parameter('usb_index', 1)
        self.declare_parameter('init_mode', 1)  
        self.declare_parameter('publish_rate', 30.0)

        self.usb_index = self.get_parameter('usb_index').get_parameter_value().integer_value
        self.init_mode = self.get_parameter('init_mode').get_parameter_value().integer_value
        self.publish_rate = self.get_parameter('publish_rate').get_parameter_value().double_value

        self.home_position = [180, 90, 83, 30, 110, 30]
        self.calibration_timeout = 120.0
        self.cached_motor_angles = [0.0] * 6
        
        # ========== 初始化电机控制 ==========
        self.motor_control = None
        self._initialize_robot()
        
        # ========== 创建 Topic Publisher ==========
        self.publisher = self.create_publisher(
            MotorAngles,
            'motor_angles',
            10
        )
        self.get_logger().info('Topic 发布器已创建: /motor_angles')
        
        # ========== 创建 Service Server（舵机夹爪） ==========
        self.servo_gripper_srv = self.create_service(
            ServoGripper,
            'servo_gripper',
            self.servo_gripper_callback,
            callback_group=self.callback_group
        )
        self.get_logger().info('Service 服务已创建: /servo_gripper')
        
        # ========== 新增：创建 Action Server（角度模式，支持取消） ==========
        self.angle_mode_action_server = ActionServer(
            self,
            AngleMode,                           # Action 类型
            'angle_mode',                        # Action 名称
            self.angle_mode_callback,            # 执行回调
            callback_group=self.callback_group,  # 使用可重入回调组
            goal_callback=self.goal_callback,    # 目标接收回调（新增）
            cancel_callback=self.cancel_callback # 取消请求回调（新增）
        )
        self.get_logger().info('Action 服务已创建: /angle_mode (支持取消)')
        
        # ========== 创建定时器 ==========
        timer_period = 1.0 / self.publish_rate
        self.timer = self.create_timer(timer_period, self.publish_motor_angles)
        
        self.get_logger().info('='*50)
        self.get_logger().info('机械臂接口节点已启动')
        self.get_logger().info(f'  - Topic:   /motor_angles ({self.publish_rate} Hz)')
        self.get_logger().info(f'  - Service: /servo_gripper')
        self.get_logger().info(f'  - Action:  /angle_mode')
        self.get_logger().info('='*50)
    
    # ==================== 初始化相关方法 ====================
    
    def _initialize_robot(self):
        """初始化机械臂"""
        mode_name = "回零校准" if self.init_mode == 0 else "从当前位置恢复"
        self.get_logger().info(f'开始初始化机械臂，usb_index={self.usb_index}, init_mode={self.init_mode} ({mode_name})')
        
        self.motor_control = MotorControl(self.usb_index)
        if not self.motor_control.initialized:
            self.get_logger().error('CAN 设备初始化失败')
            raise RuntimeError('CAN 设备初始化失败')
        self.get_logger().info('CAN 通信初始化成功')
        
        if self.init_mode == 1:
            self._recover_from_current()
        else:
            self._perform_calibration()
    
    def _recover_from_current(self):
        """从当前位置恢复"""
        self.get_logger().info('从当前位置恢复中...')
        current_angles = self.motor_control.read_motor_angles()
        if not current_angles:
            raise RuntimeError('无法读取电机角度')
        self.motor_control.last_degrees = [
            current_angles[i] * self.motor_control.motor_ratios[i] 
            for i in range(6)
        ]
        self.cached_motor_angles = list(current_angles)
        self.get_logger().info(f'成功从当前位置恢复: {current_angles}')
    
    def _perform_calibration(self):
        """执行回零校准"""
        self.get_logger().info('开始回零校准流程...')
        for joint_index, addr in enumerate(self.motor_control.motor_address):
            self.get_logger().info(f'正在校准关节 {joint_index + 1}/6 ...')
            self.motor_control.trigger_home(addr, 0x02)
            time.sleep(0.05)
            
            start_time = time.perf_counter()
            while True:
                if self.motor_control.check_home_status(addr):
                    self.get_logger().info(f'关节 {joint_index + 1} 校准完成')
                    break
                if time.perf_counter() - start_time > self.calibration_timeout:
                    raise RuntimeError(f'关节 {joint_index + 1} 校准超时')
                time.sleep(0.5)
        
        self.get_logger().info(f'校准完成，正在移动到 Home 位置: {self.home_position}')
        time.sleep(1.0)
        move_time = self.motor_control.execute_motors_degrees_normal(self.home_position)
        time.sleep(move_time)
        self.cached_motor_angles = list(self.home_position)
        self.get_logger().info('机械臂初始化完成')
    
    # ==================== Topic 发布 ====================
    
    def publish_motor_angles(self):
        """定时器回调：发布电机角度"""
        if self.motor_control is None:
            return
        
        msg = MotorAngles()
        msg.timestamp = self.get_clock().now().to_msg()
        
        try:
            angles = self.motor_control.read_motor_angles()
            if angles and all(angle is not None for angle in angles):
                msg.angles = angles
                msg.success = True
                msg.message = "读取成功"
                self.cached_motor_angles = list(angles)
            else:
                msg.angles = self.cached_motor_angles
                msg.success = False
                msg.message = "读取失败"
        except Exception as e:
            msg.angles = self.cached_motor_angles
            msg.success = False
            msg.message = f"读取异常: {str(e)}"
        
        self.publisher.publish(msg)
    
    # ==================== Service 回调 ====================
    
    def servo_gripper_callback(self, request, response):
        """舵机夹爪服务回调函数"""
        try:
            if self.motor_control is None:
                response.success = False
                response.message = "电机控制未初始化"
                response.actual_angle = 0
                return response
            
            target_angle = request.angle
            clamped_angle = max(0, min(target_angle, 110))
            
            self.motor_control.servo_gripper(clamped_angle)
            
            response.success = True
            response.actual_angle = clamped_angle
            
            if target_angle != clamped_angle:
                response.message = f'角度已限制: 请求 {target_angle}° -> 实际 {clamped_angle}°'
            else:
                response.message = f'夹爪已设置到 {clamped_angle}°'
            
            self.get_logger().info(f'[Service] {response.message}')
            
        except Exception as e:
            response.success = False
            response.message = f'控制失败: {str(e)}'
            response.actual_angle = 0
            self.get_logger().error(f'[Service] {response.message}')
        
        return response
    
    # ==================== 新增：Action 回调 ====================
    
    def goal_callback(self, goal_request):
        """
        目标接收回调：决定是否接受目标
        
        参数:
            goal_request: 目标请求（包含 angles 和 speed_ratio）
        
        返回:
            GoalResponse.ACCEPT 或 GoalResponse.REJECT
        """
        self.get_logger().info('[Action] 收到目标请求')
        
        # 可以在这里添加目标验证逻辑
        angles = goal_request.angles
        if len(angles) != 6:
            self.get_logger().warn(f'[Action] 拒绝目标：角度数量错误（期望6个，收到{len(angles)}个）')
            return GoalResponse.REJECT
        
        # 接受目标
        return GoalResponse.ACCEPT
    
    def cancel_callback(self, goal_handle):
        """
        取消请求回调：决定是否允许取消
        
        参数:
            goal_handle: 目标句柄
        
        返回:
            CancelResponse.ACCEPT 或 CancelResponse.REJECT
        """
        self.get_logger().info('[Action] 收到取消请求，准备紧急停止')
        
        # 触发紧急停止
        if self.motor_control is not None:
            try:
                self.motor_control.set_emergency_stop(active=True)
                self.get_logger().warn('[Action] 已触发紧急停止')
                
                # 更新电机控制器的角度记录，确保下次运动计算准确
                # 使用缓存的角度（Topic 持续更新）
                self.motor_control.last_degrees = [
                    self.cached_motor_angles[i] * self.motor_control.motor_ratios[i] 
                    for i in range(6)
                ]
                self.get_logger().info('[Action] 已更新电机角度记录')
            except Exception as e:
                self.get_logger().error(f'[Action] 紧急停止失败: {str(e)}')
        
        # 接受取消请求
        return CancelResponse.ACCEPT
    
    def angle_mode_callback(self, goal_handle):
        """
        角度模式动作回调函数
        
        参数:
            goal_handle: 目标句柄，包含请求参数和状态控制方法
        
        返回:
            AngleMode.Result: 执行结果
        """
        self.get_logger().info('[Action] 接收到角度模式目标...')
        
        # 创建结果消息
        result = AngleMode.Result()
        
        # 检查电机控制是否已初始化
        if self.motor_control is None:
            result.success = False
            result.message = "电机控制未初始化"
            result.execution_time = 0.0
            result.final_angles = self.cached_motor_angles
            self.get_logger().error(f'[Action] {result.message}')
            goal_handle.abort()
            return result
        
        # 获取目标参数
        angles = list(goal_handle.request.angles)
        speed_ratio = goal_handle.request.speed_ratio
        
        # 参数验证
        if len(angles) != 6:
            result.success = False
            result.message = f"角度数量错误: 期望 6 个，实际 {len(angles)} 个"
            result.execution_time = 0.0
            result.final_angles = self.cached_motor_angles
            self.get_logger().error(f'[Action] {result.message}')
            goal_handle.abort()
            return result
        
        if not (0.0 < speed_ratio <= 1.0):
            speed_ratio = max(0.1, min(speed_ratio, 1.0))
            self.get_logger().warn(f'[Action] 速度比例已限制为: {speed_ratio}')
        
        self.get_logger().info(f'[Action] 目标角度: {angles}')
        self.get_logger().info(f'[Action] 速度比例: {speed_ratio}')
        
        start_time = time.perf_counter()
        
        try:
            # 调用电机控制 API 执行运动
            execution_time = float(self.motor_control.execute_motors_degrees_normal(
                angles, speed_ratio
            ))
            self.get_logger().info(f'[Action] 预计执行时间: {execution_time:.2f} 秒')
            
            # 发送进度反馈
            steps = 10
            for i in range(steps + 1):
                # 检查是否请求取消
                if goal_handle.is_cancel_requested:
                    # 解除紧急停止，允许后续运动命令
                    if self.motor_control is not None:
                        try:
                            self.motor_control.set_emergency_stop(active=False)
                            self.get_logger().info('[Action] 已解除紧急停止')
                        except Exception as e:
                            self.get_logger().error(f'[Action] 解除紧急停止失败: {str(e)}')
                    
                    result.success = False
                    result.message = "任务被取消"
                    result.execution_time = float(time.perf_counter() - start_time)
                    result.final_angles = self.cached_motor_angles
                    self.get_logger().warn(f'[Action] {result.message}')
                    goal_handle.canceled()
                    return result
                
                # 创建并发布反馈
                feedback_msg = AngleMode.Feedback()
                feedback_msg.elapsed_time = float(time.perf_counter() - start_time)
                feedback_msg.progress = float(i / steps)
                feedback_msg.current_angles = self.cached_motor_angles
                feedback_msg.status_message = f"运动中... {int(i / steps * 100)}%"
                goal_handle.publish_feedback(feedback_msg)
                
                self.get_logger().info(f'[Action] 进度: {int(i / steps * 100)}%')
                
                # 等待（除了最后一步）
                if i < steps:
                    time.sleep(execution_time / steps)
            
            # 运动完成
            result.success = True
            result.message = f"角度模式运动完成"
            result.execution_time = float(time.perf_counter() - start_time)
            result.final_angles = self.cached_motor_angles
            
            self.get_logger().info(f'[Action] {result.message}，耗时: {result.execution_time:.2f} 秒')
            goal_handle.succeed()
            return result
            
        except Exception as e:
            result.success = False
            result.message = f"执行失败: {str(e)}"
            result.execution_time = float(time.perf_counter() - start_time)
            result.final_angles = self.cached_motor_angles
            self.get_logger().error(f'[Action] {result.message}')
            goal_handle.abort()
            return result


def main():
    rclpy.init()
    
    try:
        node = RobotInterfaceNode()
        
        # 使用多线程执行器，支持 Action 取消功能
        executor = MultiThreadedExecutor(num_threads=4)
        executor.add_node(node)
        
        try:
            executor.spin()
        finally:
            executor.shutdown()
            node.destroy_node()
            
    except RuntimeError as e:
        print(f'启动失败: {e}')
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()


if __name__ == '__main__':
    main()