# CNN Training Pipeline

This project provides tools for training and visualizing CNN models for autonomous driving, using both images and bitmasks to predict steering angles and speeds.

## Project Structure

### Core Scripts
- `cnn_model.py`: Main script for training the CNN model
  - Supports both bitmask-only and image+bitmask training modes
  - Implements data loading, preprocessing, and model training
  - Includes model checkpointing and visualization capabilities
- `visualize_driving_instructions.py`: Creates visualizations of driving instructions
  - Overlays steering angle and speed information on images
  - Generates arrow-based visualizations for intuitive understanding
- `organize_selected_data.py`: Organizes selected images and bitmasks
  - Creates structured directories for training data
  - Maintains synchronization between images and their bitmasks
- `image_evaluator.py`: GUI tool for evaluating and selecting images
- `imageAckermannSync.py`: Synchronizes images with Ackermann drive commands
- `timestamp_analysis.py`: Analyzes and visualizes timestamp relationships
- `plot_timestamps.py`: Creates visualization plots for timestamp analysis

### Directory Structure
```
.
├── data/
│   └── run_1/
│       └── output/
│           ├── selected_data/
│           │   ├── images/          # Selected images for training
│           │   ├── bitmasks/        # Corresponding bitmasks
│           │   ├── driving_visualizations/  # Visualizations of driving instructions
│           │   └── selected_data.csv        # Synchronized data
│           └── model_checkpoints/   # Saved model checkpoints
├── cnn_model.py
├── visualize_driving_instructions.py
├── organize_selected_data.py
├── image_evaluator.py
├── imageAckermannSync.py
├── timestamp_analysis.py
└── plot_timestamps.py
```

### Data Files
- `data/run_1/output/selected_data/selected_data.csv`: Contains synchronized image, bitmask, and driving command data
- `data/run_1/output/selected_data/images/`: Directory containing selected images
- `data/run_1/output/selected_data/bitmasks/`: Directory containing corresponding bitmasks
- `data/run_1/output/selected_data/driving_visualizations/`: Directory containing visualizations of driving instructions

### Model Files
- `data/run_1/output/model_checkpoints/`: Directory containing model checkpoints
- `data/run_1/output/final_model_bitmask_only.h5`: Final model trained on bitmasks only
- `data/run_1/output/final_model_image_bitmask.h5`: Final model trained on both images and bitmasks

## Workflow

1. **Timestamp Analysis and Synchronization**
   - Run `timestamp_analysis.py` to analyze the relationship between image and pose timestamps
   - Use `plot_timestamps.py` to visualize the timestamp relationships
   - Run `imageAckermannSync.py` to synchronize images with their corresponding Ackermann drive commands
   - This creates a synchronized dataset with matching timestamps

2. **Image Evaluation and Selection**
   - Use `image_evaluator.py` to review and select images
   - The GUI allows you to:
     - View each image with its corresponding pose data
     - Mark images as keep/reject
     - Navigate through images using keyboard shortcuts
     - Save your selections to a CSV file

3. **Data Organization**
   - Run `organize_selected_data.py` to:
     - Create a structured directory for selected data
     - Copy selected images to the images directory
     - Copy corresponding bitmasks to the bitmasks directory
     - Generate a CSV file with synchronized data
   - This creates the following structure:
     ```
     data/run_1/output/selected_data/
     ├── images/          # Selected images
     ├── bitmasks/        # Corresponding bitmasks
     └── selected_data.csv # Synchronized data
     ```

4. **Data Visualization**
   - Run `visualize_driving_instructions.py` to:
     - Create visualizations of driving instructions
     - Overlay steering angle and speed information on images
     - Generate arrow-based visualizations
   - This helps verify:
     - The quality of the selected data
     - The accuracy of the synchronization
     - The clarity of the driving instructions

5. **Model Training**
   - Configure `cnn_model.py` by setting:
     - `USE_BITMASKS_ONLY = True/False` to choose training mode
     - `IMG_HEIGHT, IMG_WIDTH` for input dimensions
     - `BATCH_SIZE` and `EPOCHS` for training parameters
   - Run the training script to:
     - Load and preprocess the data
     - Train the CNN model
     - Save model checkpoints during training
     - Generate the final model file
   - Monitor training progress through:
     - Console output showing loss and metrics
     - Saved model checkpoints
     - Final model performance

6. **Model Evaluation and Iteration**
   - Review the training results
   - If needed, adjust the workflow by:
     - Selecting different images using `image_evaluator.py`
     - Modifying the training parameters in `cnn_model.py`
     - Switching between bitmask-only and image+bitmask modes
   - Repeat the process until satisfactory results are achieved

## Configuration

The `cnn_model.py` script uses several configuration parameters:
- `USE_BITMASKS_ONLY`: Toggle between bitmask-only and image+bitmask training
- `IMG_HEIGHT, IMG_WIDTH`: Input image dimensions
- `BATCH_SIZE`: Batch size for training
- `EPOCHS`: Number of training epochs

## Requirements

Install required packages using:
```bash
pip install -r requirements.txt
```

Required packages:
- tensorflow
- opencv-python
- pandas
- numpy
- matplotlib
- scikit-learn

## Usage Notes

- The CNN model can be trained in two modes:
  - Bitmask-only mode: Uses only bitmask images for training
  - Image+bitmask mode: Uses both original images and bitmasks

- The visualization tool (`visualize_driving_instructions.py`) provides:
  - Arrow-based visualization of steering angle
  - Speed information overlay
  - Clear visual feedback for model training

- Model checkpoints are saved during training to prevent data loss
- The final model is saved with a descriptive name based on the training mode

## File Descriptions

### Core Training Scripts
- `cnn_model.py`: Main training script with configurable input modes
- `visualize_driving_instructions.py`: Visualization tool for driving instructions
- `organize_selected_data.py`: Data organization and synchronization

### Utility Scripts
- `image_evaluator.py`: GUI for image selection and evaluation
- `imageAckermannSync.py`: Synchronization of images with drive commands
- `timestamp_analysis.py`: Analysis of timestamp relationships
- `plot_timestamps.py`: Visualization of timestamp analysis

### Data Files
- `selected_data.csv`: Main data file containing synchronized image, bitmask, and driving information
- Model checkpoints and final models are saved in the output directory 