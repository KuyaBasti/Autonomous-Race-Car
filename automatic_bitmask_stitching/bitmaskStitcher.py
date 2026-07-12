import cv2
import numpy as np
import pandas as pd
import os
import math
import csv
import matplotlib.pyplot as plt

# === CONFIGURATION ===
BITMASK_FOLDER = "data/datarun_for_stitching_1/output/bitmask_selected_images"
POSE_FILE = "data/datarun_for_stitching_1/output/selected_images/selected_images_with_poses.csv"
SLAM_MAP_FILE = "slam_maps/404squadMap.png"
OUTPUT_FILE = "data/datarun_for_stitching_1/output/visualizations/stitched_overlay_4.png"

# SLAM map metadata (from map.yaml)
MAP_RESOLUTION = 0.05  # meters per pixel
MAP_ORIGIN = (0.166, 0.0659)  # (x, y) in meters

# Bitmask real-world size (in meters)
BITMASK_WIDTH_METERS = 0.762
BITMASK_HEIGHT_METERS = 1.0

# Bitmask image size (in pixels)
BITMASK_WIDTH_PX = 640
BITMASK_HEIGHT_PX = 480

# Compute bitmask resolution (meters/pixel)
BITMASK_RES_X = BITMASK_WIDTH_METERS / BITMASK_WIDTH_PX
BITMASK_RES_Y = BITMASK_HEIGHT_METERS / BITMASK_HEIGHT_PX

def quaternion_to_yaw(w):
    """Convert quaternion w component to yaw angle in radians."""
    # For a quaternion (w, 0, 0, z), yaw = 2 * atan2(z, w)
    # Since we only have w, we can use: yaw = 2 * atan2(sqrt(1-w^2), w)
    if abs(w) >= 1.0:
        return 0.0
    return 2 * math.atan2(math.sqrt(1 - w*w), w)

# === LOAD DATA ===
print("Loading SLAM map...")
slam_map = cv2.imread(SLAM_MAP_FILE, cv2.IMREAD_GRAYSCALE)
map_height, map_width = slam_map.shape

print("Loading poses from CSV...")
poses_df = pd.read_csv(POSE_FILE)
# Filter for images marked as 'yes'
poses_df = poses_df[poses_df['keep'] == 'yes']

# Create an empty canvas same size as SLAM map
stitched_map = np.zeros_like(slam_map, dtype=np.uint8)
# Prepare a color overlay
overlay = cv2.cvtColor(slam_map, cv2.COLOR_GRAY2BGR)

# Prepare color key dictionary
color_key = []

