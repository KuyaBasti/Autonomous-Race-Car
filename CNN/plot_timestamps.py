import pandas as pd
import matplotlib.pyplot as plt
import os

# Paths
run_folder = 'data/run_1'
output_folder = os.path.join(run_folder, 'output')
visualizations_folder = os.path.join(output_folder, 'visualizations')

# Create visualizations directory if it doesn't exist
os.makedirs(visualizations_folder, exist_ok=True)

# Read the timestamp files
image_ts = pd.read_csv(os.path.join(output_folder, 'image_timestamps.csv'))
ackermann_ts = pd.read_csv(os.path.join(output_folder, 'ackermann_timestamps.csv'))

# Create the plot
plt.figure(figsize=(15, 6))

# Plot image timestamps
plt.scatter(image_ts['image_timestamp_sec'], 
           [1] * len(image_ts), 
           label='Image Timestamps', 
           alpha=0.5, 
           marker='o')

# Plot ackermann timestamps
plt.scatter(ackermann_ts['ackermann_timestamp_sec'], 
           [2] * len(ackermann_ts), 
           label='Ackermann Timestamps', 
           alpha=0.5, 
           marker='x')

# Customize the plot
plt.title('Image and Ackermann Timestamps Comparison')
plt.xlabel('Timestamp (seconds)')
plt.yticks([1, 2], ['Images', 'Ackermann'])
plt.grid(True, alpha=0.3)
plt.legend()

# Adjust layout and save
plt.tight_layout()
plt.savefig(os.path.join(visualizations_folder, 'timestamp_comparison.png'), dpi=300, bbox_inches='tight')
print(f"Plot saved as '{visualizations_folder}/timestamp_comparison.png'")

# Print some statistics
print("\nTimestamp Statistics:")
print(f"Number of image timestamps: {len(image_ts)}")
print(f"Number of ackermann timestamps: {len(ackermann_ts)}")
print(f"\nImage timestamp range: {image_ts['image_timestamp_sec'].min():.2f} to {image_ts['image_timestamp_sec'].max():.2f}")
print(f"Ackermann timestamp range: {ackermann_ts['ackermann_timestamp_sec'].min():.2f} to {ackermann_ts['ackermann_timestamp_sec'].max():.2f}") 