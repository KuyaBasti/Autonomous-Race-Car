# Autonomous Race Car — system design

> How a hallway becomes a race track.
>
> A LiDAR-equipped 1/10-scale car drives the track once under human control
> while **SLAM** builds a map. An **offline optimizer** turns that map into the
> fastest feasible raceline with a per-waypoint speed profile. On race day, a
> **GPU particle filter** tells the car where it is 4000 hypotheses at a time,
> **pure pursuit** chases the raceline, and a **supervisor** watches the road
> ahead — the instant an obstacle blocks the line, a reactive **follow-the-gap**
> planner takes the wheel until the path is clear. A human deadman button sits
> above everything; a time-to-collision node (`emergency_braking`) is built but
> not started by any launch file.

This document is the developer-facing map of the whole system — every major node,
**built or planned**, and how data moves between them. Read the flowchart
top-to-bottom; dashed nodes are the roadmap.

---

## End-to-end flowchart

<p align="center"><img src="docs/system-design-flowchart.svg" alt="Autonomous Race Car (F1TENTH) end-to-end flowchart. Offline, once per track: during teleop laps the Hokuyo LiDAR /scan feeds slam_toolbox; its 0.05 m/px occupancy map goes through map_converter.ipynb and the TUM raceline optimizer (minimum lap time by default) into a raceline CSV of x, y and speed. On the car, the LiDAR /scan feeds particle_filter (4000 particles, CUDA ray marching), obs_detect, gap_follow and emergency_braking; the map reaches particle_filter through nav2 map_server and the same raceline file feeds pure_pursuit and obs_detect. obs_detect publishes /use_obs_avoid so that either pure_pursuit or gap_follow publishes /drive; emergency_braking, which no launch file starts, publishes a speed-0 command on the same /drive topic. In bringup_launch.py, ackermann_mux gives /teleop from joy_teleop priority 100 over /drive priority 10, then ackermann_to_vesc and vesc_driver drive the VESC; vesc_to_odom publishes /odom back to particle_filter and emergency_braking; darc_arduino publishes /arduino with no subscriber. Offline, rosbag2 recordings of camera images, /pf/viz/inferred_pose and drive commands are extracted: imagePoseSync and bitmaskStitcher place LangSAM masks of kept frames on the SLAM map, and imageAckermannSync labels frames with steering and speed to train a PilotNet-style CNN on the masks. PerspectiveTransform is standalone and TinySAM is planned." width="100%"></p>

---

## How to read it: the three flows that matter

1. **Two timescales, one interface.** The offline factory (top right) runs *once
   per track* (drive laps → SLAM map → optimized raceline). The online loop runs
   continuously and only ever sees two artifacts from it: the map (fed to the
   particle filter) and the raceline CSV (fed to pure pursuit *and* obs_detect —
   both YAML configs point at the same file, so the supervisor checks exactly the
   corridor the tracker intends to drive, as long as `trajectory_csv` and
   `spline_file_name` stay in sync).

2. **The supervisor never steers** (the `/use_obs_avoid` edges). `obs_detect`
   only answers one question each scan: *does anything intersect the raceline
   segment the car is about to drive?* On `true`, pure pursuit goes silent and
   gap_follow publishes to the same `/drive` topic — exactly one controller
   speaks at a time. A hysteresis counter keeps avoidance latched for several
   clear cycles so control doesn't chatter mid-corner, and gap_follow inherits
   pure pursuit's profile speed as its ceiling so avoidance never out-runs the
   plan.

3. **Safety is layered, not centralized** (the red nodes). The mux gives the
   human's `/teleop` (priority 100) strictly higher priority than autonomy's
   `/drive` (10), each with a 0.2 s timeout — hold button 4 to drive by hand,
   hold button 5 to silence `/teleop` so `/drive` passes, and release both and
   joy_teleop publishes a zero-speed command that overrides autonomy. A
   time-to-collision node (`emergency_braking`) publishes speed 0 on `/drive`
   when any beam predicts impact within 1 s, but no launch file starts it, and
   when run by hand it shares the planners' priority-10 input rather than
   outranking them. gap_follow's corner check vetoes hard turns when a side wall
   is under 0.5 m away. Nothing autonomous can override a human.

The **TinySAM node** (dashed) is the vision pipeline's north star: it would be
trained on the LangSAM-labeled frames, run on the Jetson, and feed its masks to
the driving CNN in the control loop (`CNN/proposal_pipeline.md`). The
auto-labeled masks and an offline driving CNN already exist; TinySAM itself is
not built yet.

---

## Deep dive 1 — control arbitration

