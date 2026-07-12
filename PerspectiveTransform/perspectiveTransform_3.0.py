
import open3d as o3d
import numpy as np
import json
import cv2
import os

# ===== Configuration =====

world_x_max = 50
world_x_min = 7
world_y_max = 10
world_y_min = -10

world_x_interval = 0.05
world_y_interval = 0.025

X = 0
Y = 0.2667 # Camera Height in m
Z = 0

YAW_DEG = 0.0
ROLL_DEG = 0.0

CONFIG_PATH = "./PerspectiveTransform/src/config/cam_config.json"
PLY_PATH = "./PerspectiveTransform/src/config/track1.ply"
IMAGE_PATH = "./PerspectiveTransform/src/images/track1_Color.png"


# === Original helper functions (unchanged) ===



def estimate_pitch_from_ply(ply_path):
    pcd = o3d.io.read_point_cloud(ply_path)
    if pcd.is_empty():
        raise ValueError("The point cloud is empty.")

    plane_model, inliers = pcd.segment_plane(distance_threshold=0.02,
                                             ransac_n=3,
                                             num_iterations=1000)
    a, b, c, d = plane_model
    normal = np.array([a, b, c])
    normal /= np.linalg.norm(normal)

    # Pitch = arcsin(z tilt)
    pitch_rad = np.arcsin(normal[2])
    pitch_deg = -np.rad2deg(pitch_rad)

    return pitch_deg, plane_model

def rotation_from_euler(roll_deg, pitch_deg, yaw_deg):
    """
    Get rotation matrix
    Args:
        roll, pitch, yaw:       In radians

    Returns:
        R:          [4, 4]
    """
    # Convert roll, pitch, yaw to radian
    roll = -np.deg2rad(roll_deg)
    pitch = -np.deg2rad(pitch_deg)
    yaw = -np.deg2rad(yaw_deg)
    
    si, sj, sk = np.sin(roll), np.sin(pitch), np.sin(yaw)
    ci, cj, ck = np.cos(roll), np.cos(pitch), np.cos(yaw)
    cc, cs = ci * ck, ci * sk
    sc, ss = si * ck, si * sk

    R = np.identity(4)
    R[0, 0] = cj * ck
    R[0, 1] = sj * sc - cs
    R[0, 2] = sj * cc + ss
    R[1, 0] = cj * sk
    R[1, 1] = sj * ss + cc
    R[1, 2] = sj * cs - sc
    R[2, 0] = -sj
    R[2, 1] = cj * si
    R[2, 2] = cj * ci
    return R


def translation_matrix(vector):
    """
    Translation matrix

    Args:
        vector list[float]:     (x, y, z)

    Returns:
        T:      [4, 4]
    """
    M = np.identity(4)
    M[:3, 3] = vector[:3]
    return M


def load_camera_params():
    """
    Get the intrinsic and extrinsic parameters
    Returns:
        Camera extrinsic and intrinsic matrices
    """
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)

    fx = float(config["rectified.0.fx"])
    fy = float(config["rectified.0.fy"])
    u0 = float(config["rectified.0.ppx"])
    v0 = float(config["rectified.0.ppy"])
    
    pitch_deg, _ = estimate_pitch_from_ply(PLY_PATH)
    
    roll = -np.deg2rad(ROLL_DEG)
    pitch = -np.deg2rad(pitch_deg)
    yaw = -np.deg2rad(YAW_DEG)
    
    
    p = {}
    p["roll"] =  roll
    p["pitch"] =  pitch
    p["yaw"] =  yaw

    p["x"] =  X
    p["y"] =  Y
    p["z"] =  Z

    pitch, roll, yaw = p['pitch'], p['roll'], p['yaw']
    x, y, z = p['x'], p['y'], p['z']

    # Intrinsic
    K = np.array([[fx, 0, u0, 0],
                  [0, fy, v0, 0],
                  [0, 0, 1, 0],
                  [0, 0, 0, 1]])

    # Extrinsic
    R_veh2cam = np.transpose(rotation_from_euler(roll, pitch, yaw))
    T_veh2cam = translation_matrix((-x, -y, -z))

    # Rotate to camera coordinates
    R = np.array([[0., -1., 0., 0.],
                  [0., 0., -1., 0.],
                  [1., 0., 0., 0.],
                  [0., 0., 0., 1.]])

    RT = R @ R_veh2cam @ T_veh2cam
    return RT, K

