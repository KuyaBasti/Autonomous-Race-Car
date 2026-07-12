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
INPUT_IMAGE_FILENAME = "track_square.png"  # Just the filename
OUTPUT_IMAGE_FILENAME = "track_square.png"  # Just the filename
PADDING_WIDTH = 20  # Width of padding in pixels
TRACK_PADDING = 0  # Number of pixels to expand the track outward
SHOW_RESULT = False  # Whether to show intermediate steps
isRGB = False  # Whether to save final image in RGB format (True) or 8-bit format (False)

# New user inputs for world map alignment
WORLD_MAP_PATH = "WORLDMAP.png"  # Path to the world map image
# ===================

# Global Variables
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_IMAGE_PATH = os.path.join(ROOT_DIR, "src", "images", INPUT_IMAGE_FILENAME)
OUTPUT_IMAGE_PATH = os.path.join(ROOT_DIR, "outputs", OUTPUT_IMAGE_FILENAME)

# Create output directory if it doesn't exist
os.makedirs(os.path.dirname(OUTPUT_IMAGE_PATH), exist_ok=True)

def get_points_from_image(window_name, image, num_points=2):
    print(f"Please click {num_points} points on the window: {window_name}")
    points = []
    clone = image.copy()
    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if len(points) < num_points:
                points.append((x, y))
                cv2.circle(clone, (x, y), 5, (0, 0, 255), -1)
                cv2.imshow(window_name, clone)
    cv2.imshow(window_name, clone)
    cv2.setMouseCallback(window_name, mouse_callback)
    while len(points) < num_points:
        if cv2.waitKey(1) & 0xFF == 27:  # ESC to exit
            print("Selection cancelled.")
            cv2.destroyWindow(window_name)
            return None
    cv2.destroyWindow(window_name)
    return points

def compute_similarity_transform(src_pts, dst_pts):
    """
    Compute scale and rotation (in degrees) to align src_pts to dst_pts.
    src_pts, dst_pts: list of two (x, y) tuples
    Returns: scale, rotation_angle (degrees), translation (dx, dy)
    """
    src_pts = np.array(src_pts, dtype=np.float32)
    dst_pts = np.array(dst_pts, dtype=np.float32)
    # Vectors between the two points
    v1 = src_pts[1] - src_pts[0]
    v2 = dst_pts[1] - dst_pts[0]
    # Scale is the ratio of vector lengths
    scale = np.linalg.norm(v2) / np.linalg.norm(v1)
    # Angle between vectors
    angle1 = np.arctan2(v1[1], v1[0])
    angle2 = np.arctan2(v2[1], v2[0])
    rotation_angle = np.degrees(angle2 - angle1)
    # After scaling and rotation, compute translation
    # Rotate and scale src_pts[0] to align with dst_pts[0]
    theta = angle2 - angle1
    R = np.array([
        [np.cos(theta), -np.sin(theta)],
        [np.sin(theta),  np.cos(theta)]
    ])
    src0_transformed = scale * (R @ (src_pts[0]))
    translation = dst_pts[0] - src0_transformed
    return scale, rotation_angle, translation

def preprocess_black_to_white(image):
    # Convert all non-exact-black pixels to white
    result = image.copy()
    black = np.array([0, 0, 0], dtype=np.uint8)
    mask = ~np.all(result == black, axis=-1)
    result[mask] = [255, 255, 255]
    return result

def print_unique_colors(image, step_name):
    unique_colors = np.unique(image.reshape(-1, image.shape[2]), axis=0)
    print(f"Unique colors after {step_name}: {unique_colors}")

def show_image(image, window_name):
    """Show image if SHOW_RESULT is True or if it's the final alignment"""
    if SHOW_RESULT or window_name == "Final Alignment":
        cv2.imshow(window_name, image)
        cv2.waitKey(0)
        cv2.destroyWindow(window_name)

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

def add_padding(image, padding_width):
    """
    Add padding around the image.
    
    Args:
        image: Input image
        padding_width: Width of padding to add
        
    Returns:
        Padded image
    """
    # Create a new image with padding
    h, w = image.shape[:2]
    padded = np.full((h + 2*padding_width, w + 2*padding_width, 3), [205, 205, 205], dtype=np.uint8)
    
    # Copy the original image into the center
    padded[padding_width:padding_width+h, padding_width:padding_width+w] = image
    
    return padded

