import os
import pandas as pd
import numpy as np

# Paths
image_folder = 'data/datarun_for_stitching_1/extracted_images'
pose_csv_path = 'data/datarun_for_stitching_1/extracted_pose_data.csv'

# --- Extract image timestamps ---
image_files = sorted([f for f in os.listdir(image_folder) if f.endswith('.png') or f.endswith('.jpg')])

image_timestamps = []
for f in image_files:
    try:
        timestamp_ns = int(f.split('_')[-1].split('.')[0])
        timestamp_sec = timestamp_ns * 1e-9
        image_timestamps.append(timestamp_sec)
    except ValueError:
        print(f"Skipping file with invalid format: {f}")

# Convert to numpy array for sorting
image_timestamps = np.array(image_timestamps)
image_timestamps.sort()  # Sort timestamps

# Save image timestamps
image_ts_df = pd.DataFrame(image_timestamps, columns=['image_timestamp_sec'])
image_ts_df.to_csv('data/datarun_for_stitching_1/output/image_timestamps.csv', index=False)
print(f"Saved {len(image_timestamps)} image timestamps to 'image_timestamps.csv'.")

# --- Extract pose timestamps ---
try:
    # Read the CSV with explicit encoding and error handling
    pose_df = pd.read_csv(
        pose_csv_path,
        encoding='utf-8',
        sep=',',
        dtype={'timestamp_sec': float}
    )
    
    # Clean header names
    pose_df.columns = pose_df.columns.str.strip().str.replace('\ufeff', '')
    
    # Print the first few rows to verify data
    print("\nFirst few rows of pose data:")
    print(pose_df.head())
    
    # Extract timestamps and sort
    pose_ts_df = pose_df[['timestamp_sec']].copy()
    pose_ts_df.columns = ['pose_timestamp_sec']
    pose_ts_df = pose_ts_df.sort_values('pose_timestamp_sec').reset_index(drop=True)
    
    # Save timestamps
    pose_ts_df.to_csv('data/datarun_for_stitching_1/output/pose_timestamps.csv', index=False)
    print(f"\nSaved {len(pose_ts_df)} pose timestamps to 'pose_timestamps.csv'.")
    
    # Print timestamp ranges for verification
    print("\nTimestamp Ranges:")
    print(f"Image timestamps: {image_timestamps[0]:.9f} → {image_timestamps[-1]:.9f}")
    print(f"Pose timestamps: {pose_ts_df['pose_timestamp_sec'].iloc[0]:.9f} → {pose_ts_df['pose_timestamp_sec'].iloc[-1]:.9f}")
    
except Exception as e:
    print(f"Error reading pose data: {str(e)}")
    print("Please check that the file exists and is properly formatted.")