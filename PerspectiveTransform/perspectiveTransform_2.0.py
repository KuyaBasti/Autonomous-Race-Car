import open3d as o3d
import numpy as np
import json
import cv2
import os

# ============================
# 🧾 User Configuration
# ============================

CONFIG_PATH = "./PerspectiveTransform/src/config/cam_config.json"           # path to JSON config file
PLY_PATH = "./PerspectiveTransform/src/config/track1.ply"           # path to .ply file
IMAGE_PATH = "./PerspectiveTransform/src/images/track1_Color.png"              # Image to transform
CAMERA_HEIGHT_CM = 26.67                  # Known camera height (cm)
YAW_DEG = 0.0                              
ROLL_DEG = 0.0                              
GROUND_NORMAL = np.array([0, -1, 0])        # Flat ground 
OUTPUT_SIZE = (1000, 1000)                 # Output bird's-eye image size

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

    # Pitch = arcsin(z tilt)
    pitch_rad = np.arcsin(normal[2])
    pitch_deg = -np.rad2deg(pitch_rad)

    return pitch_deg, plane_model

# Computes homography given the K, orientation of camera(pitch, yall, roll), and height of the camera
# Returns 3X3 homography matrix, H
# Refer to rotational matrix in ReadMe.md
def compute_homography(K, pitch_deg, camera_height_m, yaw_deg, roll_deg, ground_normal):
    pitch = np.deg2rad(pitch_deg)
    yaw = np.deg2rad(yaw_deg)
    roll = np.deg2rad(roll_deg)

    #Computing the Rotation Matrix about x-axis (first column)
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

    # Compute the full rotational matrix (since yall and roll are 0, Ry and Rz should not matter)
    R = Rz @ Ry @ Rx
    
    # Transitional vector
    T = np.array([[0], [camera_height_m], [0]])
    n = ground_normal.reshape(3, 1)
    d = camera_height_m

    # Compute the homography matrix
    H_matrix = R - (T @ n.T) / d 
    H = K @ H_matrix @ np.linalg.inv(K)
    
    return H

# ============================
# 🚀 Main Function
# ============================

def main():
    
    # Error handling for wrong file path
    if not os.path.exists(IMAGE_PATH):
        raise FileNotFoundError(f"Image not found: {IMAGE_PATH}")
    image = cv2.imread(IMAGE_PATH)
    if image is None:
        raise ValueError(f"Failed to read image from: {IMAGE_PATH}")

    # Get instrinsic matrix
    K = get_intrinsic_matrix_from_config(CONFIG_PATH)
    # compute the pitch
    pitch_deg, _ = estimate_pitch_from_ply(PLY_PATH, CAMERA_HEIGHT_CM)
    
    # print pitch value for debugging
    print("Pitch Degree:\n", pitch_deg)
    
    # convert height from [cm] to [m]
    camera_height_m = CAMERA_HEIGHT_CM / 100.0
    
    # Compute the homography matrix
    H = compute_homography(K, pitch_deg, camera_height_m, YAW_DEG, ROLL_DEG, GROUND_NORMAL)

    # Perform perspective transform
    bird_eye_view = cv2.warpPerspective(image, H, OUTPUT_SIZE)
    
    # Show results
    cv2.imshow("Original Image", image)
    cv2.imshow("Bird's Eye View", bird_eye_view)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Optionally save the output
    cv2.imwrite("bird_eye_view.png", bird_eye_view)

    # Visualize a few transformed points
    h, w = image.shape[:2]
    corners = np.array([[0, 0], [w-1, 0], [w-1, h-1], [0, h-1]], dtype=np.float32)
    transformed_corners = cv2.perspectiveTransform(corners[None, :, :], H)
    print("Transformed corners:", transformed_corners)
    
# ============================
# 🔧 Run if main
# ============================

if __name__ == "__main__":
    main()
