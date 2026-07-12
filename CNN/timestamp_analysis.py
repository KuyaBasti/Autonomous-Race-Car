import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import os

# Paths
run_folder = 'data/run_1'
output_folder = os.path.join(run_folder, 'output')
visualizations_folder = os.path.join(output_folder, 'visualizations')

def load_timestamps(file_path, column_name):
    """Load and return timestamps from a CSV file."""
    df = pd.read_csv(file_path)
    return df[column_name].values

def analyze_timestamps(timestamps, name):
    """Analyze timestamp data and return statistics."""
    # Calculate time differences between consecutive timestamps
    diffs = np.diff(timestamps)
    
    # Calculate total duration
    total_duration = timestamps[-1] - timestamps[0]
    
    # Convert to datetime for human-readable format
    start_time = datetime.fromtimestamp(timestamps[0])
    end_time = datetime.fromtimestamp(timestamps[-1])
    
    # Calculate statistics
    stats = {
        'Total Duration': f"{total_duration:.3f} seconds",
        'Start Time': start_time.strftime('%Y-%m-%d %H:%M:%S.%f'),
        'End Time': end_time.strftime('%Y-%m-%d %H:%M:%S.%f'),
        'Number of Timestamps': len(timestamps),
        'Average Interval': f"{np.mean(diffs):.3f} seconds",
        'Median Interval': f"{np.median(diffs):.3f} seconds",
        'Min Interval': f"{np.min(diffs):.3f} seconds",
        'Max Interval': f"{np.max(diffs):.3f} seconds",
        'Standard Deviation': f"{np.std(diffs):.3f} seconds",
        '25th Percentile': f"{np.percentile(diffs, 25):.3f} seconds",
        '75th Percentile': f"{np.percentile(diffs, 75):.3f} seconds"
    }
    
    # Print statistics
    print(f"\n{name} Timestamp Analysis:")
    print("=" * 50)
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    return diffs, stats

def plot_distributions(image_diffs, ackermann_diffs):
    """Create plots of the timestamp distributions."""
    # Create output directory if it doesn't exist
    os.makedirs(visualizations_folder, exist_ok=True)
    
    plt.figure(figsize=(15, 10))
    
    # Plot 1: Interval Distribution
    plt.subplot(2, 2, 1)
    plt.hist(image_diffs, bins=50, alpha=0.5, label='Images')
    plt.hist(ackermann_diffs, bins=50, alpha=0.5, label='Ackermann')
    plt.title('Distribution of Time Intervals')
    plt.xlabel('Time Interval (seconds)')
    plt.ylabel('Frequency')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot 2: Cumulative Distribution
    plt.subplot(2, 2, 2)
    plt.hist(image_diffs, bins=50, alpha=0.5, label='Images', cumulative=True, density=True)
    plt.hist(ackermann_diffs, bins=50, alpha=0.5, label='Ackermann', cumulative=True, density=True)
    plt.title('Cumulative Distribution of Time Intervals')
    plt.xlabel('Time Interval (seconds)')
    plt.ylabel('Cumulative Probability')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Plot 3: Box Plot
    plt.subplot(2, 2, 3)
    plt.boxplot([image_diffs, ackermann_diffs], labels=['Images', 'Ackermann'])
    plt.title('Box Plot of Time Intervals')
    plt.ylabel('Time Interval (seconds)')
    plt.grid(True, alpha=0.3)
    
    # Plot 4: Scatter Plot of Intervals
    plt.subplot(2, 2, 4)
    plt.scatter(range(len(image_diffs)), image_diffs, alpha=0.5, label='Images', s=10)
    plt.scatter(range(len(ackermann_diffs)), ackermann_diffs, alpha=0.5, label='Ackermann', s=10)
    plt.title('Time Intervals Over Time')
    plt.xlabel('Interval Index')
    plt.ylabel('Time Interval (seconds)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(visualizations_folder, 'timestamp_analysis.png'), dpi=300, bbox_inches='tight')
    print(f"\nVisualization saved as '{visualizations_folder}/timestamp_analysis.png'")

def main():
    # Load timestamps
    image_timestamps = load_timestamps(os.path.join(output_folder, 'image_timestamps.csv'), 'image_timestamp_sec')
    ackermann_timestamps = load_timestamps(os.path.join(output_folder, 'ackermann_timestamps.csv'), 'ackermann_timestamp_sec')
    
    # Analyze timestamps
    image_diffs, image_stats = analyze_timestamps(image_timestamps, 'Image')
    ackermann_diffs, ackermann_stats = analyze_timestamps(ackermann_timestamps, 'Ackermann')
    
    # Calculate overlap statistics
    overlap_start = max(image_timestamps[0], ackermann_timestamps[0])
    overlap_end = min(image_timestamps[-1], ackermann_timestamps[-1])
    overlap_duration = overlap_end - overlap_start
    
    print("\nOverlap Analysis:")
    print("=" * 50)
    print(f"Overlap Duration: {overlap_duration:.3f} seconds")
    print(f"Overlap Start: {datetime.fromtimestamp(overlap_start).strftime('%Y-%m-%d %H:%M:%S.%f')}")
    print(f"Overlap End: {datetime.fromtimestamp(overlap_end).strftime('%Y-%m-%d %H:%M:%S.%f')}")
    
    # Calculate coverage
    image_coverage = (overlap_duration / (image_timestamps[-1] - image_timestamps[0])) * 100
    ackermann_coverage = (overlap_duration / (ackermann_timestamps[-1] - ackermann_timestamps[0])) * 100
    
    print(f"\nCoverage Analysis:")
    print(f"Image Data Coverage: {image_coverage:.1f}%")
    print(f"Ackermann Data Coverage: {ackermann_coverage:.1f}%")
    
    # Create visualizations
    plot_distributions(image_diffs, ackermann_diffs)

if __name__ == "__main__":
    main() 