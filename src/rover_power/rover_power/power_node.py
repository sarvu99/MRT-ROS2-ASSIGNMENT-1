import random
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from geometry_msgs.msg import Twist
class PowerNode(Node):
    def __init__(self):
        super().__init__('power_node')
        self.declare_parameter('publish_hz', 2.0)
        self.declare_parameter('drain_coeff',1.0)
        self.publish_hz = self.get_parameter('publish_hz').get_parameter_value().double_value
        self.drain_coeff = self.get_parameter('drain_coeff').get_parameter_value().double_value
        self.pub = self.create_publisher(Float32MultiArray, '/rover/power', 10)
        self.sub = self.create_subscription(Twist,'/cmd_vel',self.values,10)
        self.timer = self.create_timer(1/(self.publish_hz), self.tick)
        # 2 Hz for now
        self.battery = 100.0
        self.temperature = 20.0
        self.current_v = 0.0
        self.drain_rate = 0.0
        self.t_last = self.get_clock().now()

    def values(self,msg):
        self.current_v = abs(msg.linear.x)

    def tick(self):
        # todo: reduce battery by a small random amount, never below 0
        t_now = self.get_clock().now()
        dt = (t_now-self.t_last).nanoseconds / 1e9
        self.drain_rate = 0.05 + (self.drain_coeff * self.current_v)
        if(self.temperature > 60) or (self.temperature < 0):
            self.drain_rate *= 1.5
        self.battery = max(0.0, self.battery - self.drain_rate*dt)

        # todo: change temperature by a random step of at most 0.5,and keep it between -20 and 80
        random_step = -0.5 + random.random()
        self.temperature = min(80,self.temperature+random_step) if (self.temperature+random_step > -20) else -20
        
        msg = Float32MultiArray()
        msg.data = [self.battery, self.temperature, self.drain_rate]
        self.pub.publish(msg)
        self.get_logger().info(f'battery={self.battery:.1f}% temp={self.temperature:.1f}C drain rate = {self.drain_rate:.1f}%/s ')

def main():
    rclpy.init()
    node = PowerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()