def generate_direct_backward_mapping(
    world_x_min, world_x_max, world_x_interval, 
    world_y_min, world_y_max, world_y_interval, extrinsic, intrinsic):
    
    print("world_x_min : ", world_x_min)
    print("world_x_max : ", world_x_max)
    print("world_x_interval (m) : ", world_x_interval)
    print()
    
    print("world_y_min : ", world_y_min)
    print("world_y_max : ", world_y_max)
    print("world_y_interval (m) : ", world_y_interval)
    
    world_x_coords = np.arange(world_x_max, world_x_min, -world_x_interval)
    world_y_coords = np.arange(world_y_max, world_y_min, -world_y_interval)
    
    output_height = len(world_x_coords)
    output_width = len(world_y_coords)
    
    map_x = np.zeros((output_height, output_width)).astype(np.float32)
    map_y = np.zeros((output_height, output_width)).astype(np.float32)
    
    world_z = 0
    for i, world_x in enumerate(world_x_coords):
        for j, world_y in enumerate(world_y_coords):
            # world_coord : [world_x, world_y, 0, 1]
            # uv_coord : [u, v, 1]
            
            world_coord = [world_x, world_y, world_z, 1]
            camera_coord = extrinsic[:3, :] @ world_coord
            uv_coord = intrinsic[:3, :3] @ camera_coord
            uv_coord /= uv_coord[2]

            # map_x : (H, W)
            # map_y : (H, W)
            # dst[i][j] = src[ map_y[i][j] ][ map_x[i][j] ]
            map_x[i][j] = uv_coord[0]
            map_y[i][j] = uv_coord[1]
            
    return map_x, map_y

def remap_nearest(src, map_x, map_y):
    src_height = src.shape[0]
    src_width = src.shape[1]
    
    dst_height = map_x.shape[0]
    dst_width = map_x.shape[1]
    dst = np.zeros((dst_height, dst_width, 3)).astype(np.uint8)
    for i in range(dst_height):
        for j in range(dst_width):
            src_y = int(np.round(map_y[i][j]))
            src_x = int(np.round(map_x[i][j]))
            if 0 <= src_y and src_y < src_height and 0 <= src_x and src_x < src_width:
                dst[i][j] = src[src_y, src_x, :]
    return dst 

#output_image_nearest = remap_nearest(image, map_x, map_y)
#output_image = cv2.remap(image, map_x, map_y, cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT)

#mask = (output_image > [0, 0, 0])
#output_image = output_image.astype(np.float32)
#output_image_nearest = output_image_nearest.astype(np.float32)

#print("L1 Loss of opencv remap Vs. custom remap nearest : ", np.mean(np.abs(output_image[mask]-output_image_nearest[mask])))
#print("L2 Loss of opencv remap Vs. custom remap nearest : ", np.mean((output_image[mask]-output_image_nearest[mask])**2))

# L1 Loss of opencv remap Vs. custom remap nearest :  0.0
# L2 Loss of opencv remap Vs. custom remap nearest :  0.0

