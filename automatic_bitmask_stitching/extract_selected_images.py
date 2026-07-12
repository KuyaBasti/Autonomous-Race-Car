import os
import shutil
import pandas as pd

def extract_selected_images():
    # Read the original CSV file
    df = pd.read_csv('data/datarun_for_stitching_1/output/interpolated_synced_images_with_pose.csv')
    
    # Filter for images marked as 'yes'
    selected_df = df[df['keep'] == 'yes']
    
    # Create output directory if it doesn't exist
    output_dir = 'data/datarun_for_stitching_1/output/selected_images'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Copy selected images to output directory
    source_dir = 'data/datarun_for_stitching_1/extracted_images'
    for image_name in selected_df['image']:
        source_path = os.path.join(source_dir, image_name)
        dest_path = os.path.join(output_dir, image_name)
        if os.path.exists(source_path):
            shutil.copy2(source_path, dest_path)
            print(f"Copied {image_name}")
        else:
            print(f"Warning: Could not find {image_name}")
    
    # Save filtered CSV
    output_csv = 'data/datarun_for_stitching_1/output/selected_images/selected_images_with_poses.csv'
    selected_df.to_csv(output_csv, index=False)
    print(f"\nSaved {len(selected_df)} images and their poses to {output_csv}")
    print(f"Copied {len(selected_df)} images to {output_dir}/")

if __name__ == "__main__":
    extract_selected_images() 