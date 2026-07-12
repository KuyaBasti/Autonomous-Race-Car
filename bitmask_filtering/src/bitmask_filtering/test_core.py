import cv2
import numpy as np
from .core import (
    flood_fill_black,
    find_point_inside_track,
    convert_white_to_light_gray,
    convert_black_to_light_gray,
    resize_image,
    convert_border_gray_to_black,
    add_padding,
    expand_track
)

def create_test_image():
    """Create a simple test image with a track-like pattern."""
    # Create a 100x100 black image
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    
    # Draw a simple track (white lines on black background)
    # Outer track
    cv2.rectangle(image, (10, 10), (90, 90), (255, 255, 255), 2)
    # Inner track
    cv2.rectangle(image, (30, 30), (70, 70), (255, 255, 255), 2)
    
    return image

def test_all_functions():
    """Test all core functions with a simple test image."""
    # Create test image
    image = create_test_image()
    
    # Save original image
    cv2.imwrite('test_original.png', image)
    
    # Test flood fill
    filled = flood_fill_black(image, 0, 0)
    cv2.imwrite('test_flood_fill.png', filled)
    
    # Test find point inside track
    point = find_point_inside_track(filled)
    print(f"Found point inside track: {point}")
    
    # Test white to light gray conversion
    gray_white = convert_white_to_light_gray(filled)
    cv2.imwrite('test_white_to_gray.png', gray_white)
    
    # Test black to light gray conversion
    gray_black = convert_black_to_light_gray(gray_white)
    cv2.imwrite('test_black_to_gray.png', gray_black)
    
    # Test resize
    resized = resize_image(gray_black, 200)
    cv2.imwrite('test_resized.png', resized)
    
    # Test border gray to black conversion
    border_black = convert_border_gray_to_black(gray_black)
    cv2.imwrite('test_border_black.png', border_black)
    
    # Test padding
    padded = add_padding(border_black, 10)
    cv2.imwrite('test_padded.png', padded)
    
    # Test track expansion
    expanded = expand_track(border_black, 2)
    cv2.imwrite('test_expanded.png', expanded)
    
    print("All tests completed. Check the generated PNG files for results.")

if __name__ == "__main__":
    test_all_functions() 