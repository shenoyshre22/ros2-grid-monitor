from setuptools import find_packages, setup

package_name = 'grid_monitor'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='arc',
    maintainer_email='shenoyshreya0222@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        'voltage_simulator = grid_monitor.voltage_simulator:main',
        'dashboard_gui = grid_monitor.dashboard_gui:main',
        ],
    },
)
