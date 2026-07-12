"""
A library for processing and filtering bitmask images.
"""

from .core import (
    flood_fill_black,
    find_point_inside_track,
    convert_white_to_light_gray,
    convert_black_to_light_gray,
    resize_image,
    convert_border_gray_to_black
)

__version__ = "0.1.0" 