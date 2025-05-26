import sys
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6 import QtWidgets
from worker_obj import WorkerObj
from PySide6.QtCore import Qt, QTimer, QThread


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Volume Tool study")
        self.setGeometry(100, 100, 800, 600)

        # Central Widget
        self.frame = QtWidgets.QFrame()
        self.layout = QtWidgets.QVBoxLayout()
        self.frame.setLayout(self.layout)
        self.setCentralWidget(self.frame)

        # QtInteractor
        self.plotter = QtInteractor(self.frame)
        self.layout.addWidget(self.plotter.interactor)

        # Button to perform clipping
        self.button = QtWidgets.QPushButton("Clip Mesh")
        self.layout.addWidget(self.button)
        self.button.clicked.connect(self.perform_clipping)

        # Create the mesh
        self.thread = QThread()
        self.worker = WorkerObj("sample_low/out/Texturing/texturedMesh.obj")
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_mesh_loaded)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def _on_mesh_loaded(self, mesh_polydata: pv.PolyData, mesh_texture: pv.Texture) -> None:
        """Callback for when the mesh is loaded.
        Args:
            mesh_polydata (pv.PolyData): The loaded mesh actor.
            mesh_texture (pv.Texture): The loaded mesh texture.
        """
        self.mesh_polydata = mesh_polydata.delaunay_2d()
        self.mesh_texture = mesh_texture
        self.mesh_actor = self.plotter.add_mesh(self.mesh_polydata, name="mesh_actor", texture=self.mesh_texture)
        self.prepare_actors_for_visualization()
        # Setup Box Widget - xMin, xMax, yMin, yMax, zMin, zMax boundaries
        self.box_widget = None
        self.box_bounds = (-10.5, 10.5, -10.5, 10.5, -10.5, 10.5)
        self.create_box_widget()

    def prepare_actors_for_visualization(self) -> None:
        """Prepare the actors for visualization by shifting to the center of the scene.
        """
        # Get the center of the scene
        center = self.mesh_polydata.center
        # Shift the actors to the center
        for actor in list(self.plotter.actors.values()):
            mesh = actor.GetMapper().GetInputAsDataSet()
            if mesh is not None:
                if np.linalg.norm(mesh.center) < 1e3:
                    continue
                mesh.points -= center
        self.plotter.reset_camera()
        self.plotter.render()

    def create_box_widget(self):
        """Create the draggable box widget."""
        def callback(box):
            self.box_bounds = box.bounds  # Save updated bounds
            self.box_widget_points = box.points.reshape(-1, 3)
            # Add the Z-min plane
            planes = self.get_planes_from_box_widget()
            extrude_plane, extrude_direction = self.get_extrude_plane(plane=planes["Z-min"])
            self.plotter.add_mesh(extrude_plane, color='red', opacity=0.6, name="extrude_plane_helper")
            # Add arrow to indicate extrusion direction
            arrow_length = np.linalg.norm(self.box_widget_points[13][2] - self.box_widget_points[12][2]) / 3
            arrow = pv.Arrow(start=extrude_plane.center, direction=-extrude_direction, scale=arrow_length)
            self.plotter.add_mesh(arrow, color='red', name="extrude_direction_arrow_helper")


        self.box_widget = self.plotter.add_box_widget(
            callback=callback,
            bounds=self.box_bounds,
            rotation_enabled=True,
            color='red'
        )

    def perform_clipping(self):
        """Clip the sphere using the box's planes."""
        planes = self.get_planes_from_box_widget()
        extrude_plane, extrude_direction = self.get_extrude_plane(plane=planes["Z-min"])
        clipped_mesh = self.mesh_polydata.clip(normal=extrude_direction, origin=extrude_plane.center, invert=True, progress_bar=False)
        if clipped_mesh.n_points == 0:
            print("No points in the clipped mesh. Exiting clipping operation.")
            return
        extruded_mesh = clipped_mesh.extrude_trim(direction=extrude_direction, trim_surface=extrude_plane, extrusion="boundary_edges")
        clipped = extruded_mesh.copy()
        for name, plane in planes.items():
            if name == "Z-min":
                continue
            print(f"Clipping with plane: {name}")
            normal = plane["normal"]
            origin = plane["origin"]
            clipped = clipped.clip_closed_surface(
                normal=normal,
                origin=origin,
                progress_bar=False,
            )
        if not clipped.is_manifold:
            print("Clipped mesh is not manifold.")
        volume = clipped.volume

        self.plotter.clear_actors()
        self.plotter.add_mesh(self.mesh_polydata, name="mesh_actor", texture=self.mesh_texture, label="Original Mesh")
        self.plotter.add_mesh(clipped_mesh, color='blue', opacity=0.8, label="Clipped Original Mesh")
        self.plotter.add_mesh(clipped, color='orange', opacity=0.6, label="Extruded Volume")
        self.plotter.add_mesh(extrude_plane, style='wireframe', color='red', label="Extrude Plane")
        self.plotter.add_text(
            f"Clipped Volume: {volume:.3f} cubic units",
            position='upper_left',
            font_size=12,
            color='black'
        )
        self.plotter.add_axes()
        self.plotter.add_legend()

    def get_planes_from_box_widget(self):
        """Compute planes (origin, normal) from box mesh faces."""
        center = self.box_widget_points[-1]

        # Mapping of faces to their midpoints and corner points
        faces = {
            "X-min": {"origin_idx": 8, "corner_indices": [0, 3, 4, 7]},
            "X-max": {"origin_idx": 9, "corner_indices": [1, 2, 5, 6]},
            "Y-min": {"origin_idx": 10, "corner_indices": [0, 1, 4, 5]},
            "Y-max": {"origin_idx": 11, "corner_indices": [2, 3, 6, 7]},
            "Z-min": {"origin_idx": 12, "corner_indices": [0, 1, 2, 3]},
            "Z-max": {"origin_idx": 13, "corner_indices": [4, 5, 6, 7]},
        }

        face_info = {}
        for name, info in faces.items():
            origin = self.box_widget_points[info["origin_idx"]]
            face_corners = self.box_widget_points[info["corner_indices"]]

            # Compute two edge vectors
            v1 = face_corners[1] - face_corners[0]
            v2 = face_corners[3] - face_corners[0]
            normal = np.cross(v1, v2)
            normal /= np.linalg.norm(normal)  # Normalize

            # Ensure normal points inwards
            to_center = center - origin
            if np.dot(normal, to_center) < 0:
                normal = -normal

            face_info[name] = {
                "origin": origin,
                "normal": normal,
                "corners": face_corners,
            }

        return face_info
    
    def get_extrude_plane(self, plane: dict) -> tuple:
        """Get the extrude plane and direction based on the provided plane.
        
        Args:
            plane (dict): A dictionary containing the origin and normal of the plane.
        
        Returns:
            tuple: A tuple containing the extrude plane (as a PolyData) and the extrude direction (as a numpy array).
        """
        origin = np.array(plane["origin"])
        normal = np.array(plane["normal"])
        i_size = np.linalg.norm(plane["corners"][0] - plane["corners"][1])
        j_size = np.linalg.norm(plane["corners"][0] - plane["corners"][3])
        # Create a plane mesh
        extrude_plane = pv.Plane(center=origin, direction=normal, i_size=i_size, j_size=j_size)
        # Define the extrude direction as the negative of the normal
        extrude_direction = -normal
        return extrude_plane, extrude_direction


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
