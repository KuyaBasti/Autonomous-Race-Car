import cv2
import numpy as np

def flood_fill_black(image, x, y, new_color=[255, 255, 255]):
    """
    Flood fill all connected black pixels starting from (x,y) coordinate.
    
    Args:
        image: Input image (numpy array)
        x: Starting x coordinate
        y: Starting y coordinate
        new_color: Color to replace black pixels with (default: [255, 255, 255] - white)
    """
    print("Starting flood fill operation...")
    
    # Create a copy of the image to avoid modifying the original
    filled_image = image.copy()
    
    # Get image dimensions
    height, width = filled_image.shape[:2]
    total_pixels = height * width
    
    # Check if starting point is within image bounds
    if x < 0 or x >= width or y < 0 or y >= height:
        return filled_image
    
    # Get the target color (black)
    target_color = [0, 0, 0]
    
    # Check if starting point is black
    if not np.array_equal(filled_image[y, x], target_color):
        return filled_image
    
    # Create a visited array to track processed pixels
    visited = np.zeros((height, width), dtype=bool)
    
    # Create a queue for flood fill
    queue = [(x, y)]
    visited[y, x] = True
    
    # Define 4-connectivity (up, down, left, right)
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    
    # Progress tracking
    processed_pixels = 0
    last_progress = 0
    
    while queue:
        current_x, current_y = queue.pop(0)
        
        # Change the current pixel to new color
        filled_image[current_y, current_x] = new_color
        processed_pixels += 1
        
        # Report progress every 5%
        progress = int((processed_pixels / total_pixels) * 100)
        if progress > last_progress and progress % 5 == 0:
            print(f"Progress: {progress}% ({processed_pixels}/{total_pixels} pixels processed)")
            last_progress = progress
        
        # Check neighboring pixels
        for dx, dy in directions:
            new_x = current_x + dx
            new_y = current_y + dy
            
            # Check if the new coordinates are within bounds and not visited
            if (0 <= new_x < width and 0 <= new_y < height and 
                not visited[new_y, new_x] and 
                np.array_equal(filled_image[new_y, new_x], target_color)):
                queue.append((new_x, new_y))
                visited[new_y, new_x] = True
    
    print("Flood fill completed!")
    return filled_image

def find_point_inside_track(image):
    """
    Find a pixel coordinate that lies inside the race track.
    The function scans from the origin (0,0) to find a point that's inside the track.
    Accounts for multi-pixel wide track lines.
    
    Args:
        image: Input image (numpy array)
        
    Returns:
        tuple: (x, y) coordinates of a point inside the track, or None if not found
    """
    print("Searching for point inside track...")
    height, width = image.shape[:2]
    
    # Define white color
    white = [255, 255, 255]
    
    # Minimum number of continuous white pixels to consider it a track line
    min_track_width = 3
    
    # Start scanning from origin (0,0)
    for y in range(height):
        for x in range(width):
            if not np.array_equal(image[y, x], white):
                # Found a black pixel, check if it's inside the track
                # Check for continuous white pixels to the left
                left_white_count = 0
                for left_x in range(x-1, -1, -1):
                    if np.array_equal(image[y, left_x], white):
                        left_white_count += 1
                    else:
                        break
                
                # Check for continuous white pixels to the right
                right_white_count = 0
                for right_x in range(x+1, width):
                    if np.array_equal(image[y, right_x], white):
                        right_white_count += 1
                    else:
                        break
                
                # If we have enough white pixels on both sides, we're inside the track
                if left_white_count >= min_track_width and right_white_count >= min_track_width:
                    print(f"Found point inside track at: ({x}, {y})")
                    return (x, y)
    
    print("No suitable point inside track found")
    return None

def convert_white_to_light_gray(image):
    """
    Convert all white pixels to light gray (hex #CDCDCD).
    
    Args:
        image: Input image (numpy array)
        
    Returns:
        numpy array: Image with white pixels converted to light gray
    """
    print("Converting white pixels to light gray...")
    # Create a copy of the image
    result = image.copy()
    
    # Define white color
    white = [255, 255, 255]
    # Define light gray color (hex #CDCDCD)
    light_gray = [205, 205, 205]
    
    # Create a mask for white pixels
    white_mask = np.all(result == white, axis=-1)
    
    # Convert white pixels to light gray
    result[white_mask] = light_gray
    
    return result

def convert_black_to_light_gray(image):
    """
    Convert all black pixels to light gray (hex #CDCDCD).
    
    Args:
        image: Input image (numpy array)
        
    Returns:
        numpy array: Image with black pixels converted to light gray
    """
    print("Converting black pixels to light gray...")
    # Create a copy of the image
    result = image.copy()
    
    # Define black color
    black = [0, 0, 0]
    # Define light gray color (hex #CDCDCD)
    light_gray = [205, 205, 205]
    
    # Create a mask for black pixels
    black_mask = np.all(result == black, axis=-1)
    
    # Convert black pixels to light gray
    result[black_mask] = light_gray
    
    return result

def resize_image(image, target_width):
    """
    Resize image to target width while maintaining aspect ratio and preserving exact pixel values.
    
    Args:
        image: Input image (numpy array)
        target_width: Target width in pixels
        
    Returns:
        numpy array: Resized image
    """
    print(f"Resizing image to width {target_width}...")
    # Get original dimensions
    height, width = image.shape[:2]
    
    # Calculate new dimensions while maintaining aspect ratio
    aspect_ratio = height / width
    new_width = target_width
    new_height = int(new_width * aspect_ratio)
    
    # Resize using nearest neighbor interpolation to preserve exact pixel values
    resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_NEAREST)
    
    return resized

def convert_border_gray_to_black(image):
    """
    Convert gray pixels that border white pixels to black.
    
    Args:
        image: Input image (numpy array)
        
    Returns:
        numpy array: Image with border gray pixels converted to black
    """
    print("Converting border gray pixels to black...")
    # Create a copy of the image
    result = image.copy()
    
    # Define colors
    white = [255, 255, 255]
    gray = [205, 205, 205]
    black = [0, 0, 0]
    
    # Get image dimensions
    height, width = image.shape[:2]
    
    # Create a mask for gray pixels
    gray_mask = np.all(result == gray, axis=-1)
    
    # Define 8-connectivity (all surrounding pixels)
    directions = [(-1, -1), (-1, 0), (-1, 1),
                 (0, -1),          (0, 1),
                 (1, -1),  (1, 0), (1, 1)]
    
    # For each gray pixel, check if it borders a white pixel
    for y in range(height):
        for x in range(width):
            if gray_mask[y, x]:
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        if np.array_equal(result[ny, nx], white):
                            result[y, x] = black
                            break
    
    return result 