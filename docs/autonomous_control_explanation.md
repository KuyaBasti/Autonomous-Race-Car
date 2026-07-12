# Autonomous Control System: Pure Pursuit and Gap Following

## READY TO TEST

## TLDR
The autonomous control system uses three main components to drive the car:
1. **Pure Pursuit**: Follows a predefined path using waypoints
2. **Obstacle Detection**: Monitors for obstacles and decides when to switch modes
3. **Gap Following**: Takes over when obstacles are detected to navigate around them

The system switches between Pure Pursuit and Gap Following using the `/use_obs_avoid` topic:
- When an obstacle is detected, it immediately switches to Gap Following
- After the obstacle is cleared, it waits 15 cycles before switching back to Pure Pursuit
- This hysteresis prevents rapid switching and ensures stable operation

Key features:
- Adaptive look-ahead distance based on speed
- Safety bubbles around obstacles
- Emergency braking system
- Velocity scaling for obstacle avoidance
- Configurable parameters for tuning performance

## Overview
The autonomous control system consists of three main components that work together to provide safe and efficient autonomous driving:
1. Pure Pursuit Controller
2. Obstacle Detection System
3. Gap Following Controller

## System Architecture

### 1. Pure Pursuit Controller
The Pure Pursuit controller is responsible for following a predefined path. It uses a look-ahead point to calculate steering angles and maintain the desired trajectory.

#### Key Parameters
```yaml
pure_pursuit:
  ros__parameters:
    pp_steer_L_fast: 2.5    # Look-ahead distance for high speed
    pp_steer_L_slow: 1.8    # Look-ahead distance for low speed
    kp_fast: 0.35           # Proportional gain for high speed
    kp_slow: 0.5            # Proportional gain for low speed
    L_threshold_speed: 4.0  # Speed threshold for switching between fast/slow parameters
```

#### Core Functionality
The Pure Pursuit controller:
- Loads waypoints from a CSV file
- Calculates the closest point on the path to the vehicle
- Determines a look-ahead point based on current speed
- Computes steering angle using the pure pursuit formula:
```python
def calc_steer(self, goal_point_car, kp, L):
    y = goal_point_car[1]
    steer_dir = np.sign(y)
    r = L ** 2 / (2 * np.abs(y))
    gamma = 1 / r
    steering_angle = (gamma * kp * steer_dir)
    return steering_angle
```

### 2. Obstacle Detection System
The Obstacle Detection system is the decision-maker that determines when to switch between Pure Pursuit and Gap Following.

#### Key Parameters
```yaml
obs_detect:
  ros__parameters:
    collision_loop_threshold: 15    # Number of clear cycles before switching back to pure pursuit
    resolution: 0.1                 # Meters per pixel in occupancy grid
    collision_time_buffer: 0.5      # Safety buffer in seconds
```

#### Core Functionality
The Obstacle Detection system:
1. Creates an occupancy grid from LIDAR data
2. Projects the planned path onto the grid
3. Checks for collisions between the path and obstacles
4. Makes the switching decision based on collision detection

The switching logic is implemented as follows:
```cpp
if (use_coll_avoid == true) {
    use_coll_avoid_msg.data = use_coll_avoid;
    collision_detect_counter = 0;
} else {
    collision_detect_counter += 1;
    if (collision_detect_counter < collision_loop_threshold) {
        use_coll_avoid_msg.data = true;
    } else {
        use_coll_avoid_msg.data = false;
    }
}
```

### 3. Gap Following Controller
The Gap Following controller takes over when obstacles are detected, implementing a reactive obstacle avoidance strategy.

#### Key Parameters
```yaml
gap_follow:
  ros__parameters:
    window_size: 3
    max_range_threshold: 10.0
    max_drive_range_threshold: 5.0
    car_width: 0.60
    angle_cutoff: 1.5
    disp_threshold: 0.4
    bubble_dist_threshold: 6.0
    velocity_scaling_factor: 0.5
    minimum_speed: 0.5
```

