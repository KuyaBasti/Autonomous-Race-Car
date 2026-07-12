import cv2
import numpy as np

"""
=====================
User Defined Section
=====================
"""
# Provide paths to your images
original_image_path = './Stitching/src/images/track_elipse_13.jpg'
target_image_path = './Stitching/src/images/track_elipse_4.jpg'
output_image_path = './Stitching/src/images/track_elipse_final.jpg'

"""
=====================
Core Program
=====================
"""

def get_points_from_user(image, window_name):
    points = []

    def click_event(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            points.append((x, y))
            cv2.circle(image, (x, y), 5, (0, 255, 0), -1)
            cv2.imshow(window_name, image)

    clone = image.copy()
    cv2.imshow(window_name, clone)
    cv2.setMouseCallback(window_name, click_event)

    while len(points) < 2:
        cv2.waitKey(1)

    cv2.destroyWindow(window_name)
    return points

def feather_blend(img1, img2, blend_width=30):
    mask = np.zeros((img1.shape[0], img1.shape[1]), dtype=np.float32)
    transition_zone = np.linspace(0, 1, blend_width)

    mask[:, :img1.shape[1]//2-blend_width//2] = 1
    for i in range(blend_width):
        mask[:, img1.shape[1]//2-blend_width//2+i] = 1 - transition_zone[i]

    mask = cv2.merge([mask, mask, mask])
    blended = (img1 * mask + img2 * (1 - mask)).astype(np.uint8)
    return blended

def stitch_images(original_img, target_img, src_pts, dst_pts):
    src_pts = np.array(src_pts, dtype=np.float32)
    dst_pts = np.array(dst_pts, dtype=np.float32)

    if len(src_pts) == 2:
        def third_point(p1, p2):
            direction = p2 - p1
            perp = np.array([-direction[1], direction[0]])
            p3 = p1 + perp
            return p3

        src_pts = np.vstack([src_pts, third_point(src_pts[0], src_pts[1])])
        dst_pts = np.vstack([dst_pts, third_point(dst_pts[0], dst_pts[1])])

    M = cv2.getAffineTransform(dst_pts, src_pts)

    h1, w1 = original_img.shape[:2]
    h2, w2 = target_img.shape[:2]

    corners = np.array([
        [0, 0],
        [w2, 0],
        [w2, h2],
        [0, h2]
    ], dtype=np.float32)

    transformed_corners = cv2.transform(np.array([corners]), M)[0]

    all_corners = np.vstack((transformed_corners, [[0, 0], [w1, 0], [w1, h1], [0, h1]]))

    [xmin, ymin] = np.int32(all_corners.min(axis=0) - 0.5)
    [xmax, ymax] = np.int32(all_corners.max(axis=0) + 0.5)

    translation = [-xmin, -ymin]

    stitched_width = xmax - xmin
    stitched_height = ymax - ymin

    M[0, 2] += translation[0]
    M[1, 2] += translation[1]

    warped_target = cv2.warpAffine(target_img, M, (stitched_width, stitched_height))

    stitched_canvas = np.zeros_like(warped_target)

    src_pts_sorted = sorted(src_pts, key=lambda p: p[0])
    dst_pts_sorted = sorted(dst_pts, key=lambda p: p[0])

    cut_x_original = int((src_pts_sorted[0][0] + src_pts_sorted[1][0]) / 2)
    cut_x_target = int((dst_pts_sorted[0][0] + dst_pts_sorted[1][0]) / 2)

    y_offset = translation[1]
    x_offset = translation[0]

    # Place left side of original image
    stitched_canvas[y_offset:y_offset+h1, x_offset:x_offset+cut_x_original] = original_img[:, :cut_x_original]

    # Place right side of warped target image, cropped properly
    stitched_canvas[:, cut_x_original+x_offset:] = warped_target[:, cut_x_original+x_offset:]

    # Apply feather blending around the cut
    blended_result = feather_blend(stitched_canvas, warped_target)

    return blended_result

if __name__ == '__main__':
    original = cv2.imread(original_image_path)
    target = cv2.imread(target_image_path)

    if original is None:
        raise FileNotFoundError(f"Original image not found at {original_image_path}")
    if target is None:
        raise FileNotFoundError(f"Target image not found at {target_image_path}")

    print("Click 2 points on the ORIGINAL image")
    original_points = get_points_from_user(original, "Original Image")

    print("Click 2 points on the TARGET image")
    target_points = get_points_from_user(target, "Target Image")

    result = stitch_images(original, target, original_points, target_points)

    cv2.imwrite(output_image_path, result)
    print(f"Stitched image saved as {output_image_path}")

    cv2.imshow('Stitched Image', result)
    cv2.waitKey(0)
    cv2.destroyAllWindows() 