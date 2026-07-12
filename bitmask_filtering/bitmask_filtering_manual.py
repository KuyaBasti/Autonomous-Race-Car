import cv2
import os
import numpy as np
from src.bitmask_filtering import (
    flood_fill_black,
    find_point_inside_track,
    convert_white_to_light_gray,
    convert_black_to_light_gray,
    resize_image,
    convert_border_gray_to_black,
    expand_track,
    filter_blobs
)

# === USER INPUT ===
INPUT_IMAGE_FILENAME = "bitmask_complex.png"  # Just the filename
OUTPUT_IMAGE_FILENAME = "track_180px.png"  # Just the filename
RESIZE_WIDTH = 160
ROTATION_ANGLE = 75  # Rotation angle in degrees (positive for counterclockwise)
PADDING_WIDTH = 20  # Width of padding in pixels
TRACK_PADDING = 0  # Number of pixels to expand the track outward
SHOW_RESULT = True  # Whether to show intermediate steps
# ===================

# Global Variables
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_IMAGE_PATH = os.path.join(ROOT_DIR, "src", "images", INPUT_IMAGE_FILENAME)
OUTPUT_IMAGE_PATH = os.path.join(ROOT_DIR, "outputs", OUTPUT_IMAGE_FILENAME)

# Create output directory if it doesn't exist
os.makedirs(os.path.dirname(OUTPUT_IMAGE_PATH), exist_ok=True)

def print_unique_colors(image, step_name):
    unique_colors = np.unique(image.reshape(-1, image.shape[2]), axis=0)
    print(f"Unique colors after {step_name}: {unique_colors}")

def rotate_image(image, angle):
    """
    Rotate image by specified angle in degrees and crop to remove blank space.
    
    Args:
        image: Input image (numpy array)
        angle: Rotation angle in degrees (positive for counterclockwise)
        
    Returns:
        numpy array: Rotated and cropped image
    """
    print(f"Rotating image by {angle} degrees...")
    # Get image dimensions
    height, width = image.shape[:2]
    
    # Calculate the center of the image
    center = (width // 2, height // 2)
    
    # Get the rotation matrix
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    
    # Calculate new dimensions to fit the rotated image
    cos = np.abs(rotation_matrix[0, 0])
    sin = np.abs(rotation_matrix[0, 1])
    
    # Compute new dimensions
    new_width = int((height * sin) + (width * cos))
    new_height = int((height * cos) + (width * sin))
    
    # Adjust the rotation matrix to take into account translation
    rotation_matrix[0, 2] += (new_width / 2) - center[0]
    rotation_matrix[1, 2] += (new_height / 2) - center[1]
    
    # Perform the rotation with nearest neighbor interpolation to prevent color blending
    rotated = cv2.warpAffine(image, rotation_matrix, (new_width, new_height), 
                            flags=cv2.INTER_NEAREST, 
                            borderMode=cv2.BORDER_CONSTANT, 
                            borderValue=[205, 205, 205])  # Fill new areas with light gray
    
    # Find non-black pixels to determine crop boundaries
    gray = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # Get the bounding rectangle of the largest contour
        x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))
        # Crop the image
        rotated = rotated[y:y+h, x:x+w]
    
    return rotated

def add_padding(image, padding_width):
    """
    Add padding of hex color #CDCDCD to all edges of the image.
    
    Args:
        image: Input image (numpy array)
        padding_width: Width of padding in pixels
        
    Returns:
        numpy array: Image with padding added
    """
    print(f"Adding {padding_width} pixel padding...")
    # Define the padding color (hex #CDCDCD in BGR)
    padding_color = [205, 205, 205]  # BGR format
    
    # Add padding to all sides
    padded_image = cv2.copyMakeBorder(
        image,
        padding_width,  # top
        padding_width,  # bottom
        padding_width,  # left
        padding_width,  # right
        cv2.BORDER_CONSTANT,
        value=padding_color
    )
    
    return padded_image

def preprocess_black_to_white(image):
    # Convert all non-exact-black pixels to white
    result = image.copy()
    black = np.array([0, 0, 0], dtype=np.uint8)
    mask = ~np.all(result == black, axis=-1)
    result[mask] = [255, 255, 255]
    return result

def show_image(image, window_name):
    """Show image if SHOW_RESULT is True"""
    if SHOW_RESULT:
        cv2.imshow(window_name, image)
        cv2.waitKey(0)

def crop_and_reexpand_gray(image, padding_width):
    """
    Crop the gray area around the track until white pixels are found, then re-expand with even padding.
    
    Args:
        image: Input image (numpy array)
        padding_width: Width of padding in pixels
        
    Returns:
        numpy array: Image with evenly padded gray area
    """
    print(f"Cropping and re-expanding gray area with {padding_width} pixel padding...")
    
    # Convert to grayscale for easier processing
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Find the first white pixel from each edge
    height, width = gray.shape
    
    # Find top boundary
    top = 0
    for y in range(height):
        if np.any(gray[y, :] == 255):  # Found white pixel
            top = y
            break
    
    # Find bottom boundary
    bottom = height - 1
    for y in range(height-1, -1, -1):
        if np.any(gray[y, :] == 255):  # Found white pixel
            bottom = y
            break
    
    # Find left boundary
    left = 0
    for x in range(width):
        if np.any(gray[:, x] == 255):  # Found white pixel
            left = x
            break
    
    # Find right boundary
    right = width - 1
    for x in range(width-1, -1, -1):
        if np.any(gray[:, x] == 255):  # Found white pixel
            right = x
            break
    
    # Crop the image to the boundaries
    cropped = image[top:bottom+1, left:right+1]
    
    # Show the cropped image
    show_image(cropped, "Step 9a: After Cropping Gray Area")
    
    # Add padding to all sides
    padded = cv2.copyMakeBorder(
        cropped,
        padding_width,  # top
        padding_width,  # bottom
        padding_width,  # left
        padding_width,  # right
        cv2.BORDER_CONSTANT,
        value=[205, 205, 205]  # Light gray padding
    )
    
    # Show the re-expanded image
    show_image(padded, "Step 9b: After Re-expanding Gray Area")
    
    return padded