#### Core Functionality
The Gap Following controller:
1. Processes LIDAR data to find the largest gap
2. Creates a safety bubble around obstacles
3. Calculates the optimal steering angle to navigate through the gap
4. Adjusts speed based on the environment

## Switching Mechanism

### Communication Flow
**The switching mechanism relies on the `/use_obs_avoid` topic, which is a boolean message that controls the mode switching:**

1. **Topic Structure**:
   - Topic name: `/use_obs_avoid`
   - Message type: `std_msgs/Bool`
   - Publishers: Obstacle Detection node
   - Subscribers: Pure Pursuit and Gap Following nodes

2. **Pure Pursuit Response**:
```python
def use_obs_avoid_callback(self, avoid_msg):
    self.use_obs_avoid = avoid_msg.data

# In the main control loop:
if not self.use_obs_avoid:
    msg = AckermannDriveStamped()
    msg.drive.steering_angle = float(steering_angle)
    msg.drive.speed = float(drive_speed)
    self.drive_publisher.publish(msg)
```

3. **Gap Following Response**:
```cpp
void ReactiveFollowGap::gap_callback(const std_msgs::msg::Bool::ConstSharedPtr gap_bool) {
    use_gap = gap_bool->data;
}
```

### Switching Process
1. **Normal Operation**:
   - Obstacle Detection continuously monitors for obstacles
   - Pure Pursuit is active and publishing commands
   - Gap Following is inactive

2. **Obstacle Detection**:
   - When an obstacle is detected, Obstacle Detection publishes `true` to `/use_obs_avoid`
   - This immediately:
     - Stops Pure Pursuit from publishing commands
     - Activates Gap Following to publish commands

3. **Obstacle Clearance**:
   - When the obstacle is cleared, Obstacle Detection starts counting clear cycles
   - **After 15 clear cycles (collision_loop_threshold), it publishes `false` to `/use_obs_avoid`**
   - This causes:
     - Gap Following to stop publishing commands
     - Pure Pursuit to resume publishing commands

### Hysteresis Mechanism
The system implements hysteresis to prevent rapid switching between modes:
- Immediate switch to Gap Following when an obstacle is detected
- Delayed switch back to Pure Pursuit (15 clear cycles)
- This prevents oscillation between modes and ensures stable operation

## Safety Considerations
1. **Emergency Braking**:
   - The system includes an emergency braking component
   - Monitors Time-To-Collision (TTC)
   - Can override both Pure Pursuit and Gap Following if necessary

2. **Velocity Control**:
   - Both controllers implement velocity scaling
   - Speed is reduced in the presence of obstacles
   - Minimum speed is maintained to ensure vehicle stability

3. **Safety Margins**:
   - Gap Following uses a "bubble" approach to create safety margins
   - Obstacle Detection includes a collision time buffer
   - Pure Pursuit adjusts look-ahead distance based on speed

## Configuration and Tuning
The system's behavior can be tuned through various parameters:
1. **Pure Pursuit Tuning**:
   - Adjust look-ahead distances for different speeds
   - Modify proportional gains for steering control
   - Set speed thresholds for parameter switching

2. **Obstacle Detection Tuning**:
   - Modify collision detection sensitivity
   - Adjust the hysteresis threshold
   - Configure grid resolution and size

3. **Gap Following Tuning**:
   - Set safety margins and bubble sizes
   - Configure velocity scaling
   - Adjust angle cutoffs and thresholds

## Best Practices
1. **Parameter Tuning**:
   - Start with conservative values
   - Test in simulation before real-world deployment
   - Gradually increase performance parameters

2. **System Integration**:
   - Ensure proper topic naming and communication
   - Verify message types and formats
   - Test switching behavior in various scenarios

3. **Safety Testing**:
   - Test emergency scenarios
   - Verify obstacle detection reliability
   - Ensure smooth mode transitions 