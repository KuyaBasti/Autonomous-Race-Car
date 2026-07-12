# Particle Filter Documentation

## Table of Contents
1. [Overview](#overview)
2. [Algorithm Details](#algorithm-details)
   - [Particle Representation](#1-particle-representation)
   - [Initialization](#2-initialization)
   - [Prediction Step](#3-prediction-step)
   - [Update Step](#4-update-step)
   - [Resampling](#5-resampling)
3. [ROS2 Integration](#ros2-integration)
   - [Node Structure](#node-structure)
   - [Topics](#topics)
   - [Parameters](#parameters)
4. [Usage](#usage)
   - [Launching the Node](#launching-the-node)
   - [Setting Initial Pose](#setting-initial-pose)
   - [Monitoring](#monitoring)
5. [Performance Considerations](#performance-considerations)
   - [Computational Complexity](#computational-complexity)
   - [Optimization Tips](#optimization-tips)
6. [Troubleshooting](#troubleshooting)
   - [Common Issues](#common-issues)
   - [Debugging Tools](#debugging-tools)

## Overview

The particle filter is a probabilistic localization algorithm that estimates the car's position and orientation on the track. It uses a set of particles (possible poses) and updates their weights based on sensor measurements to track the car's state.

## Algorithm Details

### 1. Particle Representation
Each particle represents a possible pose of the car:
```cpp
struct Particle {
    double x;        // x position
    double y;        // y position
    double theta;    // orientation
    double weight;   // particle weight
};
```

### 2. Initialization
- Particles are initialized uniformly across the track
- Initial weights are set to 1/N (N = number of particles)
- Configuration parameters:
  ```yaml
  particle_filter:
    num_particles: 1000
    init_std_dev_x: 0.5
    init_std_dev_y: 0.5
    init_std_dev_theta: 0.1
  ```

### 3. Prediction Step
The prediction step updates particle positions based on motion:
```cpp
void predict(const Odometry& odom) {
    for (auto& particle : particles_) {
        // Update position using motion model
        particle.x += odom.dx * cos(particle.theta) - odom.dy * sin(particle.theta);
        particle.y += odom.dx * sin(particle.theta) + odom.dy * cos(particle.theta);
        particle.theta += odom.dtheta;
    }
}
```

### 4. Update Step
The update step adjusts particle weights based on sensor measurements:
```cpp
void update(const LaserScan& scan) {
    for (auto& particle : particles_) {
        // Calculate likelihood of measurement
        double likelihood = calculateLikelihood(scan, particle);
        particle.weight *= likelihood;
    }
    normalizeWeights();
}
```

### 5. Resampling
Resampling is performed to prevent particle degeneracy:
```cpp
void resample() {
    std::vector<Particle> new_particles;
    double max_weight = getMaxWeight();
    
    // Systematic resampling
    double step = 1.0 / num_particles_;
    double position = randomUniform(0, step);
    
    for (int i = 0; i < num_particles_; ++i) {
        while (cumulativeWeight() < position) {
            current_particle_++;
        }
        new_particles.push_back(particles_[current_particle_]);
        position += step;
    }
    
    particles_ = new_particles;
}
```

## ROS2 Integration

### Node Structure
```cpp
class ParticleFilterNode : public rclcpp::Node {
public:
    ParticleFilterNode() : Node("particle_filter") {
        // Initialize subscribers
        scan_sub_ = create_subscription<sensor_msgs::msg::LaserScan>(
            "/scan", 10,
            std::bind(&ParticleFilterNode::scanCallback, this, std::placeholders::_1));
            
        odom_sub_ = create_subscription<nav_msgs::msg::Odometry>(
            "/vesc/odom", 10,
            std::bind(&ParticleFilterNode::odomCallback, this, std::placeholders::_1));
            
        // Initialize publishers
        pose_pub_ = create_publisher<geometry_msgs::msg::PoseStamped>(
            "/particle_filter/pose", 10);
            
        particles_pub_ = create_publisher<geometry_msgs::msg::PoseArray>(
            "/particle_filter/particles", 10);
    }
    
private:
    // Callback functions
    void scanCallback(const sensor_msgs::msg::LaserScan::SharedPtr scan);
    void odomCallback(const nav_msgs::msg::Odometry::SharedPtr odom);
    
    // Publishers and subscribers
    rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr scan_sub_;
    rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub_;
    rclcpp::Publisher<geometry_msgs::msg::PoseStamped>::SharedPtr pose_pub_;
    rclcpp::Publisher<geometry_msgs::msg::PoseArray>::SharedPtr particles_pub_;
};
```

### Topics

#### Subscribed Topics
- `/scan`: LiDAR scan data
- `/vesc/odom`: Odometry data

#### Published Topics
- `/particle_filter/pose`: Estimated pose
- `/particle_filter/particles`: Particle cloud visualization

### Parameters
```yaml
particle_filter:
  # Particle filter parameters
  num_particles: 1000
  resample_threshold: 0.5
  
  # Motion model parameters
  motion_std_dev_x: 0.1
  motion_std_dev_y: 0.1
  motion_std_dev_theta: 0.05
  
  # Measurement model parameters
  measurement_std_dev: 0.1
  max_range: 10.0
  min_range: 0.1
```

## Usage

### Launching the Node
```bash
ros2 launch particle_filter particle_filter.launch.py
```

### Setting Initial Pose
1. Launch RViz2:
   ```bash
   ros2 run rviz2 rviz2
   ```
2. Click "2D Pose Estimate" in the toolbar
3. Click and drag on the map to set the initial pose

### Monitoring
1. View estimated pose:
   ```bash
   ros2 topic echo /particle_filter/pose
   ```
2. Visualize particles in RViz2:
   - Add PoseArray display
   - Set topic to `/particle_filter/particles`

## Performance Considerations

### Computational Complexity
- Time complexity: O(N * M)
  - N = number of particles
  - M = number of laser scan points
- Space complexity: O(N)

### Optimization Tips
1. **Particle Count**
   - Adjust based on available computational resources
   - Typical range: 500-2000 particles
   - More particles = better accuracy but slower performance

2. **Resampling Strategy**
   - Use systematic resampling for better performance
   - Adjust resampling threshold based on needs
   - Consider adaptive resampling

3. **Measurement Model**
   - Use efficient ray casting
   - Consider downsampling laser scan
   - Cache map lookups

## Troubleshooting

### Common Issues

1. **Particle Depletion**
   - Symptoms: All particles have very low weights
   - Solutions:
     - Increase number of particles
     - Adjust measurement model parameters
     - Check sensor calibration

2. **Localization Drift**
   - Symptoms: Estimated pose gradually diverges
   - Solutions:
     - Improve motion model
     - Adjust process noise parameters
     - Check odometry calibration

3. **Poor Convergence**
   - Symptoms: Particles spread out or don't converge
   - Solutions:
     - Adjust initial distribution
     - Improve measurement model
     - Check map accuracy

### Debugging Tools
1. **Visualization**
   ```bash
   # View particle cloud
   ros2 topic echo /particle_filter/particles
   
   # Plot particle weights
   ros2 topic echo /particle_filter/weights
   ```

2. **Parameter Tuning**
   ```bash
   # List parameters
   ros2 param list /particle_filter
   
   # Get parameter value
   ros2 param get /particle_filter num_particles
   ```
