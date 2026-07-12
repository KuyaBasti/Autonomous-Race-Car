import pandas as pd
import matplotlib.pyplot as plt

# Read the timestamp files
image_ts = pd.read_csv('data/datarun_for_stitching_1/output/image_timestamps.csv')
pose_ts = pd.read_csv('data/datarun_for_stitching_1/output/pose_timestamps.csv')

# Create the plot
plt.figure(figsize=(15, 6))

# Plot image timestamps
plt.scatter(image_ts['image_timestamp_sec'], 
           [1] * len(image_ts), 
           label='Image Timestamps', 
           alpha=0.5, 
           marker='o')

# Plot pose timestamps
plt.scatter(pose_ts['pose_timestamp_sec'], 
           [2] * len(pose_ts), 
           label='Pose Timestamps', 
           alpha=0.5, 
           marker='x')

# Customize the plot
plt.title('Image and Pose Timestamps Comparison')
plt.xlabel('Timestamp (seconds)')
plt.yticks([1, 2], ['Images', 'Poses'])
plt.grid(True, alpha=0.3)
plt.legend()

# Adjust layout and save
plt.tight_layout()
plt.savefig('data/datarun_for_stitching_1/output/visualizations/timestamp_comparison.png', dpi=300, bbox_inches='tight')
print("Plot saved as 'data/datarun_for_stitching_1/output/visualizations/timestamp_comparison.png'")

# Print some statistics
print("\nTimestamp Statistics:")
print(f"Number of image timestamps: {len(image_ts)}")
print(f"Number of pose timestamps: {len(pose_ts)}")
print(f"\nImage timestamp range: {image_ts['image_timestamp_sec'].min():.2f} to {image_ts['image_timestamp_sec'].max():.2f}")
print(f"Pose timestamp range: {pose_ts['pose_timestamp_sec'].min():.2f} to {pose_ts['pose_timestamp_sec'].max():.2f}") 