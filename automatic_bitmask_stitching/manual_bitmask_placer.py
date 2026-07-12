#!/usr/bin/env python3

import cv2
import numpy as np
import os
from pathlib import Path
import argparse
import matplotlib.pyplot as plt

class BitmaskPlacer:
    def __init__(self, map_path, bitmask_dir):
        # Load the map
        self.map = cv2.imread(map_path)
        if self.map is None:
            raise ValueError(f"Could not load map from {map_path}")
        
        # Get all bitmask files
        self.bitmask_dir = Path(bitmask_dir)
        self.bitmask_files = sorted([f for f in self.bitmask_dir.glob('*.png')])
        self.current_bitmask_idx = 0
        
        # Initialize placement parameters
        self.scale = 1.0
        self.angle = 0
        self.position = (0, 0)
        self.is_dragging = False
        self.drag_start = None
        self.is_hovering = False
        self.hover_position = (0, 0)
        self.current_bitmask = None
        self.transformed_bitmask = None
        
        # Store placed bitmasks
        self.placed_bitmasks = []
        
        # Create window and set mouse callback
        cv2.namedWindow('Bitmask Placer')
        cv2.setMouseCallback('Bitmask Placer', self.mouse_callback)
        
        # Create status bar
        self.status_height = 60
        self.status_bar = np.zeros((self.status_height, self.map.shape[1], 3), dtype=np.uint8)
        
        # Create trackbars for scale and rotation
        cv2.createTrackbar('Scale', 'Bitmask Placer', 50, 100, self.on_scale_change)
        cv2.createTrackbar('Rotation', 'Bitmask Placer', 0, 360, self.on_rotation_change)
        
        # Generate colors for bitmasks
        self.generate_colors()
        
        # Load first bitmask
        self.load_current_bitmask()
        
    def on_scale_change(self, value):
        """Callback for scale trackbar"""
        self.scale = value / 50.0  # Convert 0-100 to 0-2 range
        self.update_transformed_bitmask()
        
    def on_rotation_change(self, value):
        """Callback for rotation trackbar"""
        self.angle = value
        self.update_transformed_bitmask()
        
    def generate_colors(self):
        """Generate unique colors for each bitmask"""
        self.colors = []
        for i in range(len(self.bitmask_files)):
            # Generate color using HSV colormap for reproducibility
            color = tuple(int(c) for c in np.array(cv2.applyColorMap(
                np.array([[int(255 * i / len(self.bitmask_files))]], dtype=np.uint8), 
                cv2.COLORMAP_HSV))[0,0])
            self.colors.append(color)
        
    def load_current_bitmask(self):
        """Load the current bitmask and apply transformations"""
        if 0 <= self.current_bitmask_idx < len(self.bitmask_files):
            self.current_bitmask = cv2.imread(str(self.bitmask_files[self.current_bitmask_idx]), 
                                            cv2.IMREAD_GRAYSCALE)
            
            # Calculate initial scale to fit on map
            h, w = self.current_bitmask.shape
            map_h, map_w = self.map.shape[:2]
            scale_w = (map_w * 0.3) / w  # Use 30% of map width
            scale_h = (map_h * 0.3) / h  # Use 30% of map height
            self.scale = min(scale_w, scale_h)
            
            # Update trackbar to match initial scale
            cv2.setTrackbarPos('Scale', 'Bitmask Placer', int(self.scale * 50))
            cv2.setTrackbarPos('Rotation', 'Bitmask Placer', self.angle)
            
            self.update_transformed_bitmask()
        else:
            self.current_bitmask = None
            self.transformed_bitmask = None
    
    def update_transformed_bitmask(self):
        """Update the transformed bitmask based on current parameters"""
        if self.current_bitmask is None:
            return
            
        # Get the center of the bitmask
        h, w = self.current_bitmask.shape
        center = (w // 2, h // 2)
        
        # Create rotation matrix
        rotation_matrix = cv2.getRotationMatrix2D(center, self.angle, self.scale)
        
        # Apply rotation and scaling
        self.transformed_bitmask = cv2.warpAffine(
            self.current_bitmask, 
            rotation_matrix, 
            (w, h), 
            flags=cv2.INTER_LINEAR
        )
    
    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events"""
        if event == cv2.EVENT_MOUSEMOVE:
            self.hover_position = (x, y)
            self.is_hovering = True
            
        if event == cv2.EVENT_LBUTTONDOWN:
            self.is_dragging = True
            self.drag_start = (x, y)
            self.position = (x, y)
            self.is_hovering = False
            
        elif event == cv2.EVENT_MOUSEMOVE and self.is_dragging:
            # Calculate the movement delta
            dx = x - self.drag_start[0]
            dy = y - self.drag_start[1]
            # Update position
            self.position = (self.position[0] + dx, self.position[1] + dy)
            # Update drag start
            self.drag_start = (x, y)
            
        elif event == cv2.EVENT_LBUTTONUP:
            self.is_dragging = False
            # Place the bitmask
            if self.transformed_bitmask is not None:
                self.placed_bitmasks.append({
                    'bitmask': self.transformed_bitmask.copy(),
                    'position': self.position,
                    'scale': self.scale,
                    'angle': self.angle,
                    'color': self.colors[self.current_bitmask_idx]
                })
                # Move to next bitmask automatically
                self.current_bitmask_idx = (self.current_bitmask_idx + 1) % len(self.bitmask_files)
                self.load_current_bitmask()
    
    def update_status_bar(self):
        """Update the status bar with current information"""
        self.status_bar.fill(0)
        
        # Add status text
        status_text = [
            f"Bitmask {self.current_bitmask_idx + 1}/{len(self.bitmask_files)}",
            f"Scale: {self.scale:.2f}",
            f"Angle: {self.angle}°",
            "Controls: n/p=next/prev, s=save, u=undo, q=quit"
        ]
        
        # Draw status text
        for i, text in enumerate(status_text):
            y = 20 + i * 15
            cv2.putText(self.status_bar, text, (10, y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
    
    def draw(self):
        """Draw the current state"""
        # Create a copy of the map
        display = self.map.copy()
        
        # Draw all placed bitmasks
        for placed in self.placed_bitmasks:
            h, w = placed['bitmask'].shape
            x, y = placed['position']
            # Create colored bitmask
            colored_bitmask = np.zeros((h, w, 3), dtype=np.uint8)
            mask = placed['bitmask'] > 0
            colored_bitmask[mask] = placed['color']
            # Overlay the bitmask
            self.overlay_bitmask(display, colored_bitmask, (x, y))
        
        # Draw current bitmask if being placed or hovering
        if self.transformed_bitmask is not None and (self.is_dragging or self.is_hovering):
            h, w = self.transformed_bitmask.shape
            x, y = self.position if self.is_dragging else self.hover_position
            
            # Create colored bitmask
            colored_bitmask = np.zeros((h, w, 3), dtype=np.uint8)
            mask = self.transformed_bitmask > 0
            colored_bitmask[mask] = self.colors[self.current_bitmask_idx]
            
            # If hovering, make it semi-transparent
            if self.is_hovering:
                colored_bitmask = cv2.addWeighted(colored_bitmask, 0.5, 
                                                np.zeros_like(colored_bitmask), 0.5, 0)
            
            # Overlay the bitmask
            self.overlay_bitmask(display, colored_bitmask, (x, y))
            
            # Draw outline
            outline = np.zeros((h, w), dtype=np.uint8)
            outline[mask] = 255
            outline = cv2.Canny(outline, 100, 200)
            outline = cv2.dilate(outline, None, iterations=2)
            
            # Calculate the region of interest
            x1, y1 = max(0, x - w//2), max(0, y - h//2)
            x2, y2 = min(display.shape[1], x + w//2), min(display.shape[0], y + h//2)
            
            # Calculate the corresponding region in the outline
            ox1 = max(0, w//2 - x)
            oy1 = max(0, h//2 - y)
            ox2 = min(w, w//2 + (display.shape[1] - x))
            oy2 = min(h, h//2 + (display.shape[0] - y))
            
            # Draw the outline
            outline_region = outline[oy1:oy2, ox1:ox2]
            display[y1:y2, x1:x2][outline_region > 0] = self.colors[self.current_bitmask_idx]
        
        # Update status bar
        self.update_status_bar()
        
        # Combine status bar and display
        combined = np.vstack([self.status_bar, display])
        
        # Show the display
        cv2.imshow('Bitmask Placer', combined)
    
    def overlay_bitmask(self, image, bitmask, position):
        """Overlay a bitmask on the image at the given position"""
        h, w = bitmask.shape[:2]
        x, y = position
        
        # Calculate the region of interest
        x1, y1 = max(0, x - w//2), max(0, y - h//2)
        x2, y2 = min(image.shape[1], x + w//2), min(image.shape[0], y + h//2)
        
        # Calculate the corresponding region in the bitmask
        bx1 = max(0, w//2 - x)
        by1 = max(0, h//2 - y)
        bx2 = min(w, w//2 + (image.shape[1] - x))
        by2 = min(h, h//2 + (image.shape[0] - y))
        
        # Create a mask for the bitmask
        mask = bitmask[by1:by2, bx1:bx2].any(axis=2)
        
        # Overlay the bitmask
        image[y1:y2, x1:x2][mask] = bitmask[by1:by2, bx1:bx2][mask]
    
    def save_result(self, output_path):
        """Save the final result"""
        # Create a copy of the map
        result = self.map.copy()
        
        # Overlay all placed bitmasks
        for placed in self.placed_bitmasks:
            h, w = placed['bitmask'].shape
            x, y = placed['position']
            # Create colored bitmask
            colored_bitmask = np.zeros((h, w, 3), dtype=np.uint8)
            mask = placed['bitmask'] > 0
            colored_bitmask[mask] = placed['color']
            # Overlay the bitmask
            self.overlay_bitmask(result, colored_bitmask, (x, y))
        
        # Save the result
        cv2.imwrite(output_path, result)
        print(f"Saved result to {output_path}")
        
        # Save color key
        self.save_color_key()
    
    def save_color_key(self):
        """Save a color key showing which color corresponds to which bitmask"""
        # Create figure for color key
        fig, ax = plt.subplots(figsize=(8, max(4, len(self.placed_bitmasks)*0.3)))
        
        # Add color patches and labels
        for i, placed in enumerate(self.placed_bitmasks):
            color = tuple(c/255 for c in placed['color'])
            ax.add_patch(plt.Rectangle((0, i), 1, 1, color=color))
            ax.text(1.2, i+0.5, f"Bitmask {i+1}", va='center', fontsize=8)
        
        ax.set_xlim(0, 8)
        ax.set_ylim(0, len(self.placed_bitmasks))
        ax.axis('off')
        plt.tight_layout()
        
        # Save color key
        plt.savefig('color_key.png', dpi=200)
        plt.close()
        print("Color key saved as color_key.png")
    
    def run(self):
        """Main loop"""
        while True:
            self.draw()
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):  # Quit
                break
            elif key == ord('n'):  # Next bitmask
                self.current_bitmask_idx = (self.current_bitmask_idx + 1) % len(self.bitmask_files)
                self.load_current_bitmask()
            elif key == ord('p'):  # Previous bitmask
                self.current_bitmask_idx = (self.current_bitmask_idx - 1) % len(self.bitmask_files)
                self.load_current_bitmask()
            elif key == ord('s'):  # Save result
                self.save_result('manual_stitch_result.png')
            elif key == ord('u'):  # Undo last placement
                if self.placed_bitmasks:
                    self.placed_bitmasks.pop()
                    # Go back to previous bitmask
                    self.current_bitmask_idx = (self.current_bitmask_idx - 1) % len(self.bitmask_files)
                    self.load_current_bitmask()
        
        cv2.destroyAllWindows()

def main():
    parser = argparse.ArgumentParser(description='Manually place bitmasks on a map')
    parser.add_argument('map_path', help='Path to the map image')
    parser.add_argument('bitmask_dir', help='Directory containing bitmask images')
    args = parser.parse_args()
    
    placer = BitmaskPlacer(args.map_path, args.bitmask_dir)
    placer.run()

if __name__ == '__main__':
    main() 