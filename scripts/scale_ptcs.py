import argparse
import os
import numpy as np
import open3d as o3d
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import utm
from typing import Tuple
from scipy.spatial.transform import Rotation as R
import sys
from obj_transformer import OBJTransformer
# Force stdout and stderr to be unbuffered
sys.stdout = open(sys.stdout.fileno(), mode='w', buffering=1)
sys.stderr = open(sys.stderr.fileno(), mode='w', buffering=1)
sys.stdout.reconfigure(line_buffering=True)


def get_exif_data(image_path: str) -> Tuple[float, float, float]:
    """Extracts latitude, longitude, and altitude from image EXIF data.

    Args:
        image_path (str): path to the image files.

    Raises:
        Exception: No exif data in the image.

    Returns:
        Tuple[float, float, float]: latitude, longitude and altitude.
    """
    image = Image.open(image_path)
    exif_data = image._getexif()
    if not exif_data:
        raise Exception(f"No EXIF data found in {image_path}")

    gps_info = {}
    for tag, value in exif_data.items():
        tag_name = TAGS.get(tag, tag)
        if tag_name == "GPSInfo":
            for gps_tag in value:
                gps_info[GPSTAGS.get(gps_tag, gps_tag)] = value[gps_tag]

    latitude = convert_to_degrees(gps_info.get(
        "GPSLatitude"), gps_info.get("GPSLatitudeRef"))
    longitude = convert_to_degrees(gps_info.get(
        "GPSLongitude"), gps_info.get("GPSLongitudeRef"))
    altitude = gps_info.get("GPSAltitude", None)

    return latitude, longitude, altitude


def convert_to_degrees(value: Tuple[float, float, float], ref: str) -> float:
    """Converts GPS coordinates to degrees.

    Args:
        value (Tuple[float, float, float]): coordinates in degrees, minutes, seconds.
        ref (str): hemisphere reference.

    Returns:
        float: the coordinates in degrees.
    """
    d, m, s = value
    degrees = d + (m / 60.0) + (s / 3600.0)

    if ref in ['S', 'W']:
        degrees = -degrees

    return degrees


def process_images(folder_path: str) -> list:
    """Processes all images in the given folder and extracts GPS data.

    Args:
        folder_path (str): folder containing images.

    Raises:
        Exception: No folder is found.

    Returns:
        list: list of dictionaries containing image filename, UTM easting, northing, and altitude.
    """
    if not os.path.isdir(folder_path):
        raise Exception(f"Invalid directory: {folder_path}")

    image_extensions = (".png", ".jpg", ".jpeg")
    results = []

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(image_extensions):
            image_path = os.path.join(folder_path, filename)
            lat, lon, alt = get_exif_data(image_path)
            utm_e, utm_n, _, _ = utm.from_latlon(lat, lon)
            results.append({
                "filename": filename,
                "utm_e": float(utm_e),
                "utm_n": float(utm_n),
                "altitude": float(alt)
            })

    return results


def read_nvm_file(nvm_path: str) -> list:
    """Reads camera poses from an NVM file generated by COLMAP.

    Args:
        nvm_path (str): path to the NVM file.

    Raises:
        Exception: Invalid nvm file format.

    Returns:
        list: list of dictionaries containing image filename, position, and quaternion.
    """
    camera_poses = []
    with open(nvm_path, 'r') as file:
        lines = file.readlines()
        if len(lines) < 3:
            raise Exception("Invalid NVM file format")

        num_cameras = int(lines[2].strip())
        for i in range(3, 3 + num_cameras):
            parts = lines[i].split()
            if len(parts) < 8:
                continue
            filename, _, qw, qx, qy, qz, tx, ty, tz = parts[:9]
            camera_poses.append({
                "filename": filename,
                "position": (float(tx), float(ty), float(tz)),
                "quaternion": (float(qw), float(qx), float(qy), float(qz))
            })

    return camera_poses


