import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

# Paths
image_folder = 'data/datarun_for_stitching_1/extracted_images'
pose_csv_path = 'data/datarun_for_stitching_1/extracted_pose_data.csv'
image_ts_path = 'data/datarun_for_stitching_1/output/image_timestamps.csv'
pose_ts_path = 'data/datarun_for_stitching_1/output/pose_timestamps.csv'

# Read pre-processed timestamps
image_ts_df = pd.read_csv(image_ts_path)
pose_ts_df = pd.read_csv(pose_ts_path)

# Read pose data
pose_df = pd.read_csv(
    pose_csv_path,
    sep=',',
    names=['timestamp', 'pos_x', 'pos_y', 'ori_w'],
    skiprows=1,
    dtype={'timestamp': float, 'pos_x': float, 'pos_y': float, 'ori_w': float}
)

# Sort and prepare data
pose_df = pose_df.sort_values('timestamp').reset_index(drop=True)
pose_timestamps = pose_df['timestamp'].values
image_timestamps = image_ts_df['image_timestamp_sec'].values

# Debug: Print timestamp ranges
print("\nTimestamp Ranges:")
print(f"Pose timestamps: {pose_timestamps[0]:.9f} → {pose_timestamps[-1]:.9f}")
print(f"Image timestamps: {image_timestamps[0]:.9f} → {image_timestamps[-1]:.9f}")

# Get image filenames
image_files = sorted([f for f in os.listdir(image_folder) if f.endswith('.png') or f.endswith('.jpg')])

# Create a mapping of timestamps to filenames
timestamp_to_filename = {
    int(f.split('_')[-1].split('.')[0]) * 1e-9: f 
    for f in image_files
}

matched_data = []
gap_distribution = defaultdict(int)  # Debug: Track gap distribution

# Calculate overlap period
overlap_start = max(image_timestamps[0], pose_timestamps[0])
overlap_end = min(image_timestamps[-1], pose_timestamps[-1])

# Filter images to only those within the overlap period
valid_image_indices = np.where((image_timestamps >= overlap_start) & 
                             (image_timestamps <= overlap_end))[0]
valid_image_timestamps = image_timestamps[valid_image_indices]

print(f"\nProcessing {len(valid_image_timestamps)} images within overlap period")

# Process each image timestamp
for img_ts in valid_image_timestamps:
    # Find the two surrounding poses
    idx_after = np.searchsorted(pose_timestamps, img_ts)
    
    if idx_after == 0 or idx_after >= len(pose_df):
        print(f"Skipping timestamp {img_ts:.9f}: no surrounding pose data")
        continue
    
    idx_before = idx_after - 1
    t0, t1 = pose_timestamps[idx_before], pose_timestamps[idx_after]
    gap = t1 - t0
    
    # Debug: Track gap distribution
    gap_bucket = round(gap * 10) / 10  # Round to nearest 0.1s
    gap_distribution[gap_bucket] += 1
    
    # If time gap is too large, skip
    if gap > 7.0:  # Increased threshold to 5 seconds
        print(f"Skipping timestamp {img_ts:.9f}: time gap too large ({gap:.3f}s)")
        continue
    
    # Interpolation factor
    alpha = (img_ts - t0) / (t1 - t0)
    
    # Interpolate pose
    pose0 = pose_df.iloc[idx_before]
    pose1 = pose_df.iloc[idx_after]
    
    # Get corresponding filename
    img_file = timestamp_to_filename.get(img_ts)
    if img_file is None:
        print(f"Warning: No filename found for timestamp {img_ts:.9f}")
        continue
    
    interp_pose = {
        'image': img_file,
        'pose_timestamp': img_ts,
        'pos_x': pose0['pos_x'] * (1 - alpha) + pose1['pos_x'] * alpha,
        'pos_y': pose0['pos_y'] * (1 - alpha) + pose1['pos_y'] * alpha,
        'ori_w': pose0['ori_w'] * (1 - alpha) + pose1['ori_w'] * alpha,
        'keep': 'yes'  # Changed default to 'yes' since we're only processing valid images
    }
    
    matched_data.append(interp_pose)

# Save matched/interpolated results
matched_df = pd.DataFrame(matched_data)
matched_df.to_csv('data/datarun_for_stitching_1/output/interpolated_synced_images_with_pose.csv', index=False)

print(f"\nSynchronization Statistics:")
print(f"Total images in overlap period: {len(valid_image_timestamps)}")
print(f"Successfully matched: {len(matched_df)}")
print(f"Match rate: {(len(matched_df) / len(valid_image_timestamps) * 100):.1f}%")

# Debug: Print gap distribution
print("\nGap Distribution (number of images with each gap size):")
for gap, count in sorted(gap_distribution.items()):
    print(f"{gap:.1f}s: {count} images")

# Create visualization
plt.figure(figsize=(15, 10))

# Plot 1: Timestamp alignment
plt.subplot(2, 1, 1)
plt.plot(pose_timestamps, [1]*len(pose_timestamps), 'ro', label='Pose Timestamps', alpha=0.5)
plt.plot(valid_image_timestamps, [0]*len(valid_image_timestamps), 'bo', label='Image Timestamps', alpha=0.5)
plt.plot(matched_df['pose_timestamp'], [0.5]*len(matched_df), 'gx', label='Matched Images', alpha=0.5)

plt.legend()
plt.yticks([0, 0.5, 1], ['Images', 'Matched', 'Poses'])
plt.title("Pose vs Image Timestamp Alignment")
plt.xlabel("Timestamp (seconds)")
plt.grid(True, alpha=0.3)

# Plot 2: Gap distribution histogram
plt.subplot(2, 1, 2)
gaps = list(gap_distribution.keys())
counts = list(gap_distribution.values())
plt.bar(gaps, counts, width=0.1)
plt.title("Distribution of Time Gaps Between Poses")
plt.xlabel("Time Gap (seconds)")
plt.ylabel("Number of Images")
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('data/datarun_for_stitching_1/output/visualizations/sync_timestamp_analysis.png', dpi=300, bbox_inches='tight')
print("\nVisualization saved as 'data/datarun_for_stitching_1/output/visualizations/sync_timestamp_analysis.png'")


