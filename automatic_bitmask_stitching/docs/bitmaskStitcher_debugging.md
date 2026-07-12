# Debugging Process for `bitmaskStitcher.py`

## Overview
This document outlines the step-by-step debugging process undertaken to fix and validate the `bitmaskStitcher.py` script, which overlays bitmask track images onto a SLAM map using pose data.

---

## 1. Initial Problem
- The output overlay was entirely red or white, not showing the expected track.
- Bitmask images were not being found due to filename mismatches (missing `_mask` suffix).
- The overlay covered the whole map, indicating a transformation or scaling issue.

---

## 2. Step-by-Step Debugging

### a. Bitmask Filename Issue
- **Problem:** Script looked for `frame_xxx.png` but files were named `frame_xxx_mask.png`.
- **Fix:** Updated the script to append `_mask` before the file extension when searching for bitmask files.

### b. Overlay All Red/White
- **Problem:** The overlay was all red or all white, not showing the track.
- **Debugging:**
  - Added debug output to print unique values in each bitmask.
  - Saved the intermediate `stitched_map` as a grayscale image for inspection.
  - Printed the placement coordinates `(x_px, y_px)` and scaling factors.
  - Saved warped bitmask images for visual inspection.

### c. Scaling and Transformation
- **Problem:** Bitmasks were being blown up to cover the whole map or shrunk to a dot.
- **Fix:**
  - Corrected the scaling calculation to use `BITMASK_RES_X / MAP_RESOLUTION` and `BITMASK_RES_Y / MAP_RESOLUTION`.
  - Ensured the transformation order was: center → scale → rotate → translate.
  - Added debug output for expected warped bitmask size.

### d. Visual Validation
- **Action:**
  - Inspected warped bitmask images to confirm they matched the expected track shape and size.
  - Checked the final overlay to ensure the red track segments were correctly placed on the SLAM map.

---

## 3. Final Outcome
- The script now correctly overlays the track on the SLAM map.
- The bitmask images are properly scaled, rotated, and placed according to the pose data.
- Debug output and intermediate images were used to validate each step.

---

## 4. Lessons Learned
- Always check file naming conventions and ensure the script matches the data.
- Use debug output and intermediate visualizations to diagnose transformation and scaling issues.
- Carefully verify the order of affine transformations (scaling, rotation, translation).

---

**This process can serve as a template for debugging similar image transformation and overlay pipelines.** 