def compute_similarity_transform(pts_src: np.ndarray, pts_tgt: np.ndarray) -> Tuple[float, np.ndarray, np.ndarray]:
    """Computes the optimal similarity transformation (rotation, translation, scale).

    Args:
        pts_src (np.ndarray): points in source coordinate system.
        pts_tgt (np.ndarray): points in target coordinate system.

    Returns:
        Tuple[float, np.ndarray, np.ndarray]: scale, rotation, and translation.
    """
    # Center the points
    centroid_src = np.mean(pts_src, axis=0, dtype=np.float64)
    centroid_tgt = np.mean(pts_tgt, axis=0, dtype=np.float64)
    src_centered = (pts_src - centroid_src).astype(np.float64)
    tgt_centered = (pts_tgt - centroid_tgt).astype(np.float64)

    # Compute optimal rotation
    H = np.dot(src_centered.T, tgt_centered).astype(np.float64)
    U, S, Vt = np.linalg.svd(H)
    R_opt = np.dot(Vt.T, U.T).astype(np.float64)

    # Ensure a right-handed coordinate system
    if np.linalg.det(R_opt) < 0:
        Vt[-1, :] *= -1
        R_opt = np.dot(Vt.T, U.T).astype(np.float64)

    # Compute optimal scale and translation
    scale = np.sum(S) / np.sum(src_centered ** 2)
    t_opt = (centroid_tgt - scale * np.dot(R_opt,
             centroid_src)).astype(np.float64)

    return scale, R_opt, t_opt


def transform_save_ptc(filename: str, scale: float, rotation: np.ndarray, t: np.ndarray) -> None:
    """Reads a mesh or point cloud, applies the transformation, and saves it back.

    Raises:
        Exception: Error opening the file.

    Args:
        filename (str): name of the mesh file.
        scale (float): scale factor.
        rotation (np.ndarray): rotation matrix.
        t (np.ndarray): translation vector.
    """
    # Read the point cloud from the file
    try:
        pcd = o3d.io.read_point_cloud(filename)
    except Exception as e:
        raise Exception(f"Error opening the file {filename}: {e}")

    # Apply the transformation
    vertices = np.asarray(pcd.points, dtype=np.float64)
    vertices = (scale * (rotation @ vertices.T).T + t).astype(np.float64)
    pcd.points = o3d.utility.Vector3dVector(vertices)

    # Save the transformed point cloud
    o3d.io.write_point_cloud(filename, pcd)


def apply_transformation_to_nvm(nvm_path: str, scale: float, rotation: np.ndarray, translation: np.ndarray) -> None:
    """Applies the transformation to camera poses in the NVM file and saves the result.

    Args:
        nvm_path (str): path to the NVM file.
        scale (float): scale factor.
        rotation (np.ndarray): rotation matrix.
        translation (np.ndarray): translation vector.
    """
    with open(nvm_path, 'r') as file:
        lines = file.readlines()

    if len(lines) < 3:
        raise Exception("Invalid NVM file format")

    num_cameras = int(lines[2].strip())
    for i in range(3, 3 + num_cameras):
        parts = lines[i].split()
        # Only lines with 11 parts are considered camera poses
        if len(parts) != 11:
            continue
        # Camera pose and line content
        filename, focal_length, qw, qx, qy, qz, tx, ty, tz, c1, c2 = parts[:11]
        camera_position = np.array([float(tx), float(ty), float(tz)])
        camera_quaternion = np.array(
            [float(qw), float(qx), float(qy), float(qz)])
        camera_rotation = R.from_quat(
            camera_quaternion, scalar_first=True).as_matrix()

        # Apply transformation
        transformed_position = scale * \
            (rotation @ camera_position) + translation
        transformed_quaternion = R.from_matrix(
            camera_rotation @ rotation).as_quat(scalar_first=True)

        # Update the line with transformed values
        lines[i] = (
            f"{filename} {focal_length} "
            f"{transformed_quaternion[0]} {transformed_quaternion[1]} {transformed_quaternion[2]} {transformed_quaternion[3]} "
            f"{transformed_position[0]} {transformed_position[1]} {transformed_position[2]} "
            f"{c1} {c2}\n"
        )

    with open(nvm_path, 'w') as file:
        file.writelines(lines)


