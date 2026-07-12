Useful path:
/home/car1/f1tenth_ws/install/f1tenth_stack/share/f1tenth_stack

bluetooth:
1. connect to car1
2. Open Bluetooth File Exchange
3. transfer file
4. Files are located at /Downlaods


# This is where you should put the generated raceline map 

~/f1tenth_ws/src/darc_f1tenth_system/f1tenth_stack

find a directory called maps and you will put the generated 2D map by SLAM and the YAML in that directory

find a directory called racelines and you will put the generated raceline CSV into that directory


# This is the directory which you have to go to modify the YAML file

~/f1tenth_ws/src/darc_f1tenth_system/f1tenth_stack/config


# You have to run this everytime you change the MAPS and RACELINES; like when you also modify the YAML files of particle_filter, pure_pursuit and obstacle_detection


cd ~/f1tenth_ws
colcon build --packages-select f1tenth_stack particle_filter nav2_map_server
source install/setup.bash



# Nadav's bag commands

## To launch Realsense camera ROS node:
ros2 launch realsense2_camera rs_launch.py

## for visualizing camera stream 
ros2 run rqt_image_view rqt_image_view

## for recording camera stream
ros2 bag record -o camera_sample /camera/color/image_raw

## playing camera recording
ros2 bag play camera_sample --loop

## see message rate of topic
ros2 topic hz /camera/color/image_raw

## see info about bag file
ros2 bag info camera_sample


## Topics for pose
/pf/viz/inferred_pose -> use w for orientation (heading ang.)
/sensor/imu


pure_pursuit:
  ros__parameters:
    trajectory_csv: "/home/car1/f1tenth_ws/src/darc_f1tenth_system/f1tenth_stack/racelines/DARCMAP2_resized1_raceline.csv"
    pp_steer_L_fast: 2.5
    pp_steer_L_slow: 1.8
    kp_fast: 0.35
    kp_slow: 0.5
    L_threshold_speed: 4.0
    odom_topic: "pf/pose/odom"
    pure_pursuit_velocity_topic: "pure_pursuit_velocity"
    drive_topic: "drive"
    use_obs_avoid_topic: "use_obs_avoid"
