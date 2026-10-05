# Autonomous Race Car (F1TENTH)

<p align="center"><img src="docs/system-overview.svg" alt="Autonomous Race Car (F1TENTH) system overview. Once per track, slam_toolbox maps the track on the car from Hokuyo LiDAR scans during teleop laps. A TUM optimizer in min-lap-time mode then runs on a laptop and turns the map into a raceline CSV of x, y and speed. On the NVIDIA Jetson under ROS 2 Foxy, particle_filter (4000 particles, CUDA) localizes against the 0.05 m/px map. It uses /scan plus wheel odometry from vesc_to_odom on /odom, and each /odom message triggers an update. It publishes /pf/pose/odom to the racing brain. Inside the racing brain, obs_detect (the supervisor) checks the raceline ahead and sets /use_obs_avoid, which decides whether pure_pursuit or gap_follow publishes on the shared /drive topic. ackermann_mux lets the gamepad's /teleop input (priority 100) override /drive (priority 10), with a 0.2 s input timeout, and sends /ackermann_cmd to the VESC, which drives the motor and steering servo. Holding gamepad button 4 gives manual control and holding button 5 enables autonomy; with no button held, /teleop sends speed 0. emergency_braking would publish speed 0 on the same /drive topic when any LiDAR beam's time to collision falls below 1 s, but no launch file starts it. Offline, rosbag2 recordings of the RealSense camera, the particle-filter pose and drive commands feed a LangSAM mask and driving-CNN pipeline." width="100%"></p>

A ROS 2 autonomy stack for a 1/10-scale autonomous race car, built at UC Davis
(Davis Autonomous Race Car — DARC). The car maps a track with LiDAR SLAM,
localizes with a GPU-accelerated Monte Carlo particle filter, chases an
offline-optimized raceline with pure pursuit, and swerves around obstacles with
a reactive follow-the-gap planner — all onboard an NVIDIA Jetson. A companion
vision pipeline segments the track with language-prompted SAM and, offline,
trains an end-to-end driving CNN on those track masks (optionally plus the
camera frame).

## Repository layout

| Dir | Lang | What |
|-----|------|------|
| `darc_f1tenth_system/` | C++ / Python | On-car stack: launch files, VESC driver, LiDAR (urg_node) config, Ackermann mux, teleop, Arduino bridge |
| `particle_filter/` | Python + CUDA | Monte Carlo localization (4000 particles, RangeLibc GPU ray marching) |
| `f1tenth_gym_ros/` | C++ / Python | Racing algorithms (pure pursuit, gap follow, obs detect, emergency braking) + Dockerized simulator |
| `Raceline-Optimization/` | Python | Offline min-curvature / min-time raceline generation from SLAM maps (TUM-based) |
| `bag_extraction/` | Python | Pull images and particle-filter poses out of rosbag2 SQLite files (the drive-command extractor expects `/ackermann_mux/output`) |
| `automatic_bitmask_stitching/` | Python | Sync camera frames to particle-filter poses; stitch masks onto the SLAM map |
| `bitmask_filtering/` | Python | Mask cleanup library (flood fill, occupancy-map conventions) — unit tested |
| `PerspectiveTransform/` | Python / C++ | Bird's-eye-view homography from RealSense intrinsics + depth |
| `CNN/` | Python | End-to-end steering/speed CNN (behavioral cloning, PilotNet-style) |
| `docs/`, `helper_scripts/`, `tests/` | — | Notes, bringup scripts, sanity checks |
| `docs/system-overview.svg` | SVG | System overview diagram at the top of this README |
| `docs/system-design-flowchart.svg` | SVG | End-to-end flowchart in SYSTEM-DESIGN.md |
| `docs/control-arbitration.svg` | SVG | Gamepad / mux / controller arbitration diagram in SYSTEM-DESIGN.md |
| `docs/particle-filter-update.svg` | SVG | One particle filter update, step by step, in SYSTEM-DESIGN.md |

## Quickstart

**On the car** (Jetson, ROS 2 Foxy):

```bash
ros2 launch f1tenth_stack bringup_launch.py          # drivers: LiDAR, VESC, mux, teleop
ros2 launch f1tenth_stack particle_filter_launch.py  # map server + MCL + RViz (set 2D Pose Estimate)
ros2 launch f1tenth_stack autonomous_launch.py       # pure pursuit + obs detect + gap follow
```

**In simulation** (Docker, no hardware needed):

```bash
cd f1tenth_gym_ros
docker compose up        # RViz in the browser at localhost:8080/vnc.html
./run_tests.sh           # GoogleTest + pytest suites
```

> Full architecture — every node, topic, and algorithm, with end-to-end
> flowcharts: **[SYSTEM-DESIGN.md](SYSTEM-DESIGN.md)**