def main():
    """Main function to parse arguments and process images."""
    parser = argparse.ArgumentParser(
        description="Extract GPS data from images and compute transformation.")
    parser.add_argument("--folder", type=str, help="Path to the folder containing images.",
                        default="/home/grin/Downloads/small", required=False)
    parser.add_argument("--nvm", type=str, help="Path to the NVM file.",
                        default="/home/grin/Downloads/small_clouds/cameras.nvm", required=False)
    parser.add_argument("--cloud", type=str, help="Path to the point cloud (ply) to transform.",
                        default="/home/grin/Downloads/small_clouds/3DData/PointCloud.ply", required=False)
    parser.add_argument('--obj', help='Path to the OBJ file to transform',
                        default="/home/grin/Downloads/small_clouds/3DData/TexturedSurface/TexturedSurface.obj", required=False)
    args = parser.parse_args()

    # Describe the parameters
    print("Input parameters:", flush=True)
    print(f"Folder: {args.folder}", flush=True)
    print(f"NVM file: {args.nvm}", flush=True)
    print(f"Point cloud: {args.cloud}", flush=True)
    if args.obj and args.obj != "":
        print(f"OBJ: {args.obj}", flush=True)
    sys.stdout.flush()

    # Obtain GPS data from images and camera poses from NVM file
    print("Processing input images EXIF information ...", flush=True)
    sys.stdout.flush()
    utm_data = process_images(args.folder)
    print("Reading camera poses from NVM file ...", flush=True)
    sys.stdout.flush()
    camera_poses = read_nvm_file(args.nvm)

    # Match correspondent points according to image filenames
    print("Matching images and camera poses ...", flush=True)
    sys.stdout.flush()
    matched_utm = []
    matched_nvm = []
    for wgs_image_pose in utm_data:
        for scaled_image_pose in camera_poses:
            if os.path.basename(wgs_image_pose["filename"]) == os.path.basename(scaled_image_pose["filename"]):
                matched_utm.append(
                    [wgs_image_pose["utm_e"], wgs_image_pose["utm_n"], wgs_image_pose["altitude"]])
                matched_nvm.append(scaled_image_pose["position"])
                break

    # Compute similarity transformation and apply to point cloud, mesh, obj and NVM file
    print("Computing similarity transformation ...", flush=True)
    sys.stdout.flush()
    if len(matched_utm) >= 3:
        matched_utm = np.array(matched_utm)
        matched_nvm = np.array(matched_nvm)
        scale, global_R_scaled, global_t_scaled = compute_similarity_transform(
            matched_nvm, matched_utm)
        # Transform the points
        print("Applying transformation to point cloud ...", flush=True)
        sys.stdout.flush()
        transform_save_ptc(
            args.cloud, scale, global_R_scaled, global_t_scaled)
        print("Applying transformation to NVM file ...", flush=True)
        sys.stdout.flush()
        apply_transformation_to_nvm(
            args.nvm, scale, global_R_scaled, global_t_scaled)
        if args.obj != "":
            print("Applying transformation to OBJ file ...", flush=True)
            sys.stdout.flush()
            transformer = OBJTransformer()
            transformer.read_obj(args.obj)
            transformer.read_mtl()  # Read material file
            transformer.apply_transformation(
                scale=scale,
                quaternion=R.from_matrix(global_R_scaled).as_quat(
                    scalar_first=True).tolist(),
                translation=global_t_scaled.tolist()
            )
            transformer.save_obj(args.obj)
    else:
        print("Not enough matching points to compute transformation.", flush=True)
        sys.stdout.flush()

    print("All Done!", flush=True)
    sys.stdout.flush()


if __name__ == "__main__":
    main()
