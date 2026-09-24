from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'var_zfe_kisbead'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name), glob('launch/*launch.[pxy][yma]*')), 
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Varga Máté Gellért',
    maintainer_email='vargamategellert@gmail.com',
    description='Simulated battery publisher and battery health monitor (sensor_msgs/BatteryState, diagnostic_msgs/DiagnosticArray)',
    license='GNU General Public License v3.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'battery_sim = var_zfe_kisbead.battery_sim:main',
        ],
    },
)
