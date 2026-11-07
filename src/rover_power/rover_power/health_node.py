import random
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, String
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy

class HealthNode(Node):
    def __init__(self):
        super().__init__('health_node')
        qos_profile = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE
        )
        self.sub = self.create_subscription(Float32MultiArray, '/rover/power', self.on_power, 10)
        self.pub = self.create_publisher(String, '/rover/health', qos_profile)
        self.oldhealth = None
        
    
    def on_power(self, msg):
        battery, temperature = msg.data[0], msg.data[1]
        if temperature > 70.0:
            status = "OVERHEAT"
        elif battery < 15.0:
            status = "CRITICAL"
        elif self.oldhealth == "WARNING":
            if battery > 43.0:
                status = "HEALTHY"
            else:
                status = "WARNING"
        else:
            if battery <= 40.0:
                status = "WARNING"
            else:
                status = "HEALTHY"
        msg1 = String()
        msg1.data = status
        if(self.oldhealth!=status):
            self.oldhealth = status
            self.pub.publish(msg1)
            self.get_logger().info(f'Status : {status}')
    
def main():
    rclpy.init()
    node = HealthNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()