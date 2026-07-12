# System Architecture

## Table of Contents
1. [Overview](#overview)
2. [System Components](#system-components)
   - [Localization System](#1-localization-system)
   - [Perception System](#2-perception-system)
   - [Control System](#3-control-system)
   - [Planning System](#4-planning-system)
3. [Communication Architecture](#communication-architecture)
   - [ROS2 Topics](#ros2-topics)
   - [Node Communication](#node-communication)
4. [Data Flow](#data-flow)
5. [Configuration Management](#configuration-management)
6. [Error Handling](#error-handling)
7. [Performance Considerations](#performance-considerations)

## Overview

The Davis Autonomous Race Car system is built on ROS2 and consists of several interconnected components that work together to enable autonomous racing capabilities. This document provides a detailed explanation of the system's architecture and how its components interact.

## System Components

### 1. Localization System
The localization system uses a particle filter to estimate the car's position and orientation on the track.

#### Key Components:
- **Particle Filter Node**
  - Maintains a set of particles representing possible car poses
  - Updates particle weights based on sensor measurements
  - Resamples particles to maintain diversity
  - Publishes estimated pose on `/particle_filter/pose`

#### Inputs:
- LiDAR scan data (`/scan`)
- Map data (YAML + PNG)
- Initial pose estimate

#### Outputs:
- Estimated pose (`/particle_filter/pose`)
- Particle cloud visualization

### 2. Perception System
The perception system processes sensor data to understand the environment and detect obstacles.

#### Key Components:
- **Bitmask Filtering**
  - Processes LiDAR data to create binary masks
  - Filters out noise and irrelevant data
  - Identifies track boundaries and obstacles

- **Map Processing**
  - Handles map loading and processing
  - Provides map data to other components
  - Supports map updates and modifications

#### Inputs:
- Raw LiDAR data
- Camera data (if available)
- Map data

#### Outputs:
- Processed environment data
- Obstacle detection results
- Track boundary information

### 3. Control System
The control system manages the car's movement and implements the racing strategy.

#### Key Components:
- **Pure Pursuit Controller**
  - Follows the precomputed racing line
  - Calculates steering angles and velocities
  - Implements obstacle avoidance

- **Velocity Controller**
  - Manages speed based on track conditions
  - Implements acceleration and braking
  - Ensures smooth motion

#### Inputs:
- Current pose
- Racing line data
- Obstacle information
- Track conditions

#### Outputs:
- Steering commands
- Velocity commands
- Control status

### 4. Planning System
The planning system generates optimal racing lines and trajectories.

#### Key Components:
- **Raceline Optimizer**
  - Computes optimal racing lines
  - Considers track constraints
  - Optimizes for speed and safety

- **Trajectory Generator**
  - Creates smooth trajectories
  - Handles dynamic replanning
  - Manages multiple waypoints

#### Inputs:
- Track map
- Car capabilities
- Racing objectives

#### Outputs:
- Optimized racing line
- Trajectory waypoints
- Planning status

## Communication Architecture

### ROS2 Topics
Key topics used for inter-component communication:

1. **Sensor Data**
   - `/scan`: LiDAR data
   - `/camera/image_raw`: Camera data (if available)
   - `/vesc/odom`: Odometry data

2. **Control Commands**
   - `/cmd_vel`: Velocity commands
   - `/vesc/commands`: Motor commands
   - `/steering`: Steering commands

3. **System Status**
   - `/particle_filter/pose`: Localization data
   - `/obstacle_detection/status`: Obstacle information
   - `/planning/status`: Planning status

### Node Communication
The system uses a combination of:
- Topic-based communication for streaming data
- Services for request-response operations
- Parameters for configuration
- Actions for long-running tasks

## Data Flow

1. **Sensor Data Flow**
   ```
   Sensors → Raw Data → Processing → Filtered Data → Perception
   ```

2. **Localization Flow**
   ```
   Filtered Data + Map → Particle Filter → Pose Estimate → Control
   ```

3. **Control Flow**
   ```
   Pose + Racing Line → Pure Pursuit → Commands → Motors
   ```

4. **Planning Flow**
   ```
   Map + Objectives → Optimization → Racing Line → Control
   ```

## Configuration Management

The system uses YAML configuration files for:
- Node parameters
- Algorithm settings
- Hardware configurations
- Map data

Configuration files are located in:
- `config/`: Main configuration files
- `maps/`: Map data
- `launch/`: Launch file configurations

## Error Handling

The system implements several error handling mechanisms:
- Sensor data validation
- Node health monitoring
- Recovery behaviors
- Fallback strategies

## Performance Considerations

Key performance aspects:
- Real-time processing requirements
- Computational resource management
- Memory usage optimization
- Communication latency minimization 