def transform_points(points, original_shape, target_shape, angle=0, padding=0):
    """
    Transform points through resizing, rotation, and padding operations.
    
    Args:
        points: List of (x, y) tuples
        original_shape: (height, width) of original image
        target_shape: (height, width) of target image
        angle: Rotation angle in degrees
        padding: Padding width added to the image
        
    Returns:
        List of transformed (x, y) tuples
    """
    transformed_points = []
    orig_h, orig_w = original_shape
    target_h, target_w = target_shape
    
    # Scale factors
    scale_x = target_w / orig_w
    scale_y = target_h / orig_h
    
    for x, y in points:
        # Scale the points
        scaled_x = x * scale_x
        scaled_y = y * scale_y
        
        # Rotate around center
        if angle != 0:
            center_x = target_w / 2
            center_y = target_h / 2
            
            # Translate to origin
            dx = scaled_x - center_x
            dy = scaled_y - center_y
            
            # Rotate
            angle_rad = np.radians(angle)
            rotated_x = dx * np.cos(angle_rad) - dy * np.sin(angle_rad)
            rotated_y = dx * np.sin(angle_rad) + dy * np.cos(angle_rad)
            
            # Translate back
            scaled_x = rotated_x + center_x
            scaled_y = rotated_y + center_y
        
        # Add padding offset
        scaled_x += padding
        scaled_y += padding
        
        transformed_points.append((int(scaled_x), int(scaled_y)))
    
    return transformed_points

