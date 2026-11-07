import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from mars_msgs.msg import RoverOdometry
import math
from rcl_interfaces.msg import SetParametersResult


class OdomNode(Node):
    def __init__(self):
        super().__init__('odom_node')
        self.sub = self.create_subscription(Twist, '/cmd_vel',self.createmsg,10)
        self.pub = self.create_publisher(RoverOdometry, '/rover/odom', 10)

        self.declare_parameter('speed_limit', 2.0)
        self.declare_parameter('rover_id',1)
        self.declare_parameter('odom_hz',1.0)

        self.speed_limit  = self.get_parameter('speed_limit').get_parameter_value().double_value
        self.rover_id  = self.get_parameter('rover_id').get_parameter_value().integer_value
        self.odom_hz  = self.get_parameter('odom_hz').get_parameter_value().double_value

        self.x = 0.0
        self.y = 0.0
        self.heading = 0.0
        self.add_on_set_parameters_callback(self.on_param_change)
        self.velocity = Twist()
        self.publish_timer = self.create_timer(1/(self.odom_hz),self.publish_odometry)
        self.update_timer = self.create_timer(0.05,self.updateOdom)

    def on_param_change(self,params):
        for param in params:
            if param.name == 'speed_limit':
                self.speed_limit = param.value
                self.get_logger().info(f"Live parameter update: speed_limit set to {self.speed_limit} m/s")
        return SetParametersResult(successful=True)

    
    def createmsg(self,msg):
        self.velocity = msg
        if(msg.linear.x)>self.speed_limit:
            self.get_logger().warn(f"Speed Limit exceeded. Speed is {msg.linear.x:.2f}")

    def updateOdom(self):
        dt = 0.05
        v = self.velocity.linear.x
        w = self.velocity.angular.z
        
        if abs(w) < 1e-5:
            self.x += v * math.cos(self.heading) * dt
            self.y += v * math.sin(self.heading) * dt
            self.heading += w * dt
        else:
            self.x += (v / w) * (math.sin(self.heading + w * dt) - math.sin(self.heading))
            self.y -= (v / w) * (math.cos(self.heading + w * dt) - math.cos(self.heading))
            self.heading += w * dt

        self.heading = math.atan2(math.sin(self.heading), math.cos(self.heading))

    def publish_odometry(self):
        msg = RoverOdometry()
        
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "odom"
    
        msg.rover_id = self.rover_id
        msg.x = self.x
        msg.y = self.y
        msg.heading = self.heading
        msg.velocity = self.velocity
        
        self.pub.publish(msg)

def main():
    rclpy.init()
    node = OdomNode()
    try: 
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
        
