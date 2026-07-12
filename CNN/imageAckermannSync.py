import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

# Paths
run_folder = 'data/run_1'
image_folder = os.path.join(run_folder, 'extracted_images')
ackermann_csv_path = os.path.join(run_folder, 'ackermann_output.csv')
image_ts_path = os.path.join(run_folder, 'output/image_timestamps.csv')
ackermann_ts_path = os.path.join(run_folder, 'output/ackermann_timestamps.csv')
output_folder = os.path.join(run_folder, 'output')
visualizations_folder = os.path.join(output_folder, 'visualizations')

# Create output directories if they don't exist
os.makedirs(visualizations_folder, exist_ok=True)

# Read pre-processed timestamps
image_ts_df = pd.read_csv(image_ts_path)
ackermann_ts_df = pd.read_csv(ackermann_ts_path)

# Read ackermann data
ackermann_df = pd.read_csv(
    ackermann_csv_path,
    sep=',',
    dtype={'timestamp': float, 'steering_angle': float, 'speed': float}
)

# Sort and prepare data
ackermann_df = ackermann_df.sort_values('timestamp').reset_index(drop=True)
ackermann_timestamps = ackermann_df['timestamp'].values * 1e-9  # Convert to seconds
image_timestamps = image_ts_df['image_timestamp_sec'].values

# Debug: Print timestamp ranges and counts
print("\nData Statistics:")
print(f"Number of ackermann commands: {len(ackermann_df)}")
print(f"Number of image timestamps: {len(image_timestamps)}")
print(f"\nTimestamp Ranges:")
print(f"Ackermann timestamps: {ackermann_timestamps[0]:.9f} → {ackermann_timestamps[-1]:.9f}")
print(f"Image timestamps: {image_timestamps[0]:.9f} → {image_timestamps[-1]:.9f}")

# Get image filenames and create timestamp mapping
image_files = sorted([f for f in os.listdir(image_folder) if f.endswith('.png') or f.endswith('.jpg')])
print(f"\nNumber of actual image files: {len(image_files)}")

# Create a mapping of timestamps to filenames
timestamp_to_filename = {}
for f in image_files:
    try:
        timestamp_ns = int(f.split('_')[-1].split('.')[0])
        timestamp_sec = timestamp_ns * 1e-9
        timestamp_to_filename[timestamp_sec] = f
    except ValueError:
        print(f"Warning: Could not parse timestamp from filename: {f}")

print(f"Number of valid timestamp mappings: {len(timestamp_to_filename)}")

matched_data = []
gap_distribution = defaultdict(int)  # Debug: Track gap distribution

# Calculate overlap period
overlap_start = max(image_timestamps[0], ackermann_timestamps[0])
overlap_end = min(image_timestamps[-1], ackermann_timestamps[-1])

# Filter images to only those within the overlap period
valid_image_indices = np.where((image_timestamps >= overlap_start) & 
                             (image_timestamps <= overlap_end))[0]
valid_image_timestamps = image_timestamps[valid_image_indices]

print(f"\nProcessing {len(valid_image_timestamps)} images within overlap period")

# Process each image timestamp
for img_ts in valid_image_timestamps:
    # Find the two surrounding ackermann commands
    idx_after = np.searchsorted(ackermann_timestamps, img_ts)
    
    if idx_after == 0 or idx_after >= len(ackermann_df):
        print(f"Skipping timestamp {img_ts:.9f}: no surrounding ackermann data")
        continue
    
    idx_before = idx_after - 1
    t0, t1 = ackermann_timestamps[idx_before], ackermann_timestamps[idx_after]
    gap = t1 - t0
    
    # Debug: Track gap distribution
    gap_bucket = round(gap * 10) / 10  # Round to nearest 0.1s
    gap_distribution[gap_bucket] += 1
    
    # If time gap is too large, skip
    if gap > 0.5:  # Using 0.5s threshold for driving commands
        print(f"Skipping timestamp {img_ts:.9f}: time gap too large ({gap:.3f}s)")
        continue
    
    # Interpolation factor
    alpha = (img_ts - t0) / (t1 - t0)
    
    # Interpolate ackermann commands
    cmd0 = ackermann_df.iloc[idx_before]
    cmd1 = ackermann_df.iloc[idx_after]
    
    # Get corresponding filename
    img_file = timestamp_to_filename.get(img_ts)
    if img_file is None:
        print(f"Warning: No filename found for timestamp {img_ts:.9f}")
        continue
    
    interp_cmd = {
        'image': img_file,
        'timestamp': img_ts,
        'steering_angle': cmd0['steering_angle'] * (1 - alpha) + cmd1['steering_angle'] * alpha,
        'speed': cmd0['speed'] * (1 - alpha) + cmd1['speed'] * alpha,
        'keep': 'yes'  # Default to 'yes' since we're only processing valid images
    }
    
    matched_data.append(interp_cmd)

# Save matched/interpolated results
matched_df = pd.DataFrame(matched_data)
matched_df.to_csv(os.path.join(output_folder, 'interpolated_synced_images_with_commands.csv'), index=False)

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
plt.plot(ackermann_timestamps, [1]*len(ackermann_timestamps), 'ro', label='Ackermann Timestamps', alpha=0.5)
plt.plot(valid_image_timestamps, [0]*len(valid_image_timestamps), 'bo', label='Image Timestamps', alpha=0.5)
plt.plot(matched_df['timestamp'], [0.5]*len(matched_df), 'gx', label='Matched Images', alpha=0.5)

plt.legend()
plt.yticks([0, 0.5, 1], ['Images', 'Matched', 'Ackermann'])
plt.title("Ackermann vs Image Timestamp Alignment")
plt.xlabel("Timestamp (seconds)")
plt.grid(True, alpha=0.3)

# Plot 2: Gap distribution histogram
plt.subplot(2, 1, 2)
gaps = list(gap_distribution.keys())
counts = list(gap_distribution.values())
plt.bar(gaps, counts, width=0.1)
plt.title("Distribution of Time Gaps Between Ackermann Commands")
plt.xlabel("Time Gap (seconds)")
plt.ylabel("Number of Images")
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(visualizations_folder, 'sync_timestamp_analysis.png'), dpi=300, bbox_inches='tight')
print(f"\nVisualization saved as '{visualizations_folder}/sync_timestamp_analysis.png'") 