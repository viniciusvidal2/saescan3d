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
        self.setWindowTitle("PyVista Box Clip Example")
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
        self.button = QtWidgets.QPushButton("Clip Sphere")
        self.layout.addWidget(self.button)
        self.button.clicked.connect(self.perform_clipping)

        # Create the sphere
        # self.mesh_actor = pv.Sphere(radius=1.0, center=(0, 0, 0))
        self.thread = QThread()
        self.worker = WorkerObj("sample_low/out/Texturing/texturedMesh.obj")
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_mesh_loaded)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

        # self.plotter.add_mesh(self.mesh_actor, style='wireframe', color='blue', label="Sphere")

        # # Setup Box Widget - xMin, xMax, yMin, yMax, zMin, zMax boundaries
        # self.box_widget = None
        # self.box_bounds = (-0.5, 0.5, -0.5, 0.5, -0.5, 0.5)
        # self.create_box_widget()

    def _on_mesh_loaded(self, mesh_actor: pv.PolyData, mesh_texture: pv.Texture) -> None:
        """Callback for when the mesh is loaded.
        Args:
            mesh_actor (pv.PolyData): The loaded mesh actor.
            mesh_texture (pv.Texture): The loaded mesh texture.
        """
        self.mesh_actor = mesh_actor.delaunay_2d()
        self.mesh_texture = mesh_texture
        self.plotter.add_mesh(self.mesh_actor, name="mesh_actor")#, texture=self.mesh_texture)
        self.prepare_actors_for_visualization()
        # Setup Box Widget - xMin, xMax, yMin, yMax, zMin, zMax boundaries
        self.box_widget = None
        self.box_bounds = (-10.5, 10.5, -10.5, 10.5, -10.5, 10.5)
        self.create_box_widget()

    def prepare_actors_for_visualization(self) -> None:
        """Prepare the actors for visualization by shifting to the center of the scene.
        """
        # Get the center of the scene
        center = self.mesh_actor.center
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

        self.box_widget = self.plotter.add_box_widget(
            callback=callback,
            bounds=self.box_bounds,
            rotation_enabled=True,
            color='red'
        )

    def perform_clipping(self):
        """Clip the sphere using the box's planes."""
        box = pv.Box(bounds=self.box_bounds)

        planes = self.get_planes_from_box(box)
        
        clipped = self.mesh_actor
        for plane in planes.values():
            normal = plane["normal"]
            origin = plane["origin"]
            clipped = clipped.clip_closed_surface(
                normal=normal,
                origin=origin,
                progress_bar=False,
            )

        volume = clipped.volume
        print(f"Clipped volume: {volume:.3f} cubic units")

        self.plotter.clear_actors()
        self.plotter.add_mesh(self.mesh_actor, style='wireframe', color='blue', label="Sphere")
        self.plotter.add_mesh(clipped, color='orange', opacity=0.6, label="Clipped")
        self.plotter.add_axes()
        self.plotter.add_legend()

    def get_planes_from_box(self, box):
        """Compute planes (origin, normal) from box mesh faces."""
        # Get the center of the box
        center = np.mean(box.points, axis=0)
        # Define faces by point indices
        faces = {
            "X-min": [0, 2, 6, 4],
            "X-max": [1, 3, 7, 5],
            "Y-min": [0, 1, 5, 4],
            "Y-max": [2, 3, 7, 6],
            "Z-min": [0, 1, 3, 2],
            "Z-max": [4, 5, 7, 6],
        }
        # Compute midpoints and inwards normals
        face_info = {}
        for name, idx in faces.items():
            corners = box.points[idx]
            face_center = corners.mean(axis=0)

            # Calculate two edge vectors on the face
            v1 = corners[1] - corners[0]
            v2 = corners[3] - corners[0]
            normal = np.cross(v1, v2)
            normal /= np.linalg.norm(normal)  # Normalize

            # Check if normal points inwards; if not, flip it
            to_face = face_center - center
            if np.dot(normal, to_face) > 0:
                normal = -normal

            face_info[name] = {
                "origin": face_center,
                "normal": normal,
                "corners": corners,
            }

        return face_info


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
