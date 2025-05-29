import sys
import os
import trimesh
import numpy as np
import open3d as o3d
import pyvista as pv
import laspy



def get_file_placement_path(relative_path: str) -> str:
    """Get the absolute path to the resource, works for dev and for PyInstaller.

    Args:
        relative_path (str): Relative path to the resource.

    Returns:
        str: Absolute path to the resource.
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Normal script
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def convert_obj_to_ply(obj_path: str) -> o3d.geometry.PointCloud:
    """Load an OBJ file with texture and UV mapping into Open3D PointCloud.
    
    Args:
        obj_path (str): Path to the OBJ file.
    
    Returns:
        o3d.geometry.PointCloud: Open3D PointCloud object with vertex colors.
    """
    mesh = trimesh.load(obj_path, force='mesh', process=False)
    if not isinstance(mesh, trimesh.Trimesh):
        raise RuntimeError("Loaded object is not a mesh.")
    # Extract UV coordinates and texture image path
    uv = mesh.visual.uv
    material = mesh.visual.material
    if uv is None or not hasattr(material, 'image') or material.image is None:
        raise RuntimeError("Mesh has no UVs or texture image.")
    # Get texture image
    texture_image = material.image.convert("RGB")  # Ensure 3 channels
    texture_np = np.array(texture_image)
    # Map UV [0,1] to image coordinates (flip V axis)
    h, w, _ = texture_np.shape
    uv_img_coords = np.empty_like(uv)
    uv_img_coords[:, 0] = uv[:, 0] * (w - 1)
    uv_img_coords[:, 1] = (1.0 - uv[:, 1]) * (h - 1)
    uv_img_coords = np.rint(uv_img_coords).astype(int)
    uv_img_coords = np.clip(uv_img_coords, 0, [w - 1, h - 1])
    # Sample the texture to get per-vertex colors
    colors = texture_np[uv_img_coords[:, 1], uv_img_coords[:, 0]]
    # Create Open3D PointCloud
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(mesh.vertices)
    pcd.colors = o3d.utility.Vector3dVector(colors.astype(np.float32) / 255.0)
    return pcd


def parse_mtl_file(mtl_path: str) -> dict:
    """Parse the MTL file to get the material to texture mapping.

    Args:
        mtl_path (str): Path to the MTL file.

    Returns:
        dict: A dictionary mapping material names to texture file paths.
    """
    # Parse the MTL file to get the material to texture mapping
    material_to_texture = {}
    current_material = None
    with open(mtl_path, 'r') as file:
        for line in file:
            stripped = line.strip()
            if stripped.lower().startswith("newmtl"):
                current_material = stripped.split(None, 1)[1]
            elif stripped.lower().startswith("map_kd") and current_material:
                texture_file = stripped.split(None, 1)[1]
                material_to_texture[current_material] = texture_file
    return material_to_texture


def read_pyvista_cloud(ptc_path: str) -> pv.PolyData:
        """Read the cloud from the output folder with proper method to obtain double resolution in the points.

        Args:
            ptc_path (str): Path to the point cloud file.

        Returns:
            pv.PolyData: The point cloud.
        """
        # Read the point cloud and convert to pyvista
        point_cloud_o3d = o3d.io.read_point_cloud(ptc_path)
        point_cloud_polydata = pv.PolyData(np.asarray(point_cloud_o3d.points))
        # Add colors if they exist, create RGB array if not present
        if point_cloud_o3d.has_colors():
            point_cloud_polydata.point_data["RGB"] = (
                np.asarray(point_cloud_o3d.colors) * 255).astype(np.uint8)
        else:
            # Create a default RGB array if no colors are present
            point_cloud_polydata.point_data["RGB"] = np.full(
                (point_cloud_polydata.n_points, 3), 255, dtype=np.uint8)
        # Add normals if they exist
        if point_cloud_o3d.has_normals():
            point_cloud_polydata.point_data["Normals"] = np.asarray(point_cloud_o3d.normals)
        return point_cloud_polydata


def save_pyvista_cloud(ptc_path: str, format: str, utm_offset: np.ndarray, polydata: pv.PolyData, texture: pv.texture = None) -> bool:
    """Save the point cloud to a file.

    Args:
        ptc_path (str): Path to save the point cloud file.
        format (str): Format to save the point cloud, e.g., 'ply', 'las', 'xyz'.
        utm_offset (np.ndarray): UTM offset to apply to the point cloud coordinates.
        polydata (pv.PolyData): The point cloud to save.
        texture (pv.texture, optional): Texture to apply if saving as 'texture'.

    Returns:
        bool: True if the save was successful, False otherwise.
    """
    # Obj manipulation will be supported in the future
    if texture is not None:
        return False  # Texture saving not implemented here, return False
    # Properly extract points and set UTM offset
    polydata_to_save = polydata.copy()
    points = np.asarray(polydata_to_save.points).astype(np.float64) + utm_offset
    rgb = polydata_to_save.point_data["RGB"]
    if format.lower() == "las":
        # Scale if values are [0,1]
        if rgb.max() <= 1.0:
            rgb = (rgb * 255).astype(np.uint16)  
        else:
            rgb = rgb.astype(np.uint16)
        # Prepare LAS header
        header = laspy.LasHeader(point_format=3, version="1.2")  # Point format 3 supports RGB
        # Set offset and scale for 2 cm resolution
        header.x_scale = header.y_scale = header.z_scale = 0.02
        header.x_offset = points[:, 0].min()
        header.y_offset = points[:, 1].min()
        header.z_offset = points[:, 2].min()
        # Create LAS data
        las = laspy.LasData(header)
        # Set XYZ
        las.x = points[:, 0]
        las.y = points[:, 1]
        las.z = points[:, 2]
        # Set RGB (LAS expects 16-bit values for color)
        las.red = rgb[:, 0]
        las.green = rgb[:, 1]
        las.blue = rgb[:, 2]
        # Write to file
        las.write(ptc_path)
    elif format.lower() == "ply":
        if rgb.max() > 1.0:
            colors = rgb / 255.0
        else:
            colors = rgb.copy()
        colors = colors.astype(np.float64)
        # Create Open3D point cloud and save
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        pcd.colors = o3d.utility.Vector3dVector(colors)
        o3d.io.write_point_cloud(ptc_path, pcd, write_ascii=False)
    elif format.lower() == "xyz":
        # Convert RGB to uint8 [0, 255]
        if rgb.max() <= 1.0:
            rgb = (rgb * 255).astype(np.uint8)
        else:
            rgb = rgb.astype(np.uint8)
        # Write each line to a file as x y z r g b
        with open(ptc_path, 'w') as f:
            for point, color in zip(points, rgb):
                f.write(f"{point[0]:.10f} {point[1]:.10f} {point[2]:.10f} {int(color[0])} {int(color[1])} {int(color[2])}\n")
    return os.path.exists(ptc_path)
