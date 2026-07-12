import cv2
import pandas as pd
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import numpy as np

class ImageEvaluator:
    def __init__(self, root):
        self.root = root
        self.root.title("CNN Image Evaluator")
        
        # Load the synchronized data and set all keep values to 'no'
        self.data = pd.read_csv('data/run_1/output/interpolated_synced_images_with_commands.csv')
        self.data['keep'] = 'yes'  # Set all keep values to 'no' by default
        self.current_index = 0
        
        # Create main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create frames for original image and mask
        self.image_frame = ttk.LabelFrame(self.main_frame, text="Original Image", padding="5")
        self.image_frame.grid(row=0, column=0, padx=5, pady=5)
        
        self.mask_frame = ttk.LabelFrame(self.main_frame, text="Bitmask", padding="5")
        self.mask_frame.grid(row=0, column=1, padx=5, pady=5)
        
        # Image displays
        self.image_label = ttk.Label(self.image_frame)
        self.image_label.grid(row=0, column=0, padx=5, pady=5)
        
        self.mask_label = ttk.Label(self.mask_frame)
        self.mask_label.grid(row=0, column=0, padx=5, pady=5)
        
        # Command information
        self.command_frame = ttk.LabelFrame(self.main_frame, text="Command Information", padding="5")
        self.command_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        self.steering_label = ttk.Label(self.command_frame, text="Steering Angle:")
        self.steering_label.grid(row=0, column=0, sticky=tk.W)
        self.steering_value = ttk.Label(self.command_frame, text="")
        self.steering_value.grid(row=0, column=1, sticky=tk.W)
        
        self.speed_label = ttk.Label(self.command_frame, text="Speed:")
        self.speed_label.grid(row=1, column=0, sticky=tk.W)
        self.speed_value = ttk.Label(self.command_frame, text="")
        self.speed_value.grid(row=1, column=1, sticky=tk.W)
        
        # Navigation buttons
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.prev_button = ttk.Button(self.button_frame, text="Previous", command=self.prev_image)
        self.prev_button.grid(row=0, column=0, padx=5)
        
        self.next_button = ttk.Button(self.button_frame, text="Next", command=self.next_image)
        self.next_button.grid(row=0, column=1, padx=5)
        
        # Keep/Reject buttons
        self.keep_button = ttk.Button(self.button_frame, text="Keep", command=lambda: self.mark_image(True))
        self.keep_button.grid(row=0, column=2, padx=5)
        
        self.reject_button = ttk.Button(self.button_frame, text="Reject", command=lambda: self.mark_image(False))
        self.reject_button.grid(row=0, column=3, padx=5)
        
        # Status label
        self.status_label = ttk.Label(self.main_frame, text="")
        self.status_label.grid(row=3, column=0, columnspan=2, pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(self.main_frame, length=300, mode='determinate', variable=self.progress_var)
        self.progress.grid(row=4, column=0, columnspan=2, pady=5)
        
        # Save button
        self.save_button = ttk.Button(self.main_frame, text="Save Changes", command=self.save_changes)
        self.save_button.grid(row=5, column=0, columnspan=2, pady=5)
        
        # Bind keyboard shortcuts
        self.root.bind('<Left>', lambda e: self.prev_image())
        self.root.bind('<Right>', lambda e: self.next_image())
        self.root.bind('k', lambda e: self.mark_image(True))
        self.root.bind('r', lambda e: self.mark_image(False))
        self.root.bind('<Control-s>', lambda e: self.save_changes())
        
        # Load first image
        self.load_current_image()
        
    def load_current_image(self):
        # Get current image data
        current_data = self.data.iloc[self.current_index]
        image_path = os.path.join('data/run_1/extracted_images', current_data['image'])
        
        # Load and resize original image
        img = cv2.imread(image_path)
        if img is None:
            self.status_label.config(text=f"Error loading image: {image_path}")
            return
            
        # Resize image to fit screen while maintaining aspect ratio
        height, width = img.shape[:2]
        max_height = 400
        max_width = 600
        
        scale = min(max_width/width, max_height/height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        img = cv2.resize(img, (new_width, new_height))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Convert to PhotoImage
        self.photo = ImageTk.PhotoImage(image=Image.fromarray(img))
        self.image_label.config(image=self.photo)
        
        # Try to load corresponding mask
        mask_path = os.path.join('data/run_1/masks', current_data['image'].replace('.png', '_mask.png'))
        if os.path.exists(mask_path):
            mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
            if mask is not None:
                # Resize mask to match image size
                mask = cv2.resize(mask, (new_width, new_height))
                # Convert to RGB for display
                mask_rgb = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
                self.mask_photo = ImageTk.PhotoImage(image=Image.fromarray(mask_rgb))
                self.mask_label.config(image=self.mask_photo)
            else:
                self.mask_label.config(image='', text="Error loading mask")
        else:
            self.mask_label.config(image='', text="No mask available")
        
        # Update command information
        self.steering_value.config(text=f"{current_data['steering_angle']:.3f}")
        self.speed_value.config(text=f"{current_data['speed']:.3f}")
        
        # Update status
        self.status_label.config(text=f"Image {self.current_index + 1} of {len(self.data)} - Status: {current_data['keep']}")
        
        # Update progress
        self.progress_var.set((self.current_index + 1) / len(self.data) * 100)
        
    def prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.load_current_image()
            
    def next_image(self):
        if self.current_index < len(self.data) - 1:
            self.current_index += 1
            self.load_current_image()
            
    def mark_image(self, keep):
        self.data.iloc[self.current_index, self.data.columns.get_loc('keep')] = 'yes' if keep else 'no'
        self.status_label.config(text=f"Image {self.current_index + 1} of {len(self.data)} - Status: {'yes' if keep else 'no'}")
        
    def save_changes(self):
        self.data.to_csv('data/run_1/output/interpolated_synced_images_with_commands.csv', index=False)
        self.status_label.config(text="Changes saved successfully!")

def main():
    root = tk.Tk()
    app = ImageEvaluator(root)
    root.mainloop()

if __name__ == "__main__":
    main() 