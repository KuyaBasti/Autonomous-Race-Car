import open3d as o3d
import numpy as np
import json

# ============================
# 🧾 User Configuration
# ============================

CONFIG_PATH = "./PerspectiveTransform/src/config/cam_config.json"           # path to JSON config file
PLY_PATH = "./PerspectiveTransform/src/config/track1.ply"           # path to .ply file
CAMERA_HEIGHT_CM = 26.67                   # known camera height (cm)
YAW_DEG = 0.0                              
ROLL_DEG = 0.0                              
GROUND_NORMAL = np.array([0, 1, 0])        # flat ground (upward Y)

# ============================
# 📦 Utility Functions
# ============================

# Read in the configuration file provided by the realSense SDK
# Returns intrinsic matrix, K 
def get_intrinsic_matrix_from_config(config_path):
    with open(config_path, 'r') as f:
        config = json.load(f)

    fx = float(config["rectified.0.fx"])
    fy = float(config["rectified.0.fy"])
    cx = float(config["rectified.0.ppx"])
    cy = float(config["rectified.0.ppy"])

    K = np.array([
        [fx, 0, cx],
        [0, fy, cy],
        [0,  0,  1]
    ])
    return K

# Reads the values from the cloud point image (.PLY) and compute the pitch of the camera using the depth value and camera height
# Returns: pitch angle in degree (Works correctly)
def estimate_pitch_from_ply(ply_path, camera_height_cm):
    camera_height_m = camera_height_cm / 100.0
    pcd = o3d.io.read_point_cloud(ply_path)
    if pcd.is_empty():
        raise ValueError("The point cloud is empty.")

    plane_model, inliers = pcd.segment_plane(distance_threshold=0.02,
                                             ransac_n=3,
                                             num_iterations=1000)
    a, b, c, d = plane_model
    normal = np.array([a, b, c])
    normal /= np.linalg.norm(normal)

    camera_up = np.array([0, -1, 0])  # OpenCV convention
    dot_product = np.dot(normal, camera_up)
    pitch_rad = np.arccos(np.clip(dot_product, -1.0, 1.0))
    pitch_deg = np.rad2deg(pitch_rad)
    if normal[2] < 0:
        pitch_deg *= -1
    return pitch_deg, plane_model

# ============================
# 🚀 Main Homography Function
# ============================

# Computes homography given the K, orientation of camera(pitch, yall, roll), and height of the camera
# Returns 3X3 homography matrix, H
def compute_homography():
    K = get_intrinsic_matrix_from_config(CONFIG_PATH)
    pitch_deg, _ = estimate_pitch_from_ply(PLY_PATH, CAMERA_HEIGHT_CM)

    camera_height_m = CAMERA_HEIGHT_CM / 100.0
    pitch = np.deg2rad(pitch_deg)
    yaw = np.deg2rad(YAW_DEG)
    roll = np.deg2rad(ROLL_DEG)

    Rx = np.array([
        [1, 0, 0],
        [0, np.cos(pitch), -np.sin(pitch)],
        [0, np.sin(pitch),  np.cos(pitch)]
    ])
    Ry = np.array([
        [np.cos(yaw), 0, np.sin(yaw)],
        [0, 1, 0],
        [-np.sin(yaw), 0, np.cos(yaw)]
    ])
    Rz = np.array([
        [np.cos(roll), -np.sin(roll), 0],
        [np.sin(roll),  np.cos(roll), 0],
        [0, 0, 1]
    ])

    #R = Rz @ Ry @ Rx
    R = Rx @ Ry @ Rz
    T = np.array([[0], [camera_height_m], [0]])
    n = GROUND_NORMAL.reshape(3, 1)
    d = camera_height_m

    H_matrix = R - (T @ n.T) / d
    H = K @ H_matrix @ np.linalg.inv(K)
    return H

# Example usage
if __name__ == "__main__":
    H = compute_homography()
    K = get_intrinsic_matrix_from_config(CONFIG_PATH)
    print("Computed Intrinsic Matrix:\n", K)
    print("Computed Homography Matrix:\n", H)