def find_point_inside_track(image):
    """
    Find a point that is inside the track (black pixel surrounded by white).
    
    Args:
        image: Input image
        
    Returns:
        Tuple of (x, y) coordinates of a point inside the track
    """
    print("Searching for point inside track...")
    h, w = image.shape[:2]
    
    # Try multiple starting points
    start_points = [
        (w//4, h//4),    # Top-left quadrant
        (w//4, 3*h//4),  # Bottom-left quadrant
        (3*w//4, h//4),  # Top-right quadrant
        (3*w//4, 3*h//4) # Bottom-right quadrant
    ]
    
    for start_x, start_y in start_points:
        # Search horizontally
        for y in range(start_y, h):
            for x in range(start_x, w):
                if np.array_equal(image[y, x], [255, 255, 255]):  # Found white pixel
                    # Check if next pixel is black
                    if x + 1 < w and np.array_equal(image[y, x + 1], [0, 0, 0]):
                        print(f"Found point inside track at: ({x + 1}, {y})")
                        return (x + 1, y)
    
    # If no point found with first strategy, try scanning from edges
    for y in range(h):
        # Scan from left
        for x in range(w):
            if np.array_equal(image[y, x], [255, 255, 255]):
                if x + 1 < w and np.array_equal(image[y, x + 1], [0, 0, 0]):
                    print(f"Found point inside track at: ({x + 1}, {y})")
                    return (x + 1, y)
        
        # Scan from right
        for x in range(w-1, -1, -1):
            if np.array_equal(image[y, x], [255, 255, 255]):
                if x - 1 >= 0 and np.array_equal(image[y, x - 1], [0, 0, 0]):
                    print(f"Found point inside track at: ({x - 1}, {y})")
                    return (x - 1, y)
    
    raise ValueError("Could not find a point inside the track")

def show_world_map_with_points(world_map, points, window_name="World Map with Points"):
    """Show world map with points marked"""
    if not SHOW_RESULT:
        return
    vis = world_map.copy()
    for point in points:
        cv2.circle(vis, point, 5, (255, 0, 0), -1)  # Both points in blue
    cv2.imshow(window_name, vis)

def wait_for_key():
    """Wait for a key press and close all windows"""
    if SHOW_RESULT:
        cv2.waitKey(0)
        cv2.destroyAllWindows()

def main():
    print("\n=== Starting Image Processing ===")
    # Load the bitmask image
    if not os.path.exists(INPUT_IMAGE_PATH):
        print(f"Bitmask image not found at: {INPUT_IMAGE_PATH}")
        return
    bitmask = cv2.imread(INPUT_IMAGE_PATH)
    if bitmask is None:
        print(f"Could not read bitmask image at: {INPUT_IMAGE_PATH}")
        return
    print(f"Loaded bitmask image: {INPUT_IMAGE_PATH} (shape: {bitmask.shape})")

    # Load the world map
    world_map_full_path = os.path.join(ROOT_DIR, "src", "images", WORLD_MAP_PATH)
    if not os.path.exists(world_map_full_path):
        print(f"World map not found at: {world_map_full_path}")
        return
    world_map = cv2.imread(world_map_full_path)
    if world_map is None:
        print(f"Could not read world map at: {world_map_full_path}")
        return
    print(f"Loaded world map: {world_map_full_path} (shape: {world_map.shape})")

    print("\n=== Point Selection ===")
    # Let user select points on bitmask
    bitmask_points = get_points_from_image("Select 2 Points on Bitmask", bitmask, 2)
    if bitmask_points is None:
        print("Bitmask point selection cancelled.")
        return
    print(f"Selected bitmask points: {bitmask_points}")

    # Let user select points on world map
    world_map_points = get_points_from_image("Select 2 Points on World Map", world_map, 2)
    if world_map_points is None:
        print("World map point selection cancelled.")
        return
    print(f"Selected world map points: {world_map_points}")

    print("\n=== Computing Transformations ===")
    # Show world map with selected points
    show_world_map_with_points(world_map, world_map_points, "Step 0: World Map with Selected Points")

    # Compute similarity transform (we'll use this for processing and alignment)
    scale, rotation_angle, translation = compute_similarity_transform(bitmask_points, world_map_points)
    print(f"Computed scale: {scale}")
    print(f"Computed rotation (degrees): {rotation_angle}")
    print(f"Computed translation (dx, dy): {translation}")

    # Invert the rotation angle
    rotation_angle = -rotation_angle
    print(f"Inverted rotation angle (degrees): {rotation_angle}")

    print("\n=== Starting Image Processing Steps ===")
    # Initialize points tracking
    current_points = bitmask_points.copy()
    current_shape = bitmask.shape[:2]

    print("\nStep 1/12: Preprocessing...")
    # Step 1: Preprocess: convert all non-exact-black pixels to white
    image = preprocess_black_to_white(bitmask)
    print_unique_colors(image, "step 1 preprocess non-black to white")
    show_world_map_with_points(world_map, world_map_points, "Step 1: World Map with Points")
    
    # Show points on preprocessed image
    vis_image = image.copy()
    for point in current_points:
        cv2.circle(vis_image, point, 5, (0, 0, 255), -1)
    show_image(vis_image, "Step 1: After Preprocessing with Points")
    if SHOW_RESULT:
        wait_for_key()

    print("\nStep 2/12: Flood filling from (1,1)...")
    # Step 2: Flood fill from (1,1) to convert connected black pixels to light gray
    filled_image = flood_fill_black(image, 1, 1, new_color=[205, 205, 205])
    print_unique_colors(filled_image, "step 2 flood fill")
    show_world_map_with_points(world_map, world_map_points, "Step 2: World Map with Points")
    
    # Show points on flood filled image
    vis_image = filled_image.copy()
    for point in current_points:
        cv2.circle(vis_image, point, 5, (0, 0, 255), -1)
    show_image(vis_image, "Step 2: After Flood Fill with Points")
    if SHOW_RESULT:
        wait_for_key()

    print("\nStep 3/12: Finding point inside track...")
    # Step 3: Find a point inside the track
    point = find_point_inside_track(filled_image)
    if point is None:
        print("Error: Could not find a point inside the track")
        return

    # Visualize the selected point and tracked points
    point_image = filled_image.copy()
    cv2.circle(point_image, point, 5, (0, 0, 255), -1)  # Red dot for track point
    for p in current_points:
        cv2.circle(point_image, p, 5, (255, 0, 0), -1)  # Blue dots for tracked points
    print_unique_colors(point_image, "step 3 visualize point")
    show_image(point_image, "Step 3: Selected Point and Tracked Points")
    show_world_map_with_points(world_map, world_map_points, "Step 3: World Map with Points")
    if SHOW_RESULT:
        wait_for_key()
    
    print("\nStep 4/12: Converting white pixels to light gray...")
    # Step 4: Convert white pixels to light gray
    gray_image = convert_white_to_light_gray(filled_image)
    print_unique_colors(gray_image, "step 4 white to gray")
    
    # Show points on gray image
    vis_image = gray_image.copy()
    for p in current_points:
        cv2.circle(vis_image, p, 5, (0, 0, 255), -1)
    show_image(vis_image, "Step 4: After White to Gray with Points")
    show_world_map_with_points(world_map, world_map_points, "Step 4: World Map with Points")
    if SHOW_RESULT:
        wait_for_key()

    print("\nStep 5/12: Flood filling from selected point...")
    # Step 5: Flood fill from the selected point
    filled_image = flood_fill_black(gray_image, point[0], point[1])
    print_unique_colors(filled_image, "step 5 flood fill from point")
    
    # Show points on filled image
    vis_image = filled_image.copy()
    for p in current_points:
        cv2.circle(vis_image, p, 5, (0, 0, 255), -1)
    show_image(vis_image, "Step 5: After Flood Fill with Points")
    show_world_map_with_points(world_map, world_map_points, "Step 5: World Map with Points")
    if SHOW_RESULT:
        wait_for_key()

    print("\nStep 6/12: Resizing image...")
    # Step 6: Resize image using computed scale (width)
    h, w = filled_image.shape[:2]
    new_width = int(w * scale)
    new_height = int(h * scale)
    resized_image = cv2.resize(filled_image, (new_width, new_height), interpolation=cv2.INTER_NEAREST)
    print_unique_colors(resized_image, "step 6 resize")
    
    # Update points for resize
    scale_x = new_width / w
    scale_y = new_height / h
    current_points = [(int(x * scale_x), int(y * scale_y)) for x, y in current_points]
    current_shape = (new_height, new_width)
    
    # Show points on resized image
    vis_image = resized_image.copy()
    for p in current_points:
        cv2.circle(vis_image, p, 5, (0, 0, 255), -1)
    show_image(vis_image, "Step 6: After Resizing with Points")
    show_world_map_with_points(world_map, world_map_points, "Step 6: World Map with Points")
    if SHOW_RESULT:
        wait_for_key()

    print("\nStep 7/12: Rotating image...")
    # Step 7: Rotate image using computed rotation angle
    height, width = resized_image.shape[:2]
    center = (width // 2, height // 2)
    rotation_matrix = cv2.getRotationMatrix2D(center, rotation_angle, 1.0)
    cos = np.abs(rotation_matrix[0, 0])
    sin = np.abs(rotation_matrix[0, 1])
    new_width_rot = int((height * sin) + (width * cos))
    new_height_rot = int((height * cos) + (width * sin))
    rotation_matrix[0, 2] += (new_width_rot / 2) - center[0]
    rotation_matrix[1, 2] += (new_height_rot / 2) - center[1]
    rotated_image = cv2.warpAffine(resized_image, rotation_matrix, (new_width_rot, new_height_rot),
                                  flags=cv2.INTER_NEAREST,
                                  borderMode=cv2.BORDER_CONSTANT,
                                  borderValue=[205, 205, 205])
    # Transform the points using the same matrix
    rotated_points = []
    for x, y in current_points:
        new_x = rotation_matrix[0, 0] * x + rotation_matrix[0, 1] * y + rotation_matrix[0, 2]
        new_y = rotation_matrix[1, 0] * x + rotation_matrix[1, 1] * y + rotation_matrix[1, 2]
        rotated_points.append((int(new_x), int(new_y)))
    # Find non-black pixels to determine crop boundaries
    gray = cv2.cvtColor(rotated_image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        x, y, w, h = cv2.boundingRect(max(contours, key=cv2.contourArea))
        rotated_image = rotated_image[y:y+h, x:x+w]
        current_points = [(px - x, py - y) for px, py in rotated_points]
    else:
        current_points = rotated_points
    current_shape = rotated_image.shape[:2]
    print_unique_colors(rotated_image, "step 7 rotate")
    vis_image = rotated_image.copy()
    for p in current_points:
        cv2.circle(vis_image, p, 5, (0, 0, 255), -1)
    show_image(vis_image, "Step 7: After Rotation with Points")
    show_world_map_with_points(world_map, world_map_points, "Step 7: World Map with Points")
    if SHOW_RESULT:
        wait_for_key()

    print("\nStep 8/12: Converting remaining black pixels...")
    # Step 8: Convert remaining black pixels to light gray
    final_gray_image = convert_black_to_light_gray(rotated_image)
    print_unique_colors(final_gray_image, "step 8 black to gray")
    
    # Show points on gray image
    vis_image = final_gray_image.copy()
    for p in current_points:
        cv2.circle(vis_image, p, 5, (0, 0, 255), -1)
    show_image(vis_image, "Step 8: After Black to Gray with Points")
    show_world_map_with_points(world_map, world_map_points, "Step 8: World Map with Points")
    if SHOW_RESULT:
        wait_for_key()

    print("\nStep 9/12: Cropping and re-expanding gray area...")
    # Step 9: Crop and re-expand gray area
    # Convert to grayscale for easier processing
    gray = cv2.cvtColor(final_gray_image, cv2.COLOR_BGR2GRAY)
    
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
    cropped = final_gray_image[top:bottom+1, left:right+1]
    
    # Show the cropped image with points
    vis_image = cropped.copy()
    for x, y in current_points:
        # Convert points to cropped coordinates
        cropped_x = x - left
        cropped_y = y - top
        # Only draw if point is within image bounds
        if 0 <= cropped_x < cropped.shape[1] and 0 <= cropped_y < cropped.shape[0]:
            cv2.circle(vis_image, (cropped_x, cropped_y), 5, (0, 0, 255), -1)
    show_image(vis_image, "Step 9a: After Cropping Gray Area with Points")
    show_world_map_with_points(world_map, world_map_points, "Step 9a: World Map with Points")
    if SHOW_RESULT:
        wait_for_key()
    
    # Add padding to all sides
    padded = cv2.copyMakeBorder(
        cropped,
        PADDING_WIDTH,  # top
        PADDING_WIDTH,  # bottom
        PADDING_WIDTH,  # left
        PADDING_WIDTH,  # right
        cv2.BORDER_CONSTANT,
        value=[205, 205, 205]  # Light gray padding
    )
    
    # Update points for padding
    current_points = [(x - left + PADDING_WIDTH, y - top + PADDING_WIDTH) for x, y in current_points]
    current_shape = padded.shape[:2]
    
    # Show the re-expanded image with points
    vis_image = padded.copy()
    for x, y in current_points:
        # Only draw if point is within image bounds
        if 0 <= x < padded.shape[1] and 0 <= y < padded.shape[0]:
            cv2.circle(vis_image, (x, y), 5, (0, 0, 255), -1)
    show_image(vis_image, "Step 9b: After Re-expanding Gray Area with Points")
    show_world_map_with_points(world_map, world_map_points, "Step 9b: World Map with Points")
    if SHOW_RESULT:
        wait_for_key()
    
    print_unique_colors(padded, "step 9 crop and re-expand")

    print("\nStep 10/12: Expanding track...")
    # Step 10: Expand track by 5 pixels
    expanded_image = expand_track(padded, 5)
    print_unique_colors(expanded_image, "step 10 expand track")
    
    # Show points on expanded image
    vis_image = expanded_image.copy()
    for p in current_points:
        cv2.circle(vis_image, p, 5, (0, 0, 255), -1)
    show_image(vis_image, "Step 10: After Track Expansion with Points")
    show_world_map_with_points(world_map, world_map_points, "Step 10: World Map with Points")
    if SHOW_RESULT:
        wait_for_key()

    print("\nStep 11/12: Adding padding...")
    # Step 11: Add 5 pixel padding
    padded_image = add_padding(expanded_image, 5)
    print_unique_colors(padded_image, "step 11 add padding")
    
    # Update points for padding
    current_points = [(x + 5, y + 5) for x, y in current_points]
    
    # Show points on padded image
    vis_image = padded_image.copy()
    for p in current_points:
        cv2.circle(vis_image, p, 5, (0, 0, 255), -1)
    show_image(vis_image, "Step 11: After Adding Padding with Points")
    show_world_map_with_points(world_map, world_map_points, "Step 11: World Map with Points")
    if SHOW_RESULT:
        wait_for_key()

    print("\nStep 12/12: Filtering isolated black pixels...")
    # Step 12: Filter out isolated black pixels
    final_image = filter_blobs(padded_image)
    print_unique_colors(final_image, "step 12 filter blobs (final)")
    
    # Show points on final image
    vis_image = final_image.copy()
    for p in current_points:
        cv2.circle(vis_image, p, 5, (0, 0, 255), -1)
    show_image(vis_image, "Step 12: Final Result with Points")
    show_world_map_with_points(world_map, world_map_points, "Step 12: World Map with Points")
    if SHOW_RESULT:
        wait_for_key()

    print("\n=== Final Alignment ===")
    # Step 13: Show alignment with world map...
    print(f"Original world map point coordinates: {world_map_points[0]}")
    print(f"Original bitmask point coordinates: {bitmask_points[0]}")
    print(f"Current point coordinates after processing: {current_points[0]}")
    print(f"Translation values: dx={translation[0]}, dy={translation[1]}")
    
    # Show world map with original points (only if SHOW_RESULT is True)
    if SHOW_RESULT:
        alignment_vis = world_map.copy()
        for point in world_map_points:
            cv2.circle(alignment_vis, point, 5, (255, 0, 0), -1)  # Both points in blue
        show_world_map_with_points(world_map, world_map_points, "Step 13: World Map with Points Before Alignment")
    
    # Create canvas for alignment
    h, w = final_image.shape[:2]
    world_h, world_w = world_map.shape[:2]
    
    # Calculate the position to place the processed image
    # Use the current point coordinates from the processed image
    processed_point = current_points[0]
    world_point = world_map_points[0]
    
    # Calculate offset to align the points
    x_offset = world_point[0] - processed_point[0]
    y_offset = world_point[1] - processed_point[1]
    
    print(f"Processed image point: {processed_point}")
    print(f"World map point: {world_point}")
    print(f"Calculated offsets: x={x_offset}, y={y_offset}")
    
    # Create canvas large enough for both images
    canvas_h = max(world_h, y_offset + h)
    canvas_w = max(world_w, x_offset + w)
    
    # Create two different alignment results
    # 1. With original world map
    canvas_original = np.full((canvas_h, canvas_w, 3), [205, 205, 205], dtype=np.uint8)
    canvas_original[0:world_h, 0:world_w] = world_map  # Use original world map
    
    # 2. With all-grey world map
    canvas_grey = np.full((canvas_h, canvas_w, 3), [205, 205, 205], dtype=np.uint8)
    world_map_grey = np.full_like(world_map, [205, 205, 205])
    canvas_grey[0:world_h, 0:world_w] = world_map_grey  # Use grey world map
    
    # Create mask for non-gray pixels in processed image
    mask = ~np.all(final_image == [205, 205, 205], axis=-1)
    
    # Place processed image on both canvases
    for canvas in [canvas_original, canvas_grey]:
        roi = canvas[y_offset:y_offset+h, x_offset:x_offset+w]
        # Directly copy the processed image pixels where mask is True
        roi[mask] = final_image[mask]
        canvas[y_offset:y_offset+h, x_offset:x_offset+w] = roi
    
    # Clip both canvases to the world map boundaries
    canvas_original = canvas_original[0:world_h, 0:world_w]
    canvas_grey = canvas_grey[0:world_h, 0:world_w]
    
    # Show final alignment (using the grey version for display)
    show_image(canvas_grey, "Final Alignment")

    # Save both results
    alignment_path_original = os.path.join(ROOT_DIR, "outputs", "aligned_with_worldmap_original.png")
    alignment_path_grey = os.path.join(ROOT_DIR, "outputs", "aligned_with_worldmap_grey.png")
    output_path = os.path.join(ROOT_DIR, "outputs", "processed_bitmask.png")
    
    if isRGB:
        # Save in RGB format
        cv2.imwrite(alignment_path_original, canvas_original)
        cv2.imwrite(alignment_path_grey, canvas_grey)
        cv2.imwrite(output_path, final_image)
    else:
        # Convert to 8-bit format before saving
        # For alignment images, convert to grayscale
        cv2.imwrite(alignment_path_original, cv2.cvtColor(canvas_original, cv2.COLOR_BGR2GRAY))
        cv2.imwrite(alignment_path_grey, cv2.cvtColor(canvas_grey, cv2.COLOR_BGR2GRAY))
        # For processed image, convert to binary (black and white only)
        _, binary_image = cv2.threshold(cv2.cvtColor(final_image, cv2.COLOR_BGR2GRAY), 127, 255, cv2.THRESH_BINARY)
        cv2.imwrite(output_path, binary_image)
    
    print(f"Alignment result with original world map saved to: {alignment_path_original}")
    print(f"Alignment result with grey world map saved to: {alignment_path_grey}")
    print(f"Final processed image saved to: {output_path}")
    
    print("\n=== Processing Complete ===")

if __name__ == "__main__":
    main() 