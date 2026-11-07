import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray, String
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy

class MonitorNode(Node):
    def __init__(self):
        super().__init__('monitor_node')

        self.declare_parameter('publish_hz', 2.0)
        publish_hz = self.get_parameter('publish_hz').value
        # Timeout threshold = 3 publish periods
        self.timeout_sec = 3.0 * (1.0 / publish_hz if publish_hz > 0 else 0.5)

        qos_profile = QoSProfile(
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            reliability=ReliabilityPolicy.RELIABLE
        )

        self.sub_power = self.create_subscription(Float32MultiArray, '/rover/power', self.report1, 10)
        self.sub_health = self.create_subscription(String, '/rover/health', self.report2, qos_profile)

        self.last_power_time = None
        self.last_health_time = None
        
        self.latest_battery = None
        self.latest_temp = None
        self.latest_health = None

        self.timer = self.create_timer(1.0, self.display_status)

    def report1(self, msg):
        self.last_power_time = self.get_clock().now()
        self.latest_battery = msg.data[0]
        self.latest_temp = msg.data[1]

    def report2(self, msg):
        self.last_health_time = self.get_clock().now()
        self.latest_health = msg.data

    def display_status(self):
        now = self.get_clock().now()

        # Check power topic staleness
        if self.last_power_time is None:
            power_str = "battery N/A | temp N/A [STALE]"
        elif (now - self.last_power_time).nanoseconds/1e9 > self.timeout_sec:
            power_str = f"battery {self.latest_battery:.1f}% | temp {self.latest_temp:.1f} C [STALE]"
        else:
            power_str = f"battery {self.latest_battery:.1f}% | temp {self.latest_temp:.1f} C"

        # Check health topic staleness
        if self.last_health_time is None:
            health_str = "health N/A [STALE]"
        elif (now - self.last_health_time).nanoseconds / 1e9 > self.timeout_sec:
            health_str = f"health {self.latest_health} [STALE]"
        else:
            health_str = f"health {self.latest_health}"

        self.get_logger().info(f"[ROVER] {power_str} | {health_str}")

def main():
    rclpy.init()
    node = MonitorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()

if __name__ == '__main__':
    main()