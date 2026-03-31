from sys import exit
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QSplashScreen, QTextEdit,
    QHBoxLayout, QVBoxLayout, QLabel, QWidget, QFileDialog, QSplitter, QLineEdit
)
from PySide6.QtGui import QPixmap, QPalette, QBrush, QFont, QGuiApplication, QResizeEvent
from PySide6.QtCore import Qt, QTimer, QThread
from pyvistaqt import QtInteractor
import os
import numpy as np
import pyvista as pv
from modules.tools import get_file_placement_path
from modules.worker_sfm import WorkerSfm
from modules.worker_obj import WorkerObj


class Saescan3dWindow(QMainWindow):
    # region Main Window Creation
    def __init__(self) -> None:
        """Initialize the window with a background image and buttons.
        """
        super().__init__()
        # Title, icons, and position/sizes
        self.setWindowTitle("SfM Engine")
        self.setWindowIcon(
            QPixmap(get_file_placement_path("resources/saescan3d.ico")))
        # Center the window on the screen
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.geometry()
        window_geometry = self.frameGeometry()
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        self.move(x, y)
        # Background and main widget
        self.setup_background()
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #888;
                width: 6px;
                margin: 1px;
            }
        """)
        # Left panel layout - data input btns, process btns and text panel
        self.left_panel = QWidget()
        left_layout = QVBoxLayout(self.left_panel)
        self.setup_input_data_section(left_layout)
        self.setup_processing_section(left_layout)
        # Right panel with the label
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        self.setup_right_panel(right_layout)
        # Add the panels to the main layout
        splitter.addWidget(self.left_panel)
        splitter.addWidget(self.right_panel)
        splitter.setSizes([2 * self.width() // 3, self.width() // 3])
        main_layout.addWidget(splitter)
        # Create the SFM worker to process the data in a thread
        self.worker_sfm = WorkerSfm()
        self.thread = QThread()
        self.signals_connected = False  # Flag to prevent duplicate connections
        self.worker_sfm.moveToThread(self.thread)
        self.connect_worker_signals()
        self.thread.start()
        # Log splitter
        self.log_splitter = "--------------------------------"
        # Actors
        self.camera_actors = list()
        self.ptc_actor = None
        self.mesh_actor = None
        self.mesh_texture = None
        # Number of images to process, to see if we can run the SFM
        self.num_images = 0

    def setup_background(self) -> None:
        """Set up the background image for the main window.
        """
        self.background = QPixmap(
            get_file_placement_path("resources/background.png"))
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(self.background.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)))
        self.setPalette(palette)

    def setup_input_data_section(self, layout: QVBoxLayout) -> None:
        """Set up the btns for image and output folders.
        Args:
            layout (QVBoxLayout): The layout to add the btns to.
        """
        # Input images data
        images_input_layout = QHBoxLayout()
        label_style = "color: white; background-color: rgba(0,0,0,150); padding: 4px; border-radius: 4px;"
        images_input_label = QLabel("Input images folder:")
        images_input_label.setStyleSheet(label_style)
        self.images_text_edit = QLineEdit()
        self.images_text_edit.setPlaceholderText(
            "Path to the folder containing the input images.")
        self.images_browse_btn = QPushButton("Browse")
        self.images_browse_btn.clicked.connect(self.images_browse_btn_callback)
        images_input_layout.addWidget(images_input_label)
        images_input_layout.addWidget(self.images_text_edit)
        images_input_layout.addWidget(self.images_browse_btn)
        # Output data folder
        sfm_output_layout = QHBoxLayout()
        sfm_output_label = QLabel("Project folder:")
        sfm_output_label.setStyleSheet(label_style)
        self.sfm_output_text_edit = QLineEdit()
        self.sfm_output_text_edit.setPlaceholderText(
            "Path to the folder where the output will be saved.")
        self.sfm_output_browse_btn = QPushButton("Browse")
        self.sfm_output_browse_btn.clicked.connect(
            self.sfm_output_browse_btn_callback)
        sfm_output_layout.addWidget(sfm_output_label)
        sfm_output_layout.addWidget(self.sfm_output_text_edit)
        sfm_output_layout.addWidget(self.sfm_output_browse_btn)
        # Add the input layouts to the vertical layout
        layout.addLayout(images_input_layout)
        layout.addLayout(sfm_output_layout)

    def setup_processing_section(self, layout: QVBoxLayout) -> None:
        """Set up processing buttons and text panel for log.
        Args:
            layout (QVBoxLayout): The layout to add the items to.
        """
        # Buttons with processing calls
        self.process_btn_layout = QHBoxLayout()
        self.process_btn_layout.setAlignment(Qt.AlignTop)
        self.process_btn_layout.setSpacing(10)
        self.process_btn_layout.setContentsMargins(0, 0, 0, 0)
        self.process_sfm_btn = QPushButton("Run SfM")
        self.process_sfm_btn.setEnabled(True)
        self.process_sfm_btn.clicked.connect(self.process_sfm_btn_callback)
        self.process_btn_layout.addWidget(self.process_sfm_btn)
        # Text panel for logs and status
        self.text_panel = QTextEdit()
        self.text_panel.setPlaceholderText(
            "Logs, status, or descriptions here...")
        self.text_panel.setReadOnly(True)
        # Add everything to the left layout
        layout.addLayout(self.process_btn_layout)
        layout.addWidget(self.text_panel, stretch=1)

    def setup_right_panel(self, layout: QVBoxLayout) -> None:
        """Set up the right panel with the visualizer and option buttons.
        Args:
            layout (QVBoxLayout): The layout to add the items to.
        """
        # Pyvista visualizer
        self.visualizer = QtInteractor(self)
        self.visualizer.set_background(color="gray")
        self.visualizer.add_axes()
        # Buttons with visualizer options
        self.vis_btn_layout = QHBoxLayout()
        self.vis_btn_layout.setAlignment(Qt.AlignTop)
        self.vis_btn_layout.setSpacing(10)
        self.vis_btn_layout.setContentsMargins(0, 0, 0, 0)
        self.ptc_vis_btn = QPushButton("Point Cloud")
        self.ptc_vis_btn.setEnabled(True)
        self.ptc_vis_btn.clicked.connect(self.ptc_vis_btn_callback)
        self.mesh_vis_btn = QPushButton("Mesh")
        self.mesh_vis_btn.setEnabled(True)
        self.mesh_vis_btn.clicked.connect(self.mesh_vis_btn_callback)
        self.camera_btn = QPushButton("Show Cameras")
        self.camera_btn.setCheckable(True)
        self.camera_btn.setEnabled(True)
        self.camera_btn.setChecked(False)
        self.camera_btn.clicked.connect(self.camera_btn_callback)
        self.vis_btn_layout.addWidget(self.ptc_vis_btn)
        self.vis_btn_layout.addWidget(self.mesh_vis_btn)
        self.vis_btn_layout.addWidget(self.camera_btn)
        layout.addWidget(self.visualizer.interactor, stretch=1)
        layout.addLayout(self.vis_btn_layout)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Resize the contents when the window is resized.
        """
        # Resizing background
        scaled_bg = self.background.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(scaled_bg))
        self.setPalette(palette)
        super().resizeEvent(event)

    def closeEvent(self, event) -> None:
        """Close the application and stop the worker thread.
        """
        self.thread.quit()
        self.thread.wait()
        event.accept()

    def connect_worker_signals(self):
        """Connect the worker signals to the slots.
        """
        if self.signals_connected:
            return
        self.worker_sfm.log.connect(self.log_output)
        self.worker_sfm.finished.connect(self.enable_buttons)
        self.signals_connected = True
        self.thread.finished.connect(self.thread.deleteLater)

    # endregion
    # region Button Callbacks

    def images_browse_btn_callback(self) -> None:
        """Callback for the images browse button.
        """
        self.log_output(self.log_splitter)
        self.disable_buttons()
        # Open file dialog to select folder
        folder = QFileDialog.getExistingDirectory(
            self, "Select folder with the input images", "", QFileDialog.ShowDirsOnly)
        if folder:
            self.images_text_edit.setText(folder)
            self.log_output(f"Selected image data folder: {folder}")
            # List images in natural order in the folder and log them
            images = sorted([f for f in os.listdir(folder) if f.endswith(('.jpg', '.png', '.jpeg', '.JPG', '.PNG', '.JPEG'))],
                            key=lambda x: int(''.join(filter(str.isdigit, x))))
            self.num_images = len(images)
            self.log_output(f"Images found in the folder: {self.num_images}")
            if self.num_images == 0:
                self.log_output("No images found in the selected folder.")
                self.enable_buttons()
                return
            for img in images:
                self.log_output(f" - {os.path.basename(img)}")
            # Set the input folder in the worker
            self.worker_sfm.set_input_folder(self.images_text_edit.text())
        else:
            self.log_output("No folder selected.")
        self.enable_buttons()

    def sfm_output_browse_btn_callback(self) -> None:
        """Callback for the SFM output browse button.
        """
        self.log_output(self.log_splitter)
        self.disable_buttons()
        # Open file dialog to select folder
        folder = QFileDialog.getExistingDirectory(
            self, "Select folder to store the output SFM data", "", QFileDialog.ShowDirsOnly)
        if folder:
            self.sfm_output_text_edit.setText(folder)
            self.log_output(f"Selected project folder: {folder}")
            # Set the output folder in the worker
            self.worker_sfm.set_output_folder(folder)
            # If there is already point cloud data in the folder, log it
            if os.path.exists(os.path.join(folder, "pointCloud.ply")):
                self.log_output(
                    "Point cloud data already exists in the project folder.")
            # If there is already a mesh in the folder, log it
            if os.path.exists(os.path.join(folder, "Texturing", "texturedMesh.obj")):
                self.log_output(
                    "Mesh data already exists in the project folder.")
        else:
            self.log_output("No folder selected.")
        self.enable_buttons()

    def process_sfm_btn_callback(self) -> None:
        """Callback for the SFM process button.
        """
        self.log_output(self.log_splitter)
        # Check if the input folder is set
        if not self.images_text_edit.text() or not self.sfm_output_text_edit.text():
            self.log_output("Input images folder or project folder not set.")
            return
        if self.num_images < 2:
            self.log_output(
                "Not enough images to run the SfM process. At least 2 images are required.")
            return
        self.disable_buttons()
        # Set the input and output folders in the worker
        self.worker_sfm.set_input_folder(self.images_text_edit.text())
        self.worker_sfm.set_output_folder(self.sfm_output_text_edit.text())
        # Set the pipeline to run
        self.worker_sfm.set_pipeline("full")
        # Run the SFM process in a separate thread
        QTimer.singleShot(0, self.worker_sfm.run_pipeline_signal.emit)

    def ptc_vis_btn_callback(self) -> None:
        """Callback for the point cloud visualization button.
        """
        # Adding point cloud actor for visualization
        self.log_output(self.log_splitter)
        self.disable_buttons()
        self.log_output("Displaying point cloud...")
        ptc_polydata = self.worker_sfm.get_pyvista_cloud()
        if ptc_polydata is not None:
            # Remove the mesh actor from the visualizer if the name matches
            if self.mesh_actor is not None:
                self.visualizer.remove_actor(self.mesh_actor, reset_camera=False)
                self.mesh_actor = None
                self.mesh_texture = None
            # Create and add the point cloud actor
            self.ptc_actor = self.visualizer.add_mesh(
                ptc_polydata, scalars=ptc_polydata.point_data["RGB"], rgb=True, name="ptc_actor")
            self.prepare_actors_for_visualization()
            self.visualizer.show()
            self.log_output("Point Cloud data displayed.")
        else:
            self.log_output("No point cloud data available.")
        self.enable_buttons()

    def mesh_vis_btn_callback(self) -> None:
        """Callback for the mesh visualization button.
        """
        # Check if the mesh is available
        self.log_output(self.log_splitter)
        self.disable_buttons()
        self.log_output("Displaying mesh...")
        obj_path, mtl_path = self.worker_sfm.get_textured_mesh_paths()
        if obj_path == "" or mtl_path == "":
            self.log_output("No textured mesh data available.")
            self.enable_buttons()
            return
        # Remove the previous point cloud actor if it exists
        if self.ptc_actor is not None:
            self.visualizer.remove_actor(self.ptc_actor, reset_camera=False)
            self.ptc_actor = None
        # Load the mesh with texture in a separate thread so it does not block the window with big meshes
        if not self.mesh_actor:
            self.log_output(
                "Loading the mesh with texture. It will show up in the visualizer once it is loaded.")
            self.log_output(
                "It can take some time depending on the mesh size, please wait...")
            self.thread_obj = QThread()
            self.worker_obj = WorkerObj(obj_path=obj_path)
            self.worker_obj.moveToThread(self.thread_obj)
            self.thread_obj.started.connect(self.worker_obj.run)
            self.worker_obj.finished.connect(self._on_mesh_loaded)
            self.worker_obj.finished.connect(self.thread_obj.quit)
            self.worker_obj.finished.connect(self.worker_obj.deleteLater)
            self.thread_obj.finished.connect(self.thread_obj.deleteLater)
            self.thread_obj.start()
        else:
            self.log_output("Mesh already loaded, displaying it...")
            self.visualizer.reset_camera()
            self.visualizer.render()
            self.enable_buttons()

    def _on_mesh_loaded(self, mesh_actor: pv.PolyData, mesh_texture: pv.Texture) -> None:
        """Callback for when the mesh is loaded.
        Args:
            mesh_actor (pv.PolyData): The loaded mesh actor.
            mesh_texture (pv.Texture): The loaded mesh texture.
        """
        self.mesh_texture = mesh_texture
        self.mesh_actor = self.visualizer.add_mesh(
            mesh_actor, name="mesh_actor", texture=self.mesh_texture)
        self.visualizer.reset_camera()
        self.visualizer.render()
        self.log_output("Mesh loaded successfully.")
        self.prepare_actors_for_visualization()
        self.visualizer.show()
        self.log_output("Mesh data displayed.")
        self.enable_buttons()

    def camera_btn_callback(self) -> None:
        """Callback for the camera visualization button.
        """
        self.log_output(self.log_splitter)
        if self.camera_btn.isChecked():
            cameras = self.worker_sfm.get_cameras()
            # Check if cameras are available
            if not cameras:
                self.log_output("No camera data available.")
                self.camera_btn.setChecked(False)
                self.enable_buttons()
                return
            # Show the cameras by adding the actors
            self.log_output("Showing cameras...")
            self.camera_btn.setText("Hide Cameras")
            for cam in cameras.values():
                self.camera_actors.append(
                    self.visualizer.add_mesh(cam, color="red"))
            self.prepare_actors_for_visualization()
        else:
            # Remove the cameras by removing the actors
            if self.camera_actors:
                self.camera_btn.setText("Show Cameras")
                self.log_output("Hiding cameras...")
                for actor in self.camera_actors:
                    self.visualizer.remove_actor(actor, reset_camera=False)
                self.camera_actors.clear()
                self.prepare_actors_for_visualization()
            else:
                self.camera_btn.setChecked(True)
                self.log_output("No camera displayed for us to hide.")

    # endregion
    # region Tools

    def prepare_actors_for_visualization(self) -> None:
        """Prepare the actors for visualization by shifting to the center of the scene.
        """
        # Get the center of the scene
        center = self.worker_sfm.get_scene_center()
        # Shift the actors to the center
        for actor in list(self.visualizer.actors.values()):
            mesh = actor.GetMapper().GetInputAsDataSet()
            if mesh is not None:
                if np.linalg.norm(mesh.center) < 1e3:
                    continue
                mesh.points -= center
        self.visualizer.reset_camera()
        self.visualizer.render()

    # endregion
    # region Logging
    def log_output(self, msg: str) -> None:
        """Log output to the text panel.
        Args:
            msg (str): The message to log.
        """
        self.text_panel.append(msg)

    def disable_buttons(self) -> None:
        """Disable the buttons in the processing section.
        """
        self.process_sfm_btn.setEnabled(False)
        self.ptc_vis_btn.setEnabled(False)
        self.mesh_vis_btn.setEnabled(False)
        self.images_browse_btn.setEnabled(False)
        self.sfm_output_browse_btn.setEnabled(False)
        self.camera_btn.setEnabled(False)
        self.images_text_edit.setEnabled(False)
        self.sfm_output_text_edit.setEnabled(False)

    def enable_buttons(self) -> None:
        """Enable the buttons in the processing section.
        """
        self.process_sfm_btn.setEnabled(True)
        self.ptc_vis_btn.setEnabled(True)
        self.mesh_vis_btn.setEnabled(True)
        self.images_browse_btn.setEnabled(True)
        self.sfm_output_browse_btn.setEnabled(True)
        self.camera_btn.setEnabled(True)
        self.images_text_edit.setEnabled(True)
        self.sfm_output_text_edit.setEnabled(True)

    # endregion
# region Main call


def main() -> None:
    """Main function to run the application.
    """
    app = QApplication()

    # Splash screen
    original_pix = QPixmap(get_file_placement_path("resources/splash.png"))
    scaled_pix = original_pix.scaled(
        original_pix.width(),
        original_pix.height(),
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation)
    splash = QSplashScreen(scaled_pix)
    splash.setFont(QFont("Arial", 20))
    splash.show()

    # Animate "Loading..." text
    dots = ["", ".", "..", "..."]
    current_index = [0]  # Using list to make it mutable in closure

    def update_loading_text():
        splash.showMessage(f"Loading{dots[current_index[0]]}",
                           Qt.AlignCenter,
                           Qt.white)
        current_index[0] = (current_index[0] + 1) % len(dots)
    timer = QTimer()
    timer.timeout.connect(update_loading_text)
    timer.start(200)

    # After some seconds, close splash and open main window
    window = Saescan3dWindow()
    QTimer.singleShot(1000, timer.stop)
    QTimer.singleShot(1000, splash.close)
    QTimer.singleShot(1000, window.show)
    exit(app.exec())


if __name__ == '__main__':
    main()

# endregion
