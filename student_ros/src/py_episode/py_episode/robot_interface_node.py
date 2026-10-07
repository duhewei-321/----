#!/usr/bin/env python3
"""
机械臂接口节点 - 初始化 + 发布电机角度
支持两种初始化模式：
  - init_mode=0: 回零校准（calibration）
  - init_mode=1: 从当前位置恢复（recover from current）
"""
import time
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from robot_arm_interfaces.msg import MotorAngles

# 导入电机控制核心库
from episode_controller_core.controller_core import MotorControl


class RobotInterfaceNode(Node):
    """机械臂接口节点：初始化 + 发布关节角度"""
    
    def __init__(self):
        super().__init__('robot_interface_node')
        
        # ========== 配置参数（直接写死，便于理解）==========
        self.usb_index = 1          # USB-CAN 适配器索引（根据实际情况修改）
        self.init_mode = 0          # 初始化模式：0=回零校准, 1=从当前位置恢复
        self.publish_rate = 30.0    # 发布频率（Hz）
        self.home_position = [180, 90, 83, 30, 110, 30]  # Home 位置
        self.calibration_timeout = 120.0  # 每个关节校准超时时间（秒）
        



                # 声明参数（带默认值）
        self.declare_parameter('usb_index', 1)
        self.declare_parameter('init_mode', 1)  
        self.declare_parameter('publish_rate', 30.0)

        # 读取参数值
        self.usb_index = self.get_parameter('usb_index').get_parameter_value().integer_value
        self.init_mode = self.get_parameter('init_mode').get_parameter_value().integer_value
        self.publish_rate = self.get_parameter('publish_rate').get_parameter_value().double_value
                # 缓存的电机角度
        self.cached_motor_angles = [0.0] * 6
        
        # ========== 初始化电机控制 ==========
        self.motor_control = None
        self._initialize_robot()
        
        # ========== 创建 Publisher ==========
        self.publisher = self.create_publisher(
            MotorAngles,        # 消息类型
            'motor_angles',     # 话题名称
            10                  # 队列大小
        )
        
        # ========== 创建定时器 ==========
        timer_period = 1.0 / self.publish_rate
        self.timer = self.create_timer(timer_period, self.publish_motor_angles)
        
        self.get_logger().info(f'机械臂接口节点已启动，发布频率: {self.publish_rate} Hz')
    
    def _initialize_robot(self):
        """初始化机械臂：根据 init_mode 选择不同的初始化方式"""
        mode_name = "回零校准" if self.init_mode == 0 else "从当前位置恢复"
        self.get_logger().info(f'开始初始化机械臂，usb_index={self.usb_index}, init_mode={self.init_mode} ({mode_name})')
        
        # 步骤 1：初始化 CAN 通信
        self.motor_control = MotorControl(self.usb_index)
        if not self.motor_control.initialized:
            self.get_logger().error('CAN 设备初始化失败，请检查 USB-CAN 适配器连接')
            raise RuntimeError('CAN 设备初始化失败')
        self.get_logger().info('CAN 通信初始化成功')
        
        # ========== 根据 init_mode 选择初始化方式 ==========
        if self.init_mode == 1:
            # 模式 1：从当前位置恢复
            self._recover_from_current()
        else:
            # 模式 0：回零校准（默认）
            self._perform_calibration()
    
    def _recover_from_current(self):
        """模式 1：从当前位置恢复，跳过回零校准"""
        self.get_logger().info('从当前位置恢复中...')
        
        # 读取当前编码器位置
        current_angles = self.motor_control.read_motor_angles()
        if not current_angles:
            self.get_logger().error('从当前位置恢复失败 - 无法读取电机角度')
            raise RuntimeError('无法读取电机角度')
        
        # 更新系统记录的角度
        self.motor_control.last_degrees = [
            current_angles[i] * self.motor_control.motor_ratios[i] 
            for i in range(6)
        ]
        
        self.get_logger().info(f'成功从当前位置恢复: {current_angles}')
    
    def _perform_calibration(self):
        """模式 0：执行完整的回零校准流程"""
        # 步骤 2：依次校准各关节
        self.get_logger().info('开始回零校准流程（请确保周围无障碍物）...')
        for joint_index, addr in enumerate(self.motor_control.motor_address):
            self.get_logger().info(f'正在校准关节 {joint_index + 1}/6 ...')
            
            # 触发回零
            self.motor_control.trigger_home(addr, 0x02)
            time.sleep(0.05)
            
            # 等待校准完成
            start_time = time.perf_counter()
            while True:
                if self.motor_control.check_home_status(addr):
                    self.get_logger().info(f'关节 {joint_index + 1} 校准完成')
                    break
                
                # 超时检查
                elapsed = time.perf_counter() - start_time
                if elapsed > self.calibration_timeout:
                    self.get_logger().error(f'关节 {joint_index + 1} 校准超时')
                    raise RuntimeError(f'关节 {joint_index + 1} 校准超时')
                
                time.sleep(0.5)
        
        # 步骤 3：移动到 Home 位置
        self.get_logger().info(f'校准完成，正在移动到 Home 位置: {self.home_position}')
        time.sleep(1.0)
        move_time = self.motor_control.execute_motors_degrees_normal(self.home_position)
        time.sleep(move_time)
        
        self.get_logger().info('机械臂初始化完成，已到达 Home 位置')
    
    def publish_motor_angles(self):
        """定时器回调：读取并发布电机角度"""
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
                msg.message = "读取失败 - 某些角度为 None"
        except Exception as e:
            msg.angles = self.cached_motor_angles
            msg.success = False
            msg.message = f"读取异常: {str(e)}"
            self.get_logger().error(msg.message)
        
        self.publisher.publish(msg)


def main():
    rclpy.init()
    
    try:
        node = RobotInterfaceNode()
        rclpy.spin(node)
    except RuntimeError as e:
        print(f'启动失败: {e}')
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
