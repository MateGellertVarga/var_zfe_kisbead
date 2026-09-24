"""Simulated robot battery publishing sensor_msgs/BatteryState."""

import random
import signal

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import BatteryState


class BatterySim(Node):
    """Simulate a 3S LiPo battery with a repeating discharge / charge cycle."""

    CELLS = 3
    CELL_EMPTY_V = 3.3  # volt per cell at 0 %
    CELL_FULL_V = 4.2   # volt per cell at 100 %

    def __init__(self):
        super().__init__('battery_sim')
        self.declare_parameter('publish_rate', 2.0)     # Hz
        self.declare_parameter('discharge_rate', 0.02)  # fraction of charge / s
        self.declare_parameter('charge_rate', 0.05)     # fraction of charge / s
        self.declare_parameter('capacity', 5.0)         # Ah

        self.dt = 1.0 / self.get_parameter('publish_rate').value
        self.level = 1.0        # state of charge, 0.0 .. 1.0
        self.charging = False
        self.pub = self.create_publisher(BatteryState, 'battery_state', 10)
        self.timer = self.create_timer(self.dt, self.loop)
        self.get_logger().info('battery_sim started, publishing /battery_state')

    def update_level(self):
        """Step the state of charge and switch between charging and discharging."""
        if self.charging:
            rate = self.get_parameter('charge_rate').value
            self.level = min(1.0, self.level + rate * self.dt)
            if self.level >= 1.0:
                self.charging = False
                self.get_logger().info('Battery full, back to work')
        else:
            rate = self.get_parameter('discharge_rate').value
            self.level = max(0.0, self.level - rate * self.dt)
            if self.level <= 0.0:
                self.charging = True
                self.get_logger().info('Battery empty, docking to charger')

    def loop(self):
        """Publish one BatteryState message."""
        self.update_level()
        capacity = self.get_parameter('capacity').value
        cell_v = self.CELL_EMPTY_V + (self.CELL_FULL_V - self.CELL_EMPTY_V) * self.level

        msg = BatteryState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'battery'
        msg.cell_voltage = [cell_v + random.gauss(0.0, 0.005) for _ in range(self.CELLS)]
        msg.voltage = sum(msg.cell_voltage)
        msg.percentage = self.level
        msg.capacity = capacity
        msg.design_capacity = capacity
        msg.charge = self.level * capacity
        msg.current = 3.0 if self.charging else -2.0  # positive = charging
        msg.temperature = float('nan')  # not measured
        msg.power_supply_status = (
            BatteryState.POWER_SUPPLY_STATUS_CHARGING if self.charging
            else BatteryState.POWER_SUPPLY_STATUS_DISCHARGING)
        msg.power_supply_health = BatteryState.POWER_SUPPLY_HEALTH_GOOD
        msg.power_supply_technology = BatteryState.POWER_SUPPLY_TECHNOLOGY_LIPO
        msg.present = True
        self.pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = BatterySim()
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
