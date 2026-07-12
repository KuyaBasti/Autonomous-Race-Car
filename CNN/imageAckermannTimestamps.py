import os
import pandas as pd
import numpy as np

# Paths
run_folder = 'data/run_1'
image_folder = os.path.join(run_folder, 'extracted_images')
ackermann_csv_path = os.path.join(run_folder, 'ackermann_output.csv')
output_folder = os.path.join(run_folder, 'output')

# Create output directory if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

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
image_ts_df.to_csv(os.path.join(output_folder, 'image_timestamps.csv'), index=False)
print(f"Saved {len(image_timestamps)} image timestamps to '{output_folder}/image_timestamps.csv'.")

# --- Extract ackermann timestamps ---
try:
    # Read the CSV with explicit encoding and error handling
    ackermann_df = pd.read_csv(
        ackermann_csv_path,
        encoding='utf-8',
        sep=',',
        dtype={'timestamp': float}
    )
    
    # Clean header names
    ackermann_df.columns = ackermann_df.columns.str.strip().str.replace('\ufeff', '')
    
    # Print the first few rows to verify data
    print("\nFirst few rows of ackermann data:")
    print(ackermann_df.head())
    
    # Extract timestamps, convert to seconds, and sort
    ackermann_ts_df = ackermann_df[['timestamp']].copy()
    ackermann_ts_df['timestamp'] = ackermann_ts_df['timestamp'] * 1e-9  # Convert nanoseconds to seconds
    ackermann_ts_df.columns = ['ackermann_timestamp_sec']
    ackermann_ts_df = ackermann_ts_df.sort_values('ackermann_timestamp_sec').reset_index(drop=True)
    
    # Save timestamps
    ackermann_ts_df.to_csv(os.path.join(output_folder, 'ackermann_timestamps.csv'), index=False)
    print(f"\nSaved {len(ackermann_ts_df)} ackermann timestamps to '{output_folder}/ackermann_timestamps.csv'.")
    
    # Print timestamp ranges for verification
    print("\nTimestamp Ranges:")
    print(f"Image timestamps: {image_timestamps[0]:.9f} → {image_timestamps[-1]:.9f}")
    print(f"Ackermann timestamps: {ackermann_ts_df['ackermann_timestamp_sec'].iloc[0]:.9f} → {ackermann_ts_df['ackermann_timestamp_sec'].iloc[-1]:.9f}")
    
except Exception as e:
    print(f"Error reading ackermann data: {str(e)}")
    print("Please check that the file exists and is properly formatted.") 