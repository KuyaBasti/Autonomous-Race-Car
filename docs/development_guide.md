# Development Guide

## Table of Contents
1. [Development Environment Setup](#development-environment-setup)
   - [Prerequisites](#prerequisites)
   - [Initial Setup](#initial-setup)
2. [Code Organization](#code-organization)
   - [Directory Structure](#directory-structure)
   - [Package Structure](#package-structure)
3. [Coding Standards](#coding-standards)
   - [C++ Standards](#c-standards)
   - [Python Standards](#python-standards)
   - [ROS2 Best Practices](#ros2-best-practices)
4. [Testing](#testing)
   - [Integration Testing](#integration-testing)
5. [Debugging](#debugging)
   - [Common Tools](#common-tools)
   - [Logging](#logging)
6. [Documentation](#documentation)
   - [Code Documentation](#code-documentation)
   - [API Documentation](#api-documentation)
7. [Deployment](#deployment)
   - [Deployment Checklist](#deployment-checklist)
8. [Troubleshooting](#troubleshooting)
   - [Common Issues](#common-issues)

This guide provides comprehensive information for developers working on the Davis Autonomous Race Car project.

## Development Environment Setup

### Prerequisites
- Ubuntu 20.04 LTS
- ROS2 Foxy
- Python 3.8+
- CMake 3.16+
- Git

### Initial Setup
1. **Install ROS2 Foxy**
   ```bash
   # Add ROS2 apt repository
   sudo apt update && sudo apt install curl gnupg2 lsb-release
   curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.key | sudo apt-key add -
   sudo sh -c 'echo "deb [arch=amd64] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" > /etc/apt/sources.list.d/ros2-latest.list'
   
   # Install ROS2 Foxy
   sudo apt update
   sudo apt install ros-foxy-desktop
   ```

2. **Set up the workspace**
   ```bash
   # Create workspace
   mkdir -p ~/f1tenth_ws/src
   cd ~/f1tenth_ws/src
   
   # Clone the repository
   git clone [repository-url]
   
   # Install dependencies
   cd ~/f1tenth_ws
   rosdep install --from-paths src --ignore-src -r -y
   ```

3. **Build the workspace**
   ```bash
   colcon build
   source install/setup.bash
   ```

## Code Organization

### Directory Structure
```
f1tenth_ws/
├── src/
│   ├── darc_f1tenth_system/     # Main ROS2 package
│   ├── particle_filter/         # Localization system
│   ├── bitmask_filtering/       # Perception algorithms
│   └── ...
├── build/                       # Build artifacts
├── install/                     # Installed files
└── log/                         # Build logs
```

### Package Structure
Each ROS2 package follows this structure:
```
package_name/
├── include/                     # Header files
├── src/                         # Source files
├── launch/                      # Launch files
├── config/                      # Configuration files
├── test/                        # Unit tests
├── package.xml                  # Package manifest
└── CMakeLists.txt              # Build configuration
```

## Coding Standards

### C++ Standards
- Follow the [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html)
- Use C++17 features where appropriate
- Document all public interfaces

### Python Standards
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints
- Write docstrings for all functions

### ROS2 Best Practices
- Use ROS2 message types for data exchange
- Implement proper error handling
- Use parameters for configuration
- Follow ROS2 naming conventions

## Testing

### Integration Testing
1. **Launch File Testing**
   ```bash
   # Test launch files
   ros2 launch package_name test_launch.py
   ```

2. **System Testing**
   ```bash
   # Run system tests
   ros2 launch package_name system_test.launch.py
   ```

## Debugging

### Common Tools
1. **ROS2 CLI**
   ```bash
   # List nodes
   ros2 node list
   
   # List topics
   ros2 topic list
   
   # Echo topic data
   ros2 topic echo /topic_name
   ```

2. **RViz2**
   ```bash
   # Launch RViz2
   ros2 run rviz2 rviz2
   ```


### Logging
- Use ROS2 logging macros:
  ```cpp
  RCLCPP_INFO(node->get_logger(), "Message: %s", value);
  RCLCPP_ERROR(node->get_logger(), "Error: %s", error);
  ```


## Documentation

### Code Documentation
- Keep documentation up to date
- Include examples

### API Documentation
- Document all public interfaces
- Include usage examples
- Specify preconditions and postconditions
- Document error conditions

## Deployment

### Deployment Checklist
1. Check documentation
2. Verify performance
3. Test on target hardware
4. Create deployment package

## Troubleshooting

### Common Issues
1. **Build Errors**
   - Check dependencies
   - Verify CMake configuration
   - Check compiler version

2. **Runtime Errors**
   - Check ROS2 node status
   - Verify topic connections
   - Check parameter values

3. **Performance Issues**
   - Profile the system
   - Check resource usage
   - Verify algorithm efficiency 