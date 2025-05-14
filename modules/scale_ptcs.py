import numpy as np
import open3d as o3d
import utm
from typing import Tuple
from scipy.spatial.transform import Rotation as R
import json
from modules.obj_transformer import OBJTransformer


def convert_to_degrees(value: str, ref: str) -> float:
    """Converts GPS coordinates to degrees.

    Args:
        value (str): coordinates in degrees, minutes, seconds.
        ref (str): hemisphere reference.

    Returns:
        float: the coordinates in degrees.
    """
    d, m, s = value.split(",")
    degrees = float(d) + (float(m) / 60.0) + (float(s) / 3600.0)
    if ref in ['S', 'W']:
        degrees = -degrees
    return degrees


def read_sfm_file(sfm_path: str) -> tuple:
    """Reads camera poses and correspondent GPS info from SFM file.

    Args:
        sfm_path (str): path to the SFM file.

    Returns:
        tuple: tuple with positions for both GPS and local coordinates.
    """
    # Load the SFM file
    with open(sfm_path, "r") as f:
        sfm_data = json.load(f)
    # Define the rotation matrix to fix the coordinate system
    R_fix = np.array([
            [1,  0,  0],
            [0, -1,  0],
            [0,  0, -1]
        ], dtype=np.float64)
    # Extract GPS and camera points
    gps_points = []
    camera_points = []
    camera_info = {}
    views = sfm_data.get("views", [])
    poses = {pose["poseId"]: pose for pose in sfm_data.get("poses", [])}
    for view in views:
        pose_id = view.get("poseId")
        if pose_id is None or pose_id not in poses:
            continue
        # Extract GPS data
        metadata = view.get("metadata", {})
        lat = convert_to_degrees(
            metadata.get("GPS:Latitude"), metadata.get("GPS:LatitudeRef"))
        lon = convert_to_degrees(
            metadata.get("GPS:Longitude"), metadata.get("GPS:LongitudeRef"))
        alt = metadata.get("GPS:Altitude", None)
        # Convert GPS to UTM coordinates
        if lat is not None and lon is not None and alt is not None:
            utm_coords = utm.from_latlon(lat, lon)
            gps_points.append((utm_coords[0], utm_coords[1], alt))
        # Extract camera pose
        pose = poses[pose_id]
        transform = pose["pose"]["transform"]
        center = np.array([float(x) for x in transform["center"]])
        rotation = np.array([float(x) for x in transform.get("rotation", None)])
        rotation = rotation.reshape((3, 3))
        position = R_fix @ center
        # Use center and if quaternion is not provided, use rotation matrix
        camera_points.append(position)
        camera_info[pose_id] = {
            "position": position,
            "orientation": rotation
        }
    return np.array(gps_points, dtype=np.float64), np.array(camera_points, dtype=np.float64)


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


def transform_data_frames(sfm_path: str, cloud_path: str, obj_path: str, mtl_path: str) -> None:
    """Transforms the point cloud and OBJ file to the UTM coordinate system.

    Args:
        sfm_path (str): path to the SFM file.
        cloud_path (str): path to the point cloud file.
        obj_path (str): path to the OBJ file.
        mtl_path (str): path to the MTL file.
    """
    # Reading SFM file
    utm_points, camera_points = read_sfm_file(sfm_path=sfm_path)
    # Compute similarity transformation and apply to point cloud and obj files
    scale, global_R_scaled, global_t_scaled = compute_similarity_transform(
        pts_src=camera_points, pts_tgt=utm_points)
    # Convert rotation matrix to quaternion (x, y, z, w)
    quaternion_scalar_last = R.from_matrix(global_R_scaled).as_quat()
    # Transform the points in the point cloud
    transform_save_ptc(
        filename=cloud_path, scale=scale, rotation=global_R_scaled, t=global_t_scaled)
    # Transform the points in the OBJ file
    transformer = OBJTransformer()
    transformer.read_obj(filename=obj_path)
    transformer.read_mtl(filename=mtl_path)
    transformer.apply_transformation(
        scale=scale,
        quaternion=quaternion_scalar_last.tolist(),
        translation=global_t_scaled.tolist()
    )
    transformer.save_obj(filename=obj_path)


if __name__ == "__main__":
    # Example usage
    sfm_path = "D:\\datasets_sfm\\balsa-small\\out\\cameras.sfm"
    cloud_path = "D:\\datasets_sfm\\balsa-small\\out\\pointCloud.ply"
    obj_path = "D:\\datasets_sfm\\balsa-small\\out\\Texturing\\texturedMesh.obj"
    mtl_path = "D:\\datasets_sfm\\balsa-small\\out\\Texturing\\texturedMesh.mtl"
    print("Please provide the paths to the SFM file, point cloud file, and OBJ file.")
    transform_data_frames(sfm_path=sfm_path,
                          cloud_path=cloud_path,
                          obj_path=obj_path,
                          mtl_path=mtl_path)
    print("Transformation completed.")
