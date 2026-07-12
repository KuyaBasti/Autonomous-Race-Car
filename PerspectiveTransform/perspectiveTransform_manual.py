import cv2
import numpy as np
import os
from pathlib import Path

# ==== USER INPUT WITH DEFAULTS ====
default_car_path = "./PerspectiveTransform/src/config/track_complex.jpg"
default_bev_path = "./PerspectiveTransform/src/config/track_complex_config.jpg"
default_input_dir = "./PerspectiveTransform/src/inputs"
default_output_dir = "./PerspectiveTransform/output/transformed_images"

car_input = input(f"Enter car-view image path [default: {default_car_path}]: ").strip()
bev_input = input(f"Enter BEV image path [default: {default_bev_path}]: ").strip()
input_dir = input(f"Enter input directory path [default: {default_input_dir}]: ").strip()
output_dir = input(f"Enter output directory path [default: {default_output_dir}]: ").strip()

CAR_IMAGE_PATH = car_input if car_input else default_car_path
BEV_IMAGE_PATH = bev_input if bev_input else default_bev_path
INPUT_DIR = input_dir if input_dir else default_input_dir
OUTPUT_DIR = output_dir if output_dir else default_output_dir
# ==================================

# === Load and check images ===
car_img = cv2.imread(CAR_IMAGE_PATH)
bev_img = cv2.imread(BEV_IMAGE_PATH)

if car_img is None or bev_img is None:
    raise FileNotFoundError("One or both images not found. Check your paths.")

# === Resize both images to same size ===
resize_width = min(car_img.shape[1], bev_img.shape[1])
resize_height = min(car_img.shape[0], bev_img.shape[0])
target_size = (resize_width, resize_height)

car_resized = cv2.resize(car_img, target_size)
bev_resized = cv2.resize(bev_img, target_size)

print(f"Both images resized to: {target_size}")

# === Point collection logic ===
def get_four_points(window_name, image):
    clone = image.copy()
    points = []

    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and len(points) < 4:
            points.append((x, y))
            cv2.circle(clone, (x, y), 5, (0, 255, 0), -1)
            cv2.putText(clone, f"{len(points)}", (x+5, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)
            cv2.imshow(window_name, clone)

    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, mouse_callback)

    print(f"Please click 4 points on the '{window_name}' window.")
    while len(points) < 4:
        cv2.imshow(window_name, clone)
        if cv2.waitKey(1) & 0xFF == 27:  # Esc to cancel
            break

    cv2.destroyWindow(window_name)
    return points

# === Step 1: Select source points from CAR image ===
car_points = get_four_points("1️⃣ Car View (Resized) - Click Source Points", car_resized)

# === Step 2: Select destination points from BEV image ===
bev_points = get_four_points("2️⃣ BEV View (Resized) - Click Destination Points", bev_resized)

# === Compute homography and warp ===
src_pts = np.array(car_points, dtype=np.float32)  # FROM
dst_pts = np.array(bev_points, dtype=np.float32)  # TO

H, status = cv2.findHomography(src_pts, dst_pts)
print("\nComputed Homography Matrix:")
print(H)

# Get reference warped image
warped_ref = cv2.warpPerspective(car_resized, H, target_size)
ref_size = warped_ref.shape[:2]  # Get height and width of reference

# === Process all images in input directory ===
print(f"\nProcessing images from: {INPUT_DIR}")
print(f"Saving transformed images to: {OUTPUT_DIR}")

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Process each image in the input directory
image_count = 0
success_count = 0

for image_path in Path(INPUT_DIR).glob("*"):
    if image_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
        image_count += 1
        print(f"\nProcessing {image_path.name}...")
        
        # Load image
        img = cv2.imread(str(image_path))
        if img is None:
            print(f"Failed to load image: {image_path.name}")
            continue
            
        # Resize to target size
        img_resized = cv2.resize(img, target_size)
        
        # Apply perspective transform
        warped_img = cv2.warpPerspective(img_resized, H, target_size)
        
        # Save transformed image
        #output_path = Path(OUTPUT_DIR) / f"transformed_{image_path.name}"
        output_path = Path(OUTPUT_DIR) / f"{image_path.name}"
        cv2.imwrite(str(output_path), warped_img)
        success_count += 1
        print(f"Saved transformed image to: {output_path}")

print(f"\nProcessing complete!")
print(f"Total images found: {image_count}")
print(f"Successfully transformed: {success_count}")
print(f"Failed to process: {image_count - success_count}")

# Display and save reference warped image
cv2.imshow("Reference Warped Image", warped_ref)
cv2.imwrite(os.path.join(OUTPUT_DIR, "reference_warped.png"), warped_ref)
print("\nReference warped image saved as reference_warped.png")

cv2.waitKey(0)
cv2.destroyAllWindows() 