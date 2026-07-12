cmake_minimum_required(VERSION 3.5)
project(elapsed_time)

# Find required ROS2 packages
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)

# Add the elapsed_time_publisher node executable
add_executable(elapsed_time_publisher src/elapsed_time.cpp)

# Link dependencies
ament_target_dependencies(elapsed_time_publisher rclcpp std_msgs)

# Install targets
install(TARGETS
  elapsed_time_publisher
  DESTINATION lib/${PROJECT_NAME}
)

# Install launch files
install(DIRECTORY launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

# Finalize package
ament_package()
