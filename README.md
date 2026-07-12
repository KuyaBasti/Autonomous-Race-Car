# Autonomous Race Car (F1TENTH)

A ROS 2 autonomy stack for a 1/10-scale autonomous race car, built at UC Davis
(Davis Autonomous Race Car — DARC). The car maps a track with LiDAR SLAM,
localizes with a GPU-accelerated Monte Carlo particle filter, chases an
offline-optimized raceline with pure pursuit, and swerves around obstacles with
a reactive follow-the-gap planner — all onboard an NVIDIA Jetson. A companion
vision pipeline segments the track with language-prompted SAM and trains an
end-to-end driving CNN from camera frames.

## Repository layout

| Dir | Lang | What |
|-----|------|------|
| `darc_f1tenth_system/` | C++ / Python | On-car stack: launch files, VESC + LiDAR drivers, Ackermann mux, teleop, Arduino bridge |
| `particle_filter/` | Python + CUDA | Monte Carlo localization (4000 particles, RangeLibc GPU ray marching) |
| `f1tenth_gym_ros/` | C++ / Python | Racing algorithms (pure pursuit, gap follow, obs detect, emergency braking) + Dockerized simulator |
| `Raceline-Optimization/` | Python | Offline min-curvature / min-time raceline generation from SLAM maps (TUM-based) |
| `bag_extraction/` | Python | Pull images, poses, and drive commands out of rosbag2 SQLite files |
| `automatic_bitmask_stitching/` | Python | Sync camera frames to particle-filter poses; stitch masks onto the SLAM map |
| `bitmask_filtering/` | Python | Mask cleanup library (flood fill, occupancy-map conventions) — unit tested |
| `PerspectiveTransform/` | Python / C++ | Bird's-eye-view homography from RealSense intrinsics + depth |
| `CNN/` | Python | End-to-end steering/speed CNN (behavioral cloning, PilotNet-style) |
| `docs/`, `helper_scripts/`, `tests/` | — | Notes, bringup scripts, sanity checks |

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
