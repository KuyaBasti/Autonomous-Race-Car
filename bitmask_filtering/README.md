# Bitmask Filtering Library

A Python library for processing and filtering bitmask images, particularly useful for race track images.

## Features

- Flood fill operation to fill connected black pixels
- Point detection inside track regions
- Color conversion utilities (white/black to light gray)
- Image resizing with aspect ratio preservation
- Border pixel conversion

## Installation

1. Clone the repository
2. Create a virtual environment (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

```python
from bitmask_filtering import (
    flood_fill_black,
    find_point_inside_track,
    convert_white_to_light_gray,
    convert_black_to_light_gray,
    resize_image,
    convert_border_gray_to_black
)

# Load your image
image = cv2.imread('your_image.png')

# Find a point inside the track
point = find_point_inside_track(image)
if point:
    x, y = point
    # Fill the track area
    filled_image = flood_fill_black(image, x, y)
    
    # Convert colors and resize as needed
    result = convert_border_gray_to_black(filled_image)
    result = resize_image(result, target_width=200)
    
    # Save the result
    cv2.imwrite('output.png', result)
```

## Functions

### flood_fill_black(image, x, y, new_color=[255, 255, 255])
Fills connected black pixels starting from the given coordinates with the specified color.

### find_point_inside_track(image)
Automatically finds a point inside the track by scanning for black pixels between white track lines.

### convert_white_to_light_gray(image)
Converts all white pixels to light gray (RGB: 205, 205, 205).

### convert_black_to_light_gray(image)
Converts all black pixels to light gray (RGB: 205, 205, 205).

### resize_image(image, target_width)
Resizes the image to the target width while maintaining aspect ratio.

### convert_border_gray_to_black(image)
Converts gray pixels that border white pixels to black.

## Requirements

- Python 3.7 or higher
- OpenCV (opencv-python)
- NumPy

## License

MIT License 