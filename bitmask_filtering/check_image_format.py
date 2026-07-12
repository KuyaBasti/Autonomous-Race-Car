import cv2
import numpy as np
import os

def check_image_format(image_path):
    # Read the image
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not read image at {image_path}")
        return
    
    # Get image shape
    height, width, channels = img.shape
    print(f"\nImage: {os.path.basename(image_path)}")
    print(f"Dimensions: {width}x{height}")
    print(f"Number of channels: {channels}")
    
    # Check if all channels are identical (grayscale)
    if channels == 3:
        is_grayscale = np.all(img[:,:,0] == img[:,:,1]) and np.all(img[:,:,1] == img[:,:,2])
        print(f"Is grayscale (all channels identical): {is_grayscale}")
        
        # Show unique values in each channel
        print("\nUnique values in each channel:")
        for i in range(3):
            unique_vals = np.unique(img[:,:,i])
            print(f"Channel {i}: {unique_vals}")
    else:
        print("Image is already single-channel (grayscale)")
        unique_vals = np.unique(img)
        print(f"Unique values: {unique_vals}")

if __name__ == "__main__":
    # Check all output images
    output_dir = "bitmask_filtering/outputs"
    for filename in ["aligned_with_worldmap_original.png", 
                    "aligned_with_worldmap_grey.png", 
                    "processed_bitmask.png"]:
        image_path = os.path.join(output_dir, filename)
        if os.path.exists(image_path):
            check_image_format(image_path)
            print("\n" + "="*50 + "\n") 