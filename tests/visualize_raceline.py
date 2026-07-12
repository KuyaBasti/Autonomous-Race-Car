import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

def load_raceline(csv_path):
    """Load raceline data from CSV file."""
    data = np.loadtxt(csv_path, delimiter=',')
    x = data[:, 0]  # x coordinates
    y = data[:, 1]  # y coordinates
    v = data[:, 2]  # velocities
    return x, y, v

def plot_raceline(x, y, v, title="Raceline Visualization"):
    """Create a figure with two subplots: track layout and velocity profile."""
    # Create figure with two subplots
    fig = plt.figure(figsize=(15, 10))
    gs = GridSpec(2, 1, height_ratios=[2, 1])
    
    # Plot track layout
    ax1 = fig.add_subplot(gs[0])
    scatter = ax1.scatter(x, y, c=v, cmap='viridis', s=50)
    ax1.plot(x, y, 'k--', alpha=0.3)  # Connect points with dashed line
    ax1.set_title('Track Layout with Velocity Profile')
    ax1.set_xlabel('X Position (m)')
    ax1.set_ylabel('Y Position (m)')
    ax1.grid(True)
    ax1.axis('equal')  # Equal aspect ratio
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax1)
    cbar.set_label('Velocity (m/s)')
    
    # Plot velocity profile
    ax2 = fig.add_subplot(gs[1])
    distance = np.cumsum(np.sqrt(np.diff(x)**2 + np.diff(y)**2))
    distance = np.insert(distance, 0, 0)  # Add starting point
    ax2.plot(distance, v, 'b-', linewidth=2)
    ax2.set_title('Velocity Profile')
    ax2.set_xlabel('Distance Along Track (m)')
    ax2.set_ylabel('Velocity (m/s)')
    ax2.grid(True)
    
    # Add some statistics
    stats_text = f'Track Length: {distance[-1]:.2f}m\n' \
                f'Max Velocity: {np.max(v):.2f}m/s\n' \
                f'Min Velocity: {np.min(v):.2f}m/s\n' \
                f'Avg Velocity: {np.mean(v):.2f}m/s'
    ax2.text(0.02, 0.98, stats_text,
             transform=ax2.transAxes,
             verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    return fig

def main():
    # Path to the raceline CSV file
    csv_path = "../f1tenth_gym_ros/src/f1tenth_gym_ros/racelines/levine.csv"
    
    # Load and plot the raceline
    x, y, v = load_raceline(csv_path)
    fig = plot_raceline(x, y, v, "Levine Track Raceline")
    
    # Save the figure
    plt.savefig('levine_raceline.png', dpi=300, bbox_inches='tight')
    plt.show()

if __name__ == "__main__":
    main() 