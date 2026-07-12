# Stitch Map

This project provides tools for processing and analyzing image sequences with corresponding pose data, primarily focused on creating stitched maps from camera images and overlaying them on SLAM maps.

## Project Structure

### Core Scripts
- `bitmaskStitcher.py`: Main script for stitching bitmask images and overlaying them on SLAM maps
  - Handles coordinate transformations between real-world and pixel coordinates
  - Creates color-coded overlays with corresponding legends
  - Supports configurable map resolution and bitmask dimensions
- `imagePoseSync.py`: Synchronizes image timestamps with pose data
- `imagePoseTimestamps.py`: Extracts and processes timestamps from images and pose data
- `timestamp_analysis.py`: Analyzes and visualizes timestamp relationships between images and poses
- `plot_timestamps.py`: Creates visualization plots for timestamp analysis
- `image_evaluator.py`: GUI tool for evaluating and selecting images
- `extract_selected_images.py`: Extracts selected images and their corresponding poses

### Directory Structure
```
.
├── data/
│   ├── bag_stuff/                    # Raw extracted images and data
│   └── datarun_for_stitching_1/
│       ├── output/
│       │   ├── bitmask_selected_images/  # Processed bitmask images
│       │   ├── selected_images/          # Selected images for processing
│       │   ├── visualizations/           # Output visualizations
│       │   ├── interpolated_synced_images_with_pose.csv
│       │   ├── pose_timestamps.csv
│       │   └── image_timestamps.csv
│       └── extracted_pose_data.csv
├── docs/                            # Documentation files
├── slam_maps/                       # SLAM map files
├── selected_images/                 # Selected images for processing
├── track_images/                    # Track-related images
├── visualizations/                  # General visualization outputs
└── requirements.txt                 # Project dependencies
```

### Data Files
- `data/datarun_for_stitching_1/output/interpolated_synced_images_with_pose.csv`: Contains synchronized image and pose data
- `data/datarun_for_stitching_1/output/image_timestamps.csv`: Raw image timestamps
- `data/datarun_for_stitching_1/output/pose_timestamps.csv`: Raw pose timestamps
- `data/datarun_for_stitching_1/extracted_pose_data.csv`: Raw pose data from the dataset

### Visualization Files
All visualization files are stored in the `data/datarun_for_stitching_1/output/visualizations/` directory:
- `timestamp_analysis.png`: Visualization of timestamp analysis
- `sync_timestamp_analysis.png`: Visualization of synchronized timestamp analysis
- `timestamp_comparison.png`: Comparison of different timestamp sets
- `stitched_overlay.png`: Final stitched map overlay with color-coded bitmasks
- `bitmask_color_legend.png`: Legend showing color mapping for each bitmask
- `bitmask_color_key.csv`: CSV file containing color mappings for each bitmask

## Workflow

1. **Data Extraction**
   - Extract images and pose data from ROS bags into the `bag_stuff` directory
   - The data should be organized with images in `bag_stuff/extracted_images` and pose data in CSV format

2. **Timestamp Processing**
   - Run `imagePoseTimestamps.py` to extract timestamps from images and pose data
   - Use `timestamp_analysis.py` to analyze timestamp relationships
   - Visualize the analysis using `plot_timestamps.png`

3. **Image-Pose Synchronization**
   - Run `imagePoseSync.py` to synchronize images with their corresponding poses
   - This creates `interpolated_synced_images_with_pose.csv`

4. **Image Evaluation**
   - Use `image_evaluator.py` to review and select images
   - The GUI allows you to:
     - View each image with its corresponding pose data
     - Mark images as keep/reject
     - Navigate through images using keyboard shortcuts
     - Save your selections

5. **Extract Selected Images**
   - Run `extract_selected_images.py` to:
     - Create a new directory with selected images
     - Generate a CSV file with corresponding pose data
     - This creates `selected_images/` directory and `selected_images_with_poses.csv`

6. **Bitmask Stitching**
   - Use `bitmaskStitcher.py` to create stitched maps from the selected bitmask images
   - The script:
     - Transforms bitmask coordinates to match SLAM map space
     - Creates color-coded overlays for each bitmask
     - Generates a color legend and mapping file
     - Saves both the stitched map and overlay visualizations

## Configuration

The `bitmaskStitcher.py` script uses several configuration parameters:
- `MAP_RESOLUTION`: Resolution of the SLAM map in meters per pixel
- `MAP_ORIGIN`: Origin coordinates of the SLAM map in meters
- `BITMASK_WIDTH_METERS`: Real-world width of bitmasks in meters
- `BITMASK_HEIGHT_METERS`: Real-world height of bitmasks in meters
- `BITMASK_WIDTH_PX`: Width of bitmask images in pixels
- `BITMASK_HEIGHT_PX`: Height of bitmask images in pixels

## Requirements

Install required packages using:
```bash
pip install -r requirements.txt
```

Required packages:
- opencv-python
- pandas
- Pillow
- numpy
- matplotlib

## Usage Notes

- The image evaluator (`image_evaluator.py`) provides keyboard shortcuts:
  - Left/Right arrows: Navigate between images
  - Space: Toggle keep/reject status
  - S: Save current selections
  - Q: Quit the application

- When using the image evaluator, all images are initially marked as 'no'. Mark only the images you want to keep as 'yes'.

- The timestamp analysis tools help ensure proper synchronization between images and poses, which is crucial for accurate stitching.

- The bitmask stitcher creates both a binary stitched map and a color-coded overlay, along with a legend showing which color corresponds to which image.

## File Descriptions

### Core Processing Scripts
- `bitmaskStitcher.py`: Implements bitmask stitching and SLAM map overlay with color coding
- `imagePoseSync.py`: Handles synchronization between image and pose timestamps
- `imagePoseTimestamps.py`: Extracts and processes timestamps from both image and pose data
- `timestamp_analysis.py`: Analyzes timestamp relationships and generates visualizations
- `plot_timestamps.py`: Creates visualization plots for timestamp analysis

### Utility Scripts
- `image_evaluator.py`: GUI tool for reviewing and selecting images
- `extract_selected_images.py`: Extracts selected images and their pose data

### Data Files
- `interpolated_synced_images_with_pose.csv`: Main data file containing synchronized image and pose information
- `image_timestamps.csv`: Contains timestamps extracted from images
- `pose_timestamps.csv`: Contains timestamps from pose data
- `selected_images_with_poses.csv`: Contains only the selected images and their corresponding poses 