def bilinear_sampler(imgs, pix_coords):
    """
    Construct a new image by bilinear sampling from the input image.
    Args:
        imgs:                   [H, W, C]
        pix_coords:             [h, w, 2]
    :return:
        sampled image           [h, w, c]
    """
    img_h, img_w, img_c = imgs.shape
    pix_h, pix_w, pix_c = pix_coords.shape
    out_shape = (pix_h, pix_w, img_c)

    pix_x, pix_y = np.split(pix_coords, [1], axis=-1)  # [pix_h, pix_w, 1]
    pix_x = pix_x.astype(np.float32)
    pix_y = pix_y.astype(np.float32)

    # Rounding
    pix_x0 = np.floor(pix_x)
    pix_x1 = pix_x0 + 1
    pix_y0 = np.floor(pix_y)
    pix_y1 = pix_y0 + 1

    # Clip within image boundary
    y_max = (img_h - 1)
    x_max = (img_w - 1)
    zero = np.zeros([1])

    pix_x0 = np.clip(pix_x0, zero, x_max)
    pix_y0 = np.clip(pix_y0, zero, y_max)
    pix_x1 = np.clip(pix_x1, zero, x_max)
    pix_y1 = np.clip(pix_y1, zero, y_max)

    # Weights [pix_h, pix_w, 1]
    wt_x0 = pix_x1 - pix_x
    wt_x1 = pix_x - pix_x0
    wt_y0 = pix_y1 - pix_y
    wt_y1 = pix_y - pix_y0

    # indices in the image to sample from
    dim = img_w

    # Apply the lower and upper bound pix coord
    base_y0 = pix_y0 * dim
    base_y1 = pix_y1 * dim

    # 4 corner vertices
    idx00 = (pix_x0 + base_y0).flatten().astype(np.int32)
    idx01 = (pix_x0 + base_y1).astype(np.int32)
    idx10 = (pix_x1 + base_y0).astype(np.int32)
    idx11 = (pix_x1 + base_y1).astype(np.int32)

    # Gather pixels from image using vertices
    imgs_flat = imgs.reshape([-1, img_c]).astype(np.float32)
    im00 = imgs_flat[idx00].reshape(out_shape)
    im01 = imgs_flat[idx01].reshape(out_shape)
    im10 = imgs_flat[idx10].reshape(out_shape)
    im11 = imgs_flat[idx11].reshape(out_shape)

    # Apply weights [pix_h, pix_w, 1]
    w00 = wt_x0 * wt_y0
    w01 = wt_x0 * wt_y1
    w10 = wt_x1 * wt_y0
    w11 = wt_x1 * wt_y1
    output = w00 * im00 + w01 * im01 + w10 * im10 + w11 * im11
    return output

def remap_bilinear(image, map_x, map_y):
    pix_coords = np.concatenate([np.expand_dims(map_x, -1), np.expand_dims(map_y, -1)], axis=-1)
    bilinear_output = bilinear_sampler(image, pix_coords)
    output = np.round(bilinear_output).astype(np.int32)
    return output    

#output_image_bilinear = remap_bilinear(image, map_x, map_y)
#output_image = cv2.remap(image, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)

#mask = (output_image > [0, 0, 0])
#output_image = output_image.astype(np.float32)
#output_image_bilinear = output_image_bilinear.astype(np.float32)
#print("L1 Loss of opencv remap Vs. custom remap bilinear : ", np.mean(np.abs(output_image[mask]-output_image_bilinear[mask])))
#print("L2 Loss of opencv remap Vs. custom remap bilinear : ", np.mean((output_image[mask]-output_image_bilinear[mask])**2))

# L1 Loss of opencv remap Vs. custom remap bilinear :  0.045081623
# L2 Loss of opencv remap Vs. custom remap bilinear :  0.66912574

def main():
    # === Step 1: Load image ===
    if not os.path.exists(IMAGE_PATH):
        raise FileNotFoundError(f"Image not found at {IMAGE_PATH}")
    image = cv2.imread(IMAGE_PATH)
    
    print("Original image loaded.")
    cv2.imshow("Original Image", image)
    cv2.waitKey(500)  # show briefly before BEV

    # === Step 2: Estimate pitch from point cloud ===
    print("\nEstimating pitch from PLY file...")
    pitch_deg, plane_model = estimate_pitch_from_ply(PLY_PATH)
    print(f"Estimated Pitch: {pitch_deg:.4f}°")

    # === Step 3: Load camera parameters ===
    print("\nLoading camera parameters...")
    extrinsic, intrinsic = load_camera_params()

    print("\nIntrinsic Matrix (K):")
    print(intrinsic)

    print("\nExtrinsic Matrix (RT):")
    print(extrinsic)

    # === Step 4: Generate backward mapping ===
    print("\nGenerating backward mapping...")
    map_x, map_y = generate_direct_backward_mapping(
        world_x_min, world_x_max, world_x_interval,
        world_y_min, world_y_max, world_y_interval,
        extrinsic, intrinsic
    )

    # === Step 5: Perform remapping ===
    print("Performing remap (bilinear)...")
    output_image_bilinear = remap_bilinear(image, map_x, map_y)

    # === Step 6: Show and save result ===
    output_image_bilinear = np.clip(output_image_bilinear, 0, 255).astype(np.uint8)

    cv2.imshow("Bird's Eye View (Bilinear)", output_image_bilinear)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    output_path = "./PerspectiveTransform/output/bev_output_bilinear.png"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, output_image_bilinear)
    print(f"Output image saved to {output_path}")
   

if __name__ == "__main__":
    main()
