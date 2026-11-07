import math
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from geometry_msgs.msg import Twist
from std_msgs.msg import String, Float32MultiArray
from mars_msgs.msg import RoverOdometry
from mars_msgs.action import DriveTo

class NavigatorNode(Node):
    def __init__(self):
        super().__init__('navigator_node')

        self.pub_cmd = self.create_publisher(Twist, '/cmd_vel', 10)
        self.sub_odom = self.create_subscription(RoverOdometry, '/rover/odom', self.on_odom, 10)
        self.sub_health = self.create_subscription(String, '/rover/health', self.on_health, 10)
        self.sub_power = self.create_subscription(Float32MultiArray, '/rover/power', self.on_power, 10)
        self.sub_mode = self.create_subscription(String, '/rover/mode', self.on_mode, 10)  # Listen to mode

        self.action_server = ActionServer(
            self,
            DriveTo,
            '/rover/drive_to',
            execute_callback=self.execute_callback,
        )

        self.current_x = 0.0
        self.current_y = 0.0
        self.current_heading = 0.0
        self.health = "HEALTHY"
        self.battery_pct = 100.0
        self.current_mode = "AUTO"  

    def on_odom(self, msg):
        self.current_x = msg.x
        self.current_y = msg.y
        self.current_heading = msg.heading

    def on_health(self, msg):
        self.health = msg.data

    def on_power(self, msg):
        self.battery_pct = msg.data[0]

    def on_mode(self, msg):
        self.current_mode = msg.data

    def execute_callback(self, goal_handle):
        self.get_logger().info('Executing DriveTo goal...')
        start_battery = self.battery_pct
        target_x = goal_handle.request.x
        target_y = goal_handle.request.y
        tol = goal_handle.request.tolerance

        feedback_msg = DriveTo.Feedback()
        rate = self.create_rate(2.0)  # 2 Hz feedback rate[cite: 7, 10]

        if goal_handle.is_cancel_requested:
            self.pub_cmd.publish(Twist())
            goal_handle.canceled()
            result = DriveTo.Result()
            result.reached = False
            result.final_error = math.hypot(target_x - self.current_x, target_y - self.current_y)
            result.battery_used = start_battery - self.battery_pct
            return result

        if self.health == "CRITICAL":
            self.pub_cmd.publish(Twist())
            goal_handle.abort()
            result = DriveTo.Result()
            result.reached = False
            result.final_error = math.hypot(target_x - self.current_x, target_y - self.current_y)
            result.battery_used = start_battery - self.battery_pct
            return result

        dx = target_x - self.current_x
        dy = target_y - self.current_y
        dist = math.hypot(dx, dy)

        if dist <= tol:
            self.pub_cmd.publish(Twist())
            goal_handle.succeed()
            result = DriveTo.Result()
            result.reached = True
            result.final_error = dist
            result.battery_used = start_battery - self.battery_pct
            return result

        target_angle = math.atan2(dy, dx)
        angle_error = math.atan2(
            math.sin(target_angle - self.current_heading),
            math.cos(target_angle - self.current_heading)
        )

        cmd = Twist()
        if abs(angle_error) > 0.15:
            cmd.angular.z = 0.5 if angle_error > 0 else -0.5
        else:
            cmd.linear.x = min(1.0, dist)
            cmd.angular.z = 0.5 * angle_error

        self.pub_cmd.publish(cmd)

        feedback_msg.distance_remaining = dist
        feedback_msg.battery_pct = self.battery_pct
        goal_handle.publish_feedback(feedback_msg)

        rate.sleep()

def main():
    rclpy.init()
    node = NavigatorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()