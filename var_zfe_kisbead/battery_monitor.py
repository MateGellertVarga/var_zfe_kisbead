"""Battery health monitor publishing diagnostic_msgs/DiagnosticArray."""

import signal

from diagnostic_msgs.msg import DiagnosticArray, DiagnosticStatus, KeyValue
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import BatteryState


class BatteryMonitor(Node):
    """Classify /battery_state into OK / WARN / ERROR / STALE diagnostics."""

    LEVEL_NAMES = {
        DiagnosticStatus.OK: 'OK',
        DiagnosticStatus.WARN: 'WARN',
        DiagnosticStatus.ERROR: 'ERROR',
        DiagnosticStatus.STALE: 'STALE',
    }

    def __init__(self):
        super().__init__('battery_monitor')
        self.declare_parameter('warn_level', 0.3)    # below 30 % -> WARN
        self.declare_parameter('error_level', 0.1)   # below 10 % -> ERROR
        self.declare_parameter('timeout', 3.0)       # s without data -> STALE

        self.last_msg = None
        self.last_time = None
        self.last_level = None
        self.sub = self.create_subscription(
            BatteryState, 'battery_state', self.battery_callback, 10)
        self.pub = self.create_publisher(DiagnosticArray, 'diagnostics', 10)
        self.timer = self.create_timer(1.0, self.loop)
        self.get_logger().info('battery_monitor started, publishing /diagnostics')

    def battery_callback(self, msg):
        """Store the latest battery message."""
        self.last_msg = msg
        self.last_time = self.get_clock().now()

    def evaluate(self):
        """Return (level, message) for the current battery state."""
        timeout = self.get_parameter('timeout').value
        if self.last_msg is None:
            return DiagnosticStatus.STALE, 'No battery data yet'
        age = (self.get_clock().now() - self.last_time).nanoseconds * 1e-9
        if age > timeout:
            return DiagnosticStatus.STALE, f'No battery data for {age:.1f} s'
        pct = self.last_msg.percentage
        if self.last_msg.power_supply_status == BatteryState.POWER_SUPPLY_STATUS_CHARGING:
            return DiagnosticStatus.OK, f'Charging ({pct:.0%})'
        if pct < self.get_parameter('error_level').value:
            return DiagnosticStatus.ERROR, f'Critical battery ({pct:.0%}), return to charger!'
        if pct < self.get_parameter('warn_level').value:
            return DiagnosticStatus.WARN, f'Low battery ({pct:.0%})'
        return DiagnosticStatus.OK, f'Battery OK ({pct:.0%})'

    def loop(self):
        """Publish the diagnostic status once per second."""
        level, text = self.evaluate()
        status = DiagnosticStatus(
            level=level, name='battery_monitor: Battery', message=text, hardware_id='battery')
        if self.last_msg is not None:
            status.values = [
                KeyValue(key='percentage', value=f'{self.last_msg.percentage:.3f}'),
                KeyValue(key='voltage', value=f'{self.last_msg.voltage:.2f}'),
            ]
        array = DiagnosticArray(status=[status])
        array.header.stamp = self.get_clock().now().to_msg()
        self.pub.publish(array)

        if level != self.last_level:  # log only on state change
            self.get_logger().info(f'[{self.LEVEL_NAMES[level]}] {text}')
            self.last_level = level


def main(args=None):
    rclpy.init(args=args)
    node = BatteryMonitor()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass  # clean exit on Ctrl+C
    finally:
        signal.signal(signal.SIGINT, signal.SIG_IGN)  # ignore repeated Ctrl+C
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
