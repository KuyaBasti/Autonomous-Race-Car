import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Set the backend to Agg before importing pyplot
import matplotlib.pyplot as plt
import cv2
from pathlib import Path

# Paths
run_folder = 'data/run_1'
selected_data_folder = os.path.join(run_folder, 'output/selected_data')
image_folder = os.path.join(selected_data_folder, 'images')
synced_data_path = os.path.join(selected_data_folder, 'selected_data.csv')
visualizations_folder = os.path.join(selected_data_folder, 'driving_visualizations')

# Create output directory
os.makedirs(visualizations_folder, exist_ok=True)

# Read synchronized data
df = pd.read_csv(synced_data_path)

def create_driving_visualization(image_path, steering_angle, speed, output_path):
    """
    Create a visualization of driving instructions overlaid on the image.
    
    Args:
        image_path: Path to the input image
        steering_angle: Steering angle in radians (positive = left turn)
        speed: Speed value
        output_path: Path to save the visualization
    """
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        print(f"Warning: Could not read image {image_path}")
        return
    
    # Convert to RGB for matplotlib
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Create figure
    plt.figure(figsize=(12, 8))
    plt.imshow(img)
    
    # Calculate arrow parameters
    height, width = img.shape[:2]
    center_x = width // 2
    # Position arrow at bottom of image
    center_y = height - 50  # 50 pixels from bottom
    
    # Scale arrow length based on speed
    arrow_length = min(width, height) * 0.4 * abs(speed) / 2.0  # Increased scale factor for visibility
    
    # Calculate end point of arrow based on steering angle (negated to make positive = left)
    end_x = center_x - arrow_length * np.sin(steering_angle)  # Negated sin
    end_y = center_y - arrow_length * np.cos(steering_angle)  # Keep cos the same
    
    # Draw center reference line
    plt.plot([center_x, center_x], [center_y - 20, center_y + 20], 
             color='white', linewidth=2, alpha=0.5)
    
    # Draw arrow with increased visibility
    plt.arrow(center_x, center_y, 
             end_x - center_x, end_y - center_y,
             head_width=30, head_length=40, fc='red', ec='red',
             width=5, alpha=0.8)
    
    # Add text annotations with background
    plt.text(10, 30, f"Steering: {steering_angle:.2f} rad", 
             color='white', fontsize=12, 
             bbox=dict(facecolor='red', alpha=0.7))
    plt.text(10, 60, f"Speed: {speed:.2f}", 
             color='white', fontsize=12,
             bbox=dict(facecolor='red', alpha=0.7))
    
    # Remove axes and save
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', pad_inches=0)
    plt.close()

# Process each image
print(f"Processing first 20 frames from selected data...")
for idx, row in df.head(100).iterrows():
    print(f"Processing image {idx + 1}/100")
    
    image_path = os.path.join(image_folder, row['image'])
    output_path = os.path.join(visualizations_folder, f"viz_{Path(row['image']).stem}.png")
    
    create_driving_visualization(
        image_path=image_path,
        steering_angle=row['steering_angle'],
        speed=row['speed'],
        output_path=output_path
    )

print(f"\nVisualizations saved to: {visualizations_folder}") 