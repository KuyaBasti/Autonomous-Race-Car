# Visualizing Tracks in RViz

## READY TO TEST

This guide provides a comprehensive overview of how to visualize tracks, trajectories, and autonomous vehicle data in RViz for the F1Tenth race car system.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Basic Setup](#basic-setup)
3. [Display Configuration](#display-configuration)
4. [Track Visualization Components](#track-visualization-components)
5. [Advanced Visualization](#advanced-visualization)
6. [Troubleshooting](#troubleshooting)
7. [Track and Trajectory Overlay Visualization](#track-and-trajectory-overlay-visualization)
8. [Visualizing Your Specific Track](#visualizing-your-specific-track)
9. [Common Visualization States](#common-visualization-states)
10. [Tips for Clear Visualization](#tips-for-clear-visualization)

## Prerequisites

Before starting, ensure you have:
- ROS 2 installed and configured
- F1Tenth workspace built
- Track CSV file ready (generated from Raceline-Optimization)

## Basic Setup

### 1. Create RViz Configuration File
Create a new file named `track_visualization.rviz` in your project's `rviz` directory:

```bash
# Create the rviz directory if it doesn't exist
mkdir -p DavisAutonomousRaceCar/rviz

# Create the configuration file
touch DavisAutonomousRaceCar/rviz/track_visualization.rviz
```

### 2. Configure RViz Display
Copy the following configuration into your `track_visualization.rviz` file:

```yaml
Panels:
  - Class: rviz_common/Displays
    Help Height: 78
    Name: Displays
    Property Tree Widget:
      Expanded:
        - /Global Options1
        - /Status1
        - /Map1
        - /Pose1
        - /LaserScan1
      Splitter Ratio: 0.5
    Tree Height: 617
  - Class: rviz_common/Selection
    Name: Selection
  - Class: rviz_common/Tool Properties
    Expanded:
      - /2D Goal Pose1
      - /Publish Point1
    Name: Tool Properties
    Splitter Ratio: 0.5886790156364441
  - Class: rviz_common/Views
    Expanded:
      - /Current View1
    Name: Views
    Splitter Ratio: 0.5
Visualization Manager:
  Class: ""
  Displays:
    - Alpha: 0.7
      Class: rviz_default_plugins/Map
      Color Scheme: map
      Draw Behind: false
      Enabled: true
      Name: Map
      Topic:
        Depth: 5
        Durability Policy: Volatile
        History Policy: Keep Last
        Reliability Policy: Reliable
        Value: /map
      Update Topic:
        Depth: 5
        Durability Policy: Volatile
        History Policy: Keep Last
        Reliability Policy: Reliable
        Value: /map_updates
      Use Timestamp: false
      Value: true
    - Alpha: 1
      Axes Length: 1
      Axes Radius: 0.1
      Class: rviz_default_plugins/Pose
      Color: 255; 25; 0
      Enabled: true
      Head Length: 0.3
      Head Radius: 0.1
      Name: Pose
      Shaft Length: 1
      Shaft Radius: 0.05
      Shape: Arrow
      Topic:
        Depth: 5
        Durability Policy: Volatile
        History Policy: Keep Last
        Reliability Policy: Reliable
        Value: /pf/viz/inferred_pose
      Unreliable: false
      Value: true
    - Alpha: 1
      Autocompute Intensity Bounds: true
      Autocompute Value Bounds:
        Max Value: 10
        Min Value: -10
        Value: true
      Axis: Z
      Channel Name: intensity
      Class: rviz_default_plugins/LaserScan
      Color: 255; 255; 255
      Color Transformer: Intensity
      Decay Time: 0
      Enabled: true
      Invert Rainbow: false
      Max Color: 0; 76; 255
      Max Intensity: 4096
      Min Color: 0; 0; 0
      Min Intensity: 0
      Name: LaserScan
      Position Transformer: XYZ
      Queue Size: 10
      Selectable: true
      Size (Pixels): 3
      Size (m): 0.2
      Style: Squares
      Topic:
        Depth: 5
        Durability Policy: Volatile
        History Policy: Keep Last
        Reliability Policy: Reliable
        Value: /scan
      Unreliable: false
      Use Fixed Frame: true
      Use rainbow: true
      Value: true
  Enabled: true
  Global Options:
    Background Color: 48; 48; 48
    Fixed Frame: map
    Frame Rate: 30
  Name: root
  Tools:
    - Class: rviz_default_plugins/Interact
      Hide Inactive Objects: true
    - Class: rviz_default_plugins/MoveCamera
    - Class: rviz_default_plugins/Select
    - Class: rviz_default_plugins/FocusCamera
    - Class: rviz_default_plugins/Measure
      Line color: 128; 128; 0
    - Class: rviz_default_plugins/SetInitialPose
      Topic:
        Depth: 5
        Durability Policy: Volatile
        History Policy: Keep Last
        Reliability Policy: Reliable
        Value: /initialpose
    - Class: rviz_default_plugins/SetGoal
      Topic:
        Depth: 5
        Durability Policy: Volatile
        History Policy: Keep Last
        Reliability Policy: Reliable
        Value: /goal_pose
    - Class: rviz_default_plugins/PublishPoint
      Single click: true
      Topic:
        Depth: 5
        Durability Policy: Volatile
        History Policy: Keep Last
        Reliability Policy: Reliable
        Value: /clicked_point
  Transformation:
    Current:
      Class: rviz_default_plugins/TF
  Value: true
  Views:
    Current:
      Class: rviz_default_plugins/Orbit
      Distance: 10
      Enable Stereo Rendering:
        Stereo Eye Separation: 0.06
        Stereo Focal Distance: 1
        Swap Stereo Eyes: false
        Value: false
      Focal Point:
        X: 0
        Y: 0
        Z: 0
      Focal Shape Fixed Size: true
      Focal Shape Size: 0.05
      Invert Z Axis: false
      Name: Current View
      Near Clip Distance: 0.01
      Pitch: 0.785398
      Target Frame: <Fixed Frame>
      Value: Orbit (rviz)
      Yaw: 0.785398
    Saved: ~
```

### 3. Launch RViz with Configuration
Launch RViz using your configuration file:

```bash
ros2 run rviz2 rviz2 -d DavisAutonomousRaceCar/rviz/track_visualization.rviz
```

### 4. Verify Displays
After launching RViz, you should see:
1. The Map display showing your track
2. The Pose display showing the car's position
3. The LaserScan display showing LiDAR data

If any display is missing:
1. Click the "Add" button in the Displays panel
2. Select the display type (Map, Pose, or LaserScan)
3. Configure the Topic and other settings as shown in the configuration above

## Display Configuration

### 1. Map Display
Add a Map display to show the track:
```yaml
Display Type: Map
Topic: /map
Fixed Frame: map
Color Scheme: map
Alpha: 0.7
```

### 2. Pose Display
Add a Pose display to show vehicle position:
```yaml
Display Type: Pose
Topic: /pf/viz/inferred_pose
Fixed Frame: map
Color: 255; 25; 0
Shape: Arrow
```

### 3. LaserScan Display
Add a LaserScan display for LiDAR data:
```yaml
Display Type: LaserScan
Topic: /scan
Fixed Frame: map
Style: Squares
Size (m): 0.2
Color Transformer: Intensity
```

## Track Visualization Components

### 1. Track Map
The track map is displayed through the Map display:
- Shows track boundaries
- Displays occupancy grid
- Updates in real-time

### 2. Trajectory Visualization
The pure pursuit controller visualizes the planned path:
```python
# From pure_pursuit.py
self.pp_waypoints, self.drive_velocity = load_from_csv(traj_csv)
self.pp_x_spline = self.pp_waypoints[:, 0]
self.pp_y_spline = self.pp_waypoints[:, 1]
```

### 3. Obstacle Detection Visualization
The obstacle detection system provides two visualization layers:
```cpp
// From obs_detect.cpp
grid_pub = this->create_publisher<nav_msgs::msg::OccupancyGrid>(coll_grid_topic, 1);
path_pub = this->create_publisher<nav_msgs::msg::OccupancyGrid>(coll_path_topic, 1);
```

## Advanced Visualization

### 1. Particle Filter Visualization
Add a PoseArray display to see particle distribution:
```yaml
Display Type: PoseArray
Topic: /pf/viz/particles
Fixed Frame: map
Color: 255; 25; 0
Shape: Arrow (Flat)
```

### 2. Waypoint Markers
Add a Marker display for waypoints:
```yaml
Display Type: Marker
Topic: /visualization_marker_array
Fixed Frame: map
```

### 3. Custom Markers
Create custom markers for debugging:
```python
marker = Marker()
marker.header.frame_id = "map"
marker.type = Marker.POINTS
marker.action = Marker.ADD
marker.scale.x = 0.1
marker.scale.y = 0.1
marker.color.r = 1.0
marker.color.a = 1.0
```

## Troubleshooting

### Common Issues

1. **No Map Display**
   - Check if map server is running
   - Verify map topic is publishing
   - Ensure fixed frame is set correctly

2. **Misaligned Visualizations**
   - Verify TF tree is correct
   - Check frame_id in messages
   - Ensure all displays use same fixed frame

3. **Missing Trajectory**
   - Verify trajectory CSV is loaded
   - Check pure pursuit node is running
   - Ensure waypoints are being published

### Debugging Tips

1. **Check Topics**
```bash
ros2 topic list
ros2 topic echo /map
ros2 topic echo /pf/viz/inferred_pose
```

2. **Verify TF Tree**
```bash
ros2 run tf2_tools view_frames
```

3. **Monitor Node Status**
```bash
ros2 node list
ros2 node info /pure_pursuit_node
```

## Best Practices

1. **Configuration Management**
   - Save RViz configurations for different use cases
   - Use launch files to load specific configurations
   - Document custom display settings

2. **Performance Optimization**
   - Adjust update rates for heavy visualizations
   - Use appropriate QoS settings
   - Limit history size for real-time performance

3. **Visualization Organization**
   - Group related displays
   - Use consistent color schemes
   - Enable/disable displays as needed

## Additional Resources

- [RViz Documentation](http://wiki.ros.org/rviz)
- [ROS 2 Visualization Tools](https://docs.ros.org/en/rolling/Concepts/Basic/About-ROS-2.html)
- [F1Tenth Documentation](https://f1tenth.org/)

## Track and Trajectory Overlay Visualization

When properly configured, you will see three main layers in RViz:

1. **Global Map Layer** (Base Layer)
   - Shows the complete track layout
   - Displays track boundaries and obstacles
   - Provides the reference frame for all other visualizations
   ```yaml
   Display Type: Map
   Topic: /map
   Fixed Frame: map
   ```

2. **Trajectory Layer** (Middle Layer)
   - Shows the planned racing line
   - Displays waypoints from your CSV file
   - Updates in real-time as the car moves
   ```yaml
   Display Type: Marker
   Topic: /visualization_marker_array
   Fixed Frame: map
   Color: 0; 255; 0  # Green for visibility
   ```

3. **Vehicle Layer** (Top Layer)
   - Shows the car's current position and orientation
   - Displays the LiDAR scan data
   - Updates the planned path in real-time
   ```yaml
   Display Type: Pose
   Topic: /pf/viz/inferred_pose
   Fixed Frame: map
   ```

### Visualizing Your Specific Track

To see your track and trajectory:

1. **Load the Track**:
   ```bash
   # Make sure your track CSV is in the correct location
   # Default location: /sim_ws/src/f1tenth_gym_ros/racelines/your_track.csv
   ```

2. **Launch the System**:
   ```bash
   # Launch the complete system
   ros2 launch f1tenth_gym_ros gym_bridge.launch.py
   ```

3. **Verify Visualization**:
   - You should see the track boundaries on the map
   - The racing line (trajectory) should be overlaid on the track
   - The car's position should be shown with an arrow
   - LiDAR data should be visible around the car

### Common Visualization States

1. **Normal Operation**:
   - Track boundaries visible
   - Green line showing planned trajectory
   - Red arrow showing car position
   - Blue dots showing LiDAR points

2. **Obstacle Detection**:
   - Red areas showing detected obstacles
   - Modified trajectory showing avoidance path
   - Safety bubble around the car

3. **Particle Filter** (if enabled):
   - Multiple arrows showing particle distribution
   - Helps verify localization accuracy

### Tips for Clear Visualization

1. **Adjust Display Order**:
   - Map should be at the bottom
   - Trajectory in the middle
   - Vehicle and LiDAR on top

2. **Color Settings**:
   ```yaml
   Map: Default colors
   Trajectory: Green (0; 255; 0)
   Vehicle: Red (255; 25; 0)
   LiDAR: Blue to Red gradient
   ```

3. **Alpha Values**:
   - Map: 0.7 (semi-transparent)
   - Trajectory: 1.0 (fully opaque)
   - LiDAR: 0.8 (slightly transparent)

## Conclusion

Proper visualization of the track and vehicle data is crucial for development and debugging. This guide provides the essential steps and configurations needed to effectively visualize the F1Tenth race car system in RViz. Remember to save your configurations and document any custom settings for future reference. 