# === PROCESS EACH BITMASK ===
print("Processing bitmask images...")
for idx, row in poses_df.iterrows():
    filename = row['image']
    # Insert '_mask' before the file extension
    name, ext = os.path.splitext(filename)
    bitmask_filename = f"{name}_mask{ext}"
    bitmask_path = os.path.join(BITMASK_FOLDER, bitmask_filename)
    if not os.path.exists(bitmask_path):
        print(f"Warning: Bitmask {filename} not found, skipping.")
        continue

    bitmask = cv2.imread(bitmask_path, cv2.IMREAD_GRAYSCALE)
    if bitmask is None:
        print(f"Warning: Could not load image {filename}, skipping.")
        continue

    # Debug: Print unique values in the bitmask
    print(f"Bitmask unique values: {np.unique(bitmask)}")

    # Threshold to binary (just in case)
    _, bitmask = cv2.threshold(bitmask, 127, 255, cv2.THRESH_BINARY)

    # Extract pose
    x_m, y_m = row['pos_x'], row['pos_y']
    yaw = quaternion_to_yaw(row['ori_w'])

    # Convert world coordinates to SLAM map pixels
    x_px = int((x_m - MAP_ORIGIN[0]) / MAP_RESOLUTION)
    y_px = int((y_m - MAP_ORIGIN[1]) / MAP_RESOLUTION)
    print(f"Placing bitmask at pixel: ({x_px}, {y_px})")

    # Compute scale from bitmask resolution to SLAM map resolution
    scale_x = BITMASK_RES_X / MAP_RESOLUTION
    scale_y = BITMASK_RES_Y / MAP_RESOLUTION
    print(f"scale_x: {scale_x}, scale_y: {scale_y}")
    # Expected size of bitmask on map (in pixels)
    expected_width = int(BITMASK_WIDTH_PX * scale_x)
    expected_height = int(BITMASK_HEIGHT_PX * scale_y)
    print(f"Expected warped bitmask size on map: {expected_width}x{expected_height}")

    # Center of the bitmask image
    cx = BITMASK_WIDTH_PX // 2
    cy = BITMASK_HEIGHT_PX // 2

    # Build affine transform (translation, scaling, rotation)
    M_translate = np.array([
        [1, 0, -cx],
        [0, 1, -cy],
        [0, 0, 1]
    ], dtype=np.float32)
    M_scale = np.array([
        [scale_x, 0, 0],
        [0, scale_y, 0],
        [0, 0, 1]
    ], dtype=np.float32)
    M_rotate = np.array([
        [np.cos(-yaw), -np.sin(-yaw), 0],
        [np.sin(-yaw), np.cos(-yaw), 0],
        [0, 0, 1]
    ], dtype=np.float32)
    # Combine: center -> scale -> rotate -> translate to map
    M_transform = M_rotate @ M_scale @ M_translate
    M_transform[0, 2] += x_px
    M_transform[1, 2] += y_px
    M_transform = M_transform[:2, :]

    # Warp the bitmask into SLAM map space
    warped = cv2.warpAffine(bitmask, M_transform, (map_width, map_height), flags=cv2.INTER_NEAREST)
    print(f"warped shape: {warped.shape}, nonzero pixels: {np.count_nonzero(warped)}")

    # Save warped bitmask for inspection if it has nonzero pixels
    # if np.count_nonzero(warped) > 0:
    #     cv2.imwrite(f"data/datarun_for_stitching_1/output/visualizations/warped_{name}.png", warped)

    # Generate a unique color for this bitmask (using a colormap for reproducibility)
    color = tuple(int(c) for c in np.array(cv2.applyColorMap(np.array([[int(255 * idx / len(poses_df))]], dtype=np.uint8), cv2.COLORMAP_HSV))[0,0])
    color_key.append({'frame': filename, 'color_b': color[0], 'color_g': color[1], 'color_r': color[2]})

    # Overlay this bitmask with its unique color
    mask_indices = np.where(warped > 0)
    overlay[mask_indices] = color

    # Stitch using max to preserve the track mask
    stitched_map = np.maximum(stitched_map, warped)

# === DEBUG: Save stitched_map before overlay ===
cv2.imwrite("data/datarun_for_stitching_1/output/visualizations/debug_stitched_map_4.png", stitched_map)

# === OVERLAY ON SLAM MAP ===
print("Overlaying stitched map on SLAM map...")
# (overlay is already built with unique colors)

# === SAVE RESULT ===
cv2.imwrite(OUTPUT_FILE, overlay)
print(f"Stitched overlay saved as: {OUTPUT_FILE}")

# === SAVE COLOR KEY ===
with open("data/datarun_for_stitching_1/output/visualizations/bitmask_color_key.csv", "w", newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=['frame', 'color_b', 'color_g', 'color_r'])
    writer.writeheader()
    for entry in color_key:
        writer.writerow(entry)
print("Color key saved as: data/datarun_for_stitching_1/output/visualizations/bitmask_color_key.csv")

# === SAVE COLOR LEGEND CHART ===
fig, ax = plt.subplots(figsize=(8, max(4, len(color_key)*0.3)))
for i, entry in enumerate(color_key):
    color = (entry['color_r']/255, entry['color_g']/255, entry['color_b']/255)
    ax.add_patch(plt.Rectangle((0, i), 1, 1, color=color))
    ax.text(1.2, i+0.5, entry['frame'], va='center', fontsize=8)
ax.set_xlim(0, 8)
ax.set_ylim(0, len(color_key))
ax.axis('off')
plt.tight_layout()
plt.savefig("data/datarun_for_stitching_1/output/visualizations/bitmask_color_legend.png", dpi=200)
plt.close()
print("Color legend chart saved as: data/datarun_for_stitching_1/output/visualizations/bitmask_color_legend.png")
