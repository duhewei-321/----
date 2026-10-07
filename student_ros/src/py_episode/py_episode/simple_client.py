#!/usr/bin/env python3
"""
极简 Service Client：调用两数相加服务
"""
import rclpy
from rclpy.node import Node
from example_interfaces.srv import AddTwoInts    # 标准服务接口


class SimpleClient(Node):
    """简单客户端节点"""
    
    def __init__(self):
        super().__init__('simple_client')
        
        # 创建 Client：服务名和类型必须与 Server 一致
        self.cli = self.create_client(AddTwoInts, 'add_two_ints')
        
        # 等待服务可用
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('服务不可用，等待中...')
        
        self.get_logger().info('Service Client 已就绪')
    
    def send_request(self, a, b):
        """发送请求并等待响应"""
        # 创建请求对象
        request = AddTwoInts.Request()
        request.a = a
        request.b = b
        
        self.get_logger().info(f'发送请求: {a} + {b} = ?')
        
        # 异步调用服务
        future = self.cli.call_async(request)
        
        # 等待响应完成
        rclpy.spin_until_future_complete(self, future)

        # 获取结果
        response = future.result()
        self.get_logger().info(f'收到响应: {a} + {b} = {response.sum}')
        
        return response.sum


def main():
    rclpy.init()
    node = SimpleClient()
    
    try:
        # 发送几次请求测试
        node.send_request(3, 5)
        node.send_request(10, 20)
        node.send_request(100, 200)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()