import random
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String
from mars_msgs.srv import SetMode

class DriveNode(Node):
    def __init__(self):
        super().__init__('drive_node')
        self.declare_parameter('max_speed',3.0)
        self.max_speed  = self.get_parameter('max_speed').get_parameter_value().double_value
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.sub = self.create_subscription(String,'/rover/health',self.health_status,10)
        self.srv = self.create_service(SetMode,'/rover/set_mode',self.handle_mode)
        self.current_twist = Twist()
        self.speed_scale = 0
        self.mode = "AUTO"
        self.health = "HEALTHY"
        self.publish_timer = self.create_timer(0.1, self.publish_velocity)
        self.update_timer = self.create_timer(3.0, self.update_velocity)
        self.update_velocity()

    def handle_mode(self,request,response):
        req_mode = request.mode.upper()

        if req_mode == "MISSION" and self.health in ["CRITICAL", "OVERHEAT"]:
            response.accepted = False
            response.reason = f"Refused MISSION: Rover health is currently {self.health}"
            self.get_logger().warn(response.reason)
            return response

        if req_mode in ["AUTO", "HOLD", "MISSION"]:
            self.mode = req_mode
            response.accepted = True
            response.reason = f"Mode changed to {self.mode}"
            self.get_logger().info(response.reason)
        else:
            response.accepted = False
            response.reason = f"Invalid mode requested: {request.mode}"

        return response
    
    def health_status(self, msg):
        health = msg.data
        if health == "HEALTHY":
            self.speed_scale = 1.0
        elif health == "WARNING":
            self.speed_scale = 0.5
        elif health in ["CRITICAL", "OVERHEAT"]:
            self.speed_scale = 0.0

    def publish_velocity(self):
        self.pub.publish(self.current_twist)

    def update_velocity(self):
        speed = self.max_speed
        if self.mode == "MISSION":
            return
        if self.mode == "HOLD":
            self.linear.x = 0.0
            self.angular.z = 0.0
        elif self.mode == "AUTO":
            self.current_twist.linear.x = random.uniform(0.0, speed)*self.speed_scale
            self.current_twist.angular.z = random.uniform(-0.5, 0.5)*self.speed_scale
        

def main():
    
    rclpy.init()
    node = DriveNode()
    try: 
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

