import os
import shutil
import pandas as pd

def organize_selected_data():
    # Read the synchronized data CSV
    df = pd.read_csv('data/run_1/output/interpolated_synced_images_with_commands.csv')
    
    # Filter for images marked as 'yes'
    selected_df = df[df['keep'] == 'yes']
    
    # Create output directories
    base_output_dir = 'data/run_1/output/selected_data'
    images_dir = os.path.join(base_output_dir, 'images')
    bitmasks_dir = os.path.join(base_output_dir, 'bitmasks')
    
    for directory in [images_dir, bitmasks_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    # Source directories
    source_images_dir = 'data/run_1/extracted_images'
    source_bitmasks_dir = 'data/run_1/masks'  # Updated path
    
    # Copy selected images and their corresponding bitmasks
    for image_name in selected_df['image']:
        # Handle image
        source_image_path = os.path.join(source_images_dir, image_name)
        dest_image_path = os.path.join(images_dir, image_name)
        if os.path.exists(source_image_path):
            shutil.copy2(source_image_path, dest_image_path)
            print(f"Copied image: {image_name}")
        else:
            print(f"Warning: Could not find image {image_name}")
        
        # Handle corresponding bitmask
        # Extract frame number and timestamp from image name
        # Example: frame_0635_1747705570832726952.jpg -> frame_0635_1747705570832726952_mask.png
        base_name = os.path.splitext(image_name)[0]  # Remove extension
        bitmask_name = f"{base_name}_mask.png"
        
        source_bitmask_path = os.path.join(source_bitmasks_dir, bitmask_name)
        dest_bitmask_path = os.path.join(bitmasks_dir, bitmask_name)
        if os.path.exists(source_bitmask_path):
            shutil.copy2(source_bitmask_path, dest_bitmask_path)
            print(f"Copied bitmask: {bitmask_name}")
        else:
            print(f"Warning: Could not find bitmask {bitmask_name}")
    
    # Save filtered CSV with all data
    output_csv = os.path.join(base_output_dir, 'selected_data.csv')
    selected_df.to_csv(output_csv, index=False)
    
    print(f"\nOrganization complete:")
    print(f"- Saved {len(selected_df)} entries to {output_csv}")
    print(f"- Copied images to {images_dir}/")
    print(f"- Copied bitmasks to {bitmasks_dir}/")

if __name__ == "__main__":
    organize_selected_data() 