<p align="center"><img src="docs/control-arbitration.svg" alt="Autonomous Race Car control arbitration as a state diagram. Teleop: at bringup no button is held, so joy_teleop's default mapping sends speed 0 and steering 0 on /teleop at 20 Hz and the car holds at zero; holding LB (button 4) switches to the human_control mapping, which commands up to 3.0 m/s and 0.34 rad of steering either way (vesc_driver's servo limits of 0.11 to 0.715 cap the steering actually applied at about +0.24 and -0.26 rad); releasing all buttons returns to zero. Holding only RB (button 5) silences /teleop, and once /teleop is 0.2 s stale the mux forwards /drive: autonomous. From autonomous, releasing all buttons (zero command) or pressing LB (manual command) wins at once because /teleop has priority 100 over /drive at 10. Inside autonomous, obs_detect's /use_obs_avoid flag picks the controller: pure pursuit while false, gap follow while true; one scan with a LiDAR hit on the raceline within v times 0.5 s ahead, where v is the speed in the last /drive message, sets true and resets the counter, and 15 clear scans in a row set false. Concurrently and only if started by hand, emergency_braking sends speed 0 on /drive on every scan where any beam's TTC, r over max(v cos theta, 0.001), is under 1 s; there is no latch and the next pure pursuit or gap follow message replaces it, and in teleop it is outranked. Every command passes through ackermann_mux, which forwards a message only if no higher-priority input arrived in the last 0.2 s, then /ackermann_cmd to ackermann_to_vesc." width="100%"></p>

## Deep dive 2 — one particle filter update

<p align="center"><img src="docs/particle-filter-update.svg" alt="Autonomous Race Car, one particle filter update: at startup the node loads the map into RangeLibc rmgpu, uploads a 4-part beam-model table and spreads 4000 particles, which a later RViz /initialpose can re-seed; then urg_node scans are stored downsampled to every 18th beam, each vesc_to_odom message yields an odometry delta and calls update, which resamples 4000 particles by weight, applies the noisy motion model, has RangeLibc ray march about 60 beams per particle on the GPU and look up each beam in the table by observed and expected range, multiplying into one weight per particle, squashes and normalizes the weights, takes the weighted mean pose, broadcasts the map to laser TF and publishes /pf/pose/odom to pure_pursuit, obs_detect and velocity_calculator." width="100%"></p>

The beam model is a 4-component mixture precomputed into a lookup table at
startup: a Gaussian around the expected range (`z_hit`), a short-reading ramp
for unexpected obstacles (`z_short`), a max-range spike (`z_max`), and uniform
noise (`z_rand`). Weights are softened with `w^(1/2.2)` so a single bad beam
can't kill a good hypothesis.

---

## Component inventory

| Component | Layer | Tech | Status | Where |
|---|---|---|---|---|
| urg_node (Hokuyo driver) | Sensors | C++ | ✅ built | `darc_f1tenth_system/f1tenth_stack/config/sensors.yaml` |
| vesc_driver | Actuation | C++ | ✅ built | `darc_f1tenth_system/vesc/vesc_driver/` |
| ackermann_to_vesc / vesc_to_odom | Actuation | C++ | ✅ built | `darc_f1tenth_system/vesc/vesc_ackermann/` |
| ackermann_mux | Safety | C++ | ✅ built | `darc_f1tenth_system/ackermann_mux/` |
| joy_teleop | Teleop | Python | ✅ built | `darc_f1tenth_system/teleop_tools/` |
| darc_arduino bridge | Sensors | Python | ✅ built | `darc_f1tenth_system/darc_arduino/` |
| slam_toolbox config | Offline factory | — | ✅ built | `darc_f1tenth_system/f1tenth_stack/config/f1tenth_online_async.yaml` |
| Map converter | Offline factory | Python / Jupyter | ✅ built | `Raceline-Optimization/map_converter.ipynb` |
| Raceline optimizer | Offline factory | Python (TUM) | ✅ built | `Raceline-Optimization/main_globaltraj_f110.py` |
| Particle filter (MCL) | Localization | Python (GPU ray marching via external RangeLibc) | ✅ built | `particle_filter/particle_filter/particle_filter.py` |
| Velocity calculator | Localization | Python | ✅ built | `darc_f1tenth_system/darc_tools/` |
| pure_pursuit | Racing brain | Python | ✅ built | `f1tenth_gym_ros/src/pure_pursuit/` |
| obs_detect (supervisor) | Racing brain | C++ / Eigen | ✅ built | `f1tenth_gym_ros/src/obs_detect/` |
| gap_follow | Racing brain | C++ | ✅ built | `f1tenth_gym_ros/src/gap_follow/` |
| emergency_braking | Safety | C++ | ✅ built (not in any launch file) | `f1tenth_gym_ros/src/emergency_braking/` |
| Simulator bridge | Sim | Python / Docker | ✅ built | `f1tenth_gym_ros/src/f1tenth_gym_ros/` |
| Bag extraction | Vision R&D | Python / SQLite | ✅ built | `bag_extraction/` |
| Timestamp sync + frame curation | Vision R&D | Python | ✅ built | `automatic_bitmask_stitching/` |
| LangSAM segmentation | Vision R&D | PyTorch (Colab) | ✅ built | `automatic_bitmask_stitching/LangSAM.ipynb` |
| Bitmask filtering | Vision R&D | Python / OpenCV | ✅ built (smoke test, no assertions) | `bitmask_filtering/` |
| Perspective transform (IPM) | Vision R&D | Python / Open3D | ✅ built | `PerspectiveTransform/` |
| Bitmask stitcher | Vision R&D | Python / OpenCV | ✅ built | `automatic_bitmask_stitching/bitmaskStitcher.py` |
| Driving CNN | Vision R&D | TensorFlow / Keras | ✅ built (offline) | `CNN/cnn_model.py` |
| TinySAM real-time segmentation | Vision R&D | — | ⬜ planned | — *(north star, `CNN/proposal_pipeline.md`)* |
| On-car CNN deployment | Vision R&D | — | ⬜ planned | — |

