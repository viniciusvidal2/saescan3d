import sys
import os
import trimesh
import numpy as np
import open3d as o3d
import pyvista as pv


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


def load_textured_mesh(obj_path: str) -> tuple:
    """Load a textured OBJ file into PyVista PolyData.

    Args:
        obj_path (str): Path to the OBJ file.
    Returns:
        tuple: A tuple containing the PyVista PolyData object and the texture.
    """
    # Load mesh with Trimesh
    scene_or_mesh = trimesh.load(obj_path, force='scene')    
    # If it’s a scene (multiple geometries), merge them
    if isinstance(scene_or_mesh, trimesh.Scene):
        combined = trimesh.util.concatenate(tuple(scene_or_mesh.geometry.values()))
    else:
        combined = scene_or_mesh
    # Get geometry data
    vertices = combined.vertices
    faces = combined.faces
    uvs = combined.visual.uv
    image = combined.visual.material.image
    # Convert to PyVista PolyData
    faces_pv = np.hstack([[3, *face] for face in faces])
    mesh = pv.PolyData(vertices, faces_pv)
    # Set texture coordinates
    if uvs is not None:
        mesh.active_t_coords = uvs
    # Convert texture
    if image is not None:
        texture = pv.numpy_to_texture(np.array(image))
    else:
        texture = None
    return mesh, texture
