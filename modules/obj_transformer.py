import numpy as np
import argparse
from scipy.spatial.transform import Rotation
import os


class OBJTransformer:
    def __init__(self):
        """Class constructor to store vertices, faces, texture coordinates, and materials.
        """
        self.vertices = []
        self.faces = []
        self.texcoords = []
        self.texture_faces = []
        self.mtl_file = None
        self.materials = []
        self.current_material = None
        self.face_materials = []  # Store material for each face

    def read_obj(self, filename: str) -> None:
        """Read OBJ file and store vertices, faces, texture coordinates, and materials.

        Args:
            filename (str): Path to OBJ file
        """
        self.base_path = os.path.dirname(filename)

        with open(filename, 'r') as f:
            for line in f:
                if line.startswith('#'):
                    continue
                values = line.split()
                if not values:
                    continue
                if values[0] == 'mtllib':
                    # Material library
                    self.mtl_file = values[1]
                elif values[0] == 'usemtl':
                    # Material for subsequent faces
                    self.current_material = values[1]
                elif values[0] == 'v':
                    # Vertex
                    self.vertices.append([float(x) for x in values[1:4]])
                elif values[0] == 'vt':
                    # Texture coordinate
                    self.texcoords.append([float(x) for x in values[1:3]])
                elif values[0] == 'f':
                    # Face
                    face = []
                    tex_face = []
                    for v in values[1:]:
                        w = v.split('/')
                        face.append(int(w[0]) - 1)
                        if len(w) >= 2 and w[1]:
                            tex_face.append(int(w[1]) - 1)
                    self.faces.append(face)
                    if tex_face:
                        self.texture_faces.append(tex_face)
                    self.face_materials.append(self.current_material)

    def read_mtl(self, filename: str) -> None:
        """Read MTL file to get material and texture information.

        Args:
            filename (str): Path to MTL file
        """
        current_material = None
        self.material_textures = {}  # Store texture file for each material
        mtl_path = filename
        with open(mtl_path, 'r') as f:
            for line in f:
                if line.startswith('#'):
                    continue
                values = line.split()
                if not values:
                    continue
                if values[0] == 'newmtl':
                    current_material = values[1]
                    self.materials.append(current_material)
                elif values[0] == 'map_Kd' and current_material:
                    # Diffuse texture map
                    self.material_textures[current_material] = values[1]

    def apply_transformation(self, scale: float, quaternion: list, translation: list) -> None:
        """Apply transformation to vertices using scale, quaternion, and translation.

        Args:
            scale (float): scaling factor
            quaternion (list): quaternion rotation (x, y, z, w)
            translation (list): translation vector (x, y, z)
        """
        vertices = np.array(self.vertices)
        # Create rotation object from quaternion (x, y, z, w)
        rotation_matrix = Rotation.from_quat(
            quaternion).as_matrix()
        # Create 4x4 transformation matrix
        transform = np.eye(4)
        transform[:3, :3] = scale * rotation_matrix
        transform[:3, 3] = translation
        # Apply transformation to vertices
        vertices_homogeneous = np.hstack(
            (vertices, np.ones((vertices.shape[0], 1))))
        transformed_vertices = np.dot(vertices_homogeneous, transform.T)
        # Convert back to 3D coordinates
        self.vertices = transformed_vertices[:, :3].tolist()

    def save_obj(self, filename: str) -> None:
        """Save transformed model to new OBJ file and copy associated texture files.

        Args:
            filename (str): Path to save transformed OBJ file
        """
        output_path = os.path.dirname(filename)
        if not output_path:
            output_path = '.'

        with open(filename, 'w') as f:
            # Write material library reference
            if self.mtl_file:
                f.write(f'mtllib {self.mtl_file}\n')
            # Write vertices
            for v in self.vertices:
                f.write(f'v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n')
            # Write texture coordinates
            for vt in self.texcoords:
                f.write(f'vt {vt[0]:.6f} {vt[1]:.6f}\n')
            # Write faces with materials and texture coordinates
            current_material = None
            for i, face in enumerate(self.faces):
                # Write material change if needed
                if self.face_materials[i] != current_material:
                    current_material = self.face_materials[i]
                    if current_material:
                        f.write(f'usemtl {current_material}\n')
                f.write('f')
                for j, vertex_idx in enumerate(face):
                    if self.texture_faces:
                        tex_idx = self.texture_faces[i][j]
                        f.write(f' {vertex_idx + 1}/{tex_idx + 1}')
                    else:
                        f.write(f' {vertex_idx + 1}')
                f.write('\n')