---

## The numbers that matter

| Value | What it is |
|---|---|
| 4000 | particles in the Monte Carlo localizer |
| 1081 → ~60 | LiDAR beams per scan → beams the sensor model actually ray-casts (18:1 downsample) |
| 0.05 m/px | SLAM map resolution |
| 2.5 m / 1.8 m | pure pursuit lookahead above / below the 4 m/s speed threshold |
| `L = v · t_buffer` | obs_detect corridor length — scales with the commanded speed (last `/drive` message) |
| 1 s | time-to-collision threshold for emergency braking |
| 0.2 s | mux input timeout (stale commands are dropped) |
| 100 vs 10 | mux priority: joystick vs navigation |
| 3900 | motor ERPM per m/s (VESC calibration) |
| −1.2135 / +0.4 | steering-angle → servo gain / offset |
| 0.25 m | wheelbase (odometry + steering geometry) |
| 0.6 m | car width used for gap-follow disparity bubbles |
| 200 × 66 × (1 or 4) | CNN input: bitmask-only or RGB+bitmask |

---

## Race-day workflow

| Stage | Name | What happens | Status |
|---|---|---|---|
| 1 | Mapping | teleop laps + `slam_launch.py` → save `.pgm`/`.yaml` from RViz | ✅ routine |
| 2 | Raceline | clean map boundaries → `map_converter` → TUM optimizer → `traj_race_cl-*.csv`, moved into `f1tenth_stack/racelines/` (on a laptop — CPU heavy) | ✅ routine |
| 3 | Configuration | point `particle_filter.yaml`, `pure_pursuit.yaml`, `obs_detect.yaml` at the new map + raceline; `colcon build` | ✅ routine |
| 4 | Localization | `particle_filter_launch.py` + RViz *2D Pose Estimate* to seed the filter | ✅ routine |
| 5 | Race | `autonomous_launch.py` — supervisor arbitrates pure pursuit vs gap follow | ✅ routine |
| 6 | Data capture | rosbag camera + pose + drive topics for the vision pipeline (the drive-command extractor reads `/ackermann_mux/output`; the mux here publishes `/ackermann_cmd`) | ✅ routine |
| 7 | Camera-driven racing | TinySAM segmentation → CNN in the control loop | ⬜ planned |

---

## Credits & upstream sources

Built on the F1TENTH open-source ecosystem, adapted and integrated for the DARC
car: the [MIT RACECAR particle filter](https://github.com/mit-racecar/particle_filter)
(+ [RangeLibc](https://github.com/f1tenth/range_libc)) ported to ROS 2;
pure pursuit / gap follow / obs detect adapted from
[ladavis4's ICRA 2022 project](https://github.com/ladavis4/F1Tenth_Final_Project_and_ICRA2022);
raceline optimization from
[TUM FTM](https://github.com/TUMFTM/global_racetrajectory_optimization);
emergency braking referenced from
[UWaterloo CL2](https://github.com/CL2-UWaterloo/f1tenth_ws); simulation via
[f1tenth_gym_ros](https://github.com/f1tenth/f1tenth_gym_ros); segmentation via
[lang-segment-anything](https://github.com/luca-medeiros/lang-segment-anything).
