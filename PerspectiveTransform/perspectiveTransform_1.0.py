import cv2
import numpy as np

def main():
    # -------------------------------------------------------
    # 1. Load and Preprocess the Binary Segmentation Mask
    # -------------------------------------------------------
    mask_path = "test3.png"  # Update with your correct path
    original_path = "after.png"
    
    sam_mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    
    if sam_mask is None:
        print(f"Error: Could not load segmentation mask from {mask_path}. Check file path and format.")
        return
    
    # Resize the mask for consistency
    original_size = (800, 600)
    sam_mask = cv2.resize(sam_mask, original_size)
    
    # Convert to binary (0 or 255)
    _, sam_mask = cv2.threshold(sam_mask, 127, 255, cv2.THRESH_BINARY)

    # -------------------------------------------------------
    # 2. Define Source & Destination Points
    # -------------------------------------------------------
    # Source points (where in the original mask you want to transform)
    tl = (296, 226)  # Top-left
    bl = (45,   435)  # Bottom-left
    tr = (501, 223)  # Top-right
    br = (750, 404)  # Bottom-right
    pts1 = np.float32([tl, bl, tr, br])
    
    # Destination points (bird’s-eye view layout)
    output_size = (800, 600)  # (width, height)
    pts2 = np.float32([
        [206,  29],   # New top-left
        [192, 513], # New bottom-left
        [589,  6],   # New top-right
        [602,  496]  # New bottom-right
    ])

    # -------------------------------------------------------
    # 3. Compute & Apply Perspective Transformation
    # -------------------------------------------------------
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    print("Perspective Transformation Matrix:\n", matrix)

    # Convert mask to float32 for warpPerspective
    sam_mask = sam_mask.astype(np.float32)

    # Use nearest-neighbor interpolation to avoid grayscale artifacts
    transformed_mask = cv2.warpPerspective(
        sam_mask,
        matrix,
        output_size,
        flags=cv2.INTER_NEAREST
    )

    # Re-threshold to ensure the result remains strictly 0 or 255
    _, transformed_mask = cv2.threshold(transformed_mask, 127, 255, cv2.THRESH_BINARY)

    # (Optional) Morphological close to smooth small gaps/jaggies
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    transformed_mask = cv2.morphologyEx(transformed_mask, cv2.MORPH_CLOSE, kernel)

    # Convert back to uint8 for display
    transformed_mask = transformed_mask.astype(np.uint8)

    # -------------------------------------------------------
    # 4. Display Results
    # -------------------------------------------------------
    original_image = cv2.imread(original_path)
    cv2.imshow("Original Bird-Eye", original_image)
    cv2.imshow("Original SAM Mask", sam_mask.astype(np.uint8))
    cv2.imshow("Transformed Mask (Bird’s-Eye View)", transformed_mask)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()