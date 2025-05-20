from PySide6.QtCore import QObject, Signal
import numpy as np
import trimesh
import pyvista as pv


class WorkerObj(QObject):
    # Signals to communicate with the main thread
    finished = Signal(object, object)
    error = Signal(str)

    def __init__(self, obj_path: str) -> None:
        """Initialize the WorkerObj class.

        Args:
            obj_path (str): Path to the OBJ file.
        """
        super().__init__()
        self.obj_path = obj_path

    def load_textured_mesh(self, obj_path: str) -> tuple:
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
            mesh.active_texture_coordinates = uvs
        # Convert texture
        if image is not None:
            texture = pv.numpy_to_texture(np.array(image))
        else:
            texture = None
        return mesh, texture

    def run(self) -> None:
        """Run the worker thread to load the OBJ file and emit signals.
        """
        try:
            mesh_actor, mesh_texture = self.load_textured_mesh(obj_path=self.obj_path)
            self.finished.emit(mesh_actor, mesh_texture)
        except Exception as e:
            self.error.emit(str(e))