def main():
    try:
        # Load the input image
        if not os.path.exists(INPUT_IMAGE_PATH):
            raise FileNotFoundError(f"Input image not found at: {INPUT_IMAGE_PATH}")
            
        image = cv2.imread(INPUT_IMAGE_PATH)
        if image is None:
            raise ValueError(f"Could not read image at: {INPUT_IMAGE_PATH}")
        
        print_unique_colors(image, "loading input image")
        # Step 1: Preprocess: convert all non-exact-black pixels to white
        image = preprocess_black_to_white(image)
        print_unique_colors(image, "step 1 preprocess non-black to white")
        
        # Step 2: Flood fill from (1,1) to convert connected black pixels to light gray
        print("\nStep 2: Flood filling from (1,1)...")
        filled_image = flood_fill_black(image, 1, 1, new_color=[205, 205, 205])
        print_unique_colors(filled_image, "step 2 flood fill")
        show_image(filled_image, "Step 2: After Flood Fill")
        
        # Step 3: Find a point inside the track
        print("\nStep 3: Finding point inside track...")
        point = find_point_inside_track(filled_image)
        if point is None:
            print("Error: Could not find a point inside the track")
            return
        
        # Visualize the selected point
        point_image = filled_image.copy()
        cv2.circle(point_image, point, 5, (0, 0, 255), -1)  # Red dot
        print_unique_colors(point_image, "step 3 visualize point")
        show_image(point_image, "Step 3: Selected Point Inside Track")
        
        # Step 4: Convert white pixels to light gray
        print("\nStep 4: Converting white pixels to light gray...")
        gray_image = convert_white_to_light_gray(filled_image)
        print_unique_colors(gray_image, "step 4 white to gray")
        show_image(gray_image, "Step 4: After White to Gray Conversion")
        
        # Step 5: Flood fill from the selected point
        print("\nStep 5: Flood filling from selected point...")
        filled_image = flood_fill_black(gray_image, point[0], point[1])
        print_unique_colors(filled_image, "step 5 flood fill from point")
        show_image(filled_image, "Step 5: After Flood Fill from Selected Point")
        
        # Step 6: Resize image to 160px width
        print("\nStep 6: Resizing image...")
        resized_image = resize_image(filled_image, 160)
        print_unique_colors(resized_image, "step 6 resize")
        show_image(resized_image, "Step 6: After Resizing")
        
        # Step 7: Rotate image 75 degrees clockwise
        print("\nStep 7: Rotating image...")
        rotated_image = rotate_image(resized_image, 75)
        print_unique_colors(rotated_image, "step 7 rotate")
        show_image(rotated_image, "Step 7: After Rotation")
        
        # Step 8: Convert remaining black pixels to light gray
        print("\nStep 8: Converting remaining black pixels to light gray...")
        final_gray_image = convert_black_to_light_gray(rotated_image)
        print_unique_colors(final_gray_image, "step 8 black to gray")
        show_image(final_gray_image, "Step 8: After Black to Gray Conversion")
        
        # Step 9: Crop and re-expand gray area
        print("\nStep 9: Cropping and re-expanding gray area...")
        cropped_expanded = crop_and_reexpand_gray(final_gray_image, PADDING_WIDTH)
        print_unique_colors(cropped_expanded, "step 9 crop and re-expand")
        
        # Step 10: Expand track by 5 pixels
        print("\nStep 10: Expanding track...")
        expanded_image = expand_track(cropped_expanded, 5)
        print_unique_colors(expanded_image, "step 10 expand track")
        show_image(expanded_image, "Step 10: After Track Expansion")
        
        # Step 11: Add 5 pixel padding
        print("\nStep 11: Adding padding...")
        padded_image = add_padding(expanded_image, 5)
        print_unique_colors(padded_image, "step 11 add padding")
        show_image(padded_image, "Step 11: After Adding Padding")
        
        # Step 12: Filter out isolated black pixels
        print("\nStep 12: Filtering isolated black pixels...")
        final_image = filter_blobs(padded_image)
        print_unique_colors(final_image, "step 12 filter blobs (final)")
        show_image(final_image, "Step 12: Final Result")
        
        # Save only the final result
        output_path = OUTPUT_IMAGE_PATH.replace(".png", f"_filled_{ROTATION_ANGLE}deg.png")
        cv2.imwrite(output_path, final_image)
        print(f"\nFinal image saved to: {output_path}")
        
        # Close all windows
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return

if __name__ == "__main__":
    main() 