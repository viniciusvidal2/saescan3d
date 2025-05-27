from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QSplashScreen, QTextEdit,
    QHBoxLayout, QVBoxLayout, QLabel, QWidget, QFileDialog, QSplitter, QLineEdit
)
from PySide6.QtGui import (
    QPixmap, QPalette, QBrush, QFont, QGuiApplication, QResizeEvent, QIcon
)
from PySide6.QtCore import Qt, QTimer, QThread
from pyvistaqt import QtInteractor
from sys import exit
import os
import pyvista as pv
import numpy as np
import shutil
from modules.tools import get_file_placement_path, read_pyvista_cloud
from modules.helper_distance_tool import (
    enable_point_selection_for_distance_measurement, disable_point_selection_for_distance_measurement
)
from modules.helper_area_tool import (
    enable_polygon_selection_for_area_measurement, disable_polygon_selection_for_area_measurement
)
from modules.helper_elevation_tool import (
    enable_elevation_tool, disable_elevation_tool
)
from modules.helper_delete_tool import (
    enable_box_selection_for_deletion, disable_box_selection_for_deletion
)
from modules.helper_volume_tool import (
    enable_volume_calculation, disable_volume_calculation
)
from modules.worker_obj import WorkerObj


class SmartmodelWindow(QMainWindow):
    # region Main Window Creation
    def __init__(self) -> None:
        """Initialize the window with a background image and buttons.
        """
        super().__init__()
        # Title, icons, and position/sizes
        self.setWindowTitle("Model Visualizer")
        self.setWindowIcon(QPixmap(get_file_placement_path("resources/smartmodel.ico")))
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
        # Left up panel layout - data input btns
        self.left_up_panel = QWidget()
        left_up_layout = QVBoxLayout(self.left_up_panel)
        self.setup_input_data_section(left_up_layout)
        # Left down panel layout - visualizer and tools
        self.left_down_panel = QWidget()
        self.left_down_panel.setStyleSheet("""
            QWidget {
                background-color: #e0e0e0;  /* Light gray */
                border: 2px solid #555;     /* Darker gray border */
                border-radius: 8px;         /* Optional rounded corners */
            }
        """)
        left_down_layout = QVBoxLayout(self.left_down_panel)
        self.setup_visualizer_section(left_down_layout)
        # Right panel with the text panel
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        self.setup_right_panel(right_layout)
        # Add the panels to the main layout
        self.left_panel = QWidget()
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.addWidget(self.left_up_panel)
        left_layout.addWidget(self.left_down_panel)
        splitter.addWidget(self.left_panel)
        splitter.addWidget(self.right_panel)
        splitter.setSizes([3 * self.width() // 4, self.width() // 4])
        main_layout.addWidget(splitter)
        # Log splitter
        self.log_splitter = "------------------"
        # Paths in the project
        self.ply_file_path = ""
        self.obj_file_path = ""
        self.mtl_file_path = ""
        # Actors and polydata variables
        self.mesh_actor = None
        self.mesh_texture = None
        self.ptc_actor = None
        
    def setup_background(self) -> None:
        """Set up the background image for the main window.
        """
        self.background = QPixmap(get_file_placement_path("resources/background.png"))
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(self.background.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)))
        self.setPalette(palette)

    def setup_input_data_section(self, layout: QVBoxLayout) -> None:
        """Set up the btns for HSX, RAW and BIN files.
        Args:
            layout (QVBoxLayout): The layout to add the btns to.
        """
        # Input point cloud or mesh file (PLY or OBJ)
        self.input_file_layout = QHBoxLayout()
        label_style = "color: white; background-color: rgba(0,0,0,150); padding: 4px; border-radius: 4px;"
        input_file_label = QLabel("Input file:")
        input_file_label.setStyleSheet(label_style)
        self.input_file_text_edit = QLineEdit()
        self.input_file_text_edit.setPlaceholderText(
            "Path to the input file (PLY or OBJ).")
        self.input_file_browse_btn = QPushButton("Browse")
        self.input_file_browse_btn.clicked.connect(self.input_file_browse_btn_callback)
        self.mesh_ptc_btn = QPushButton("Mesh the Point Cloud!")
        self.mesh_ptc_btn.setEnabled(False)
        self.mesh_ptc_btn.setVisible(False)
        self.mesh_ptc_btn.clicked.connect(self.mesh_ptc_btn_callback)
        self.input_file_layout.addWidget(input_file_label)
        self.input_file_layout.addWidget(self.input_file_text_edit)
        self.input_file_layout.addWidget(self.input_file_browse_btn)
        self.input_file_layout.addWidget(self.mesh_ptc_btn)
        # Add to the incoming layout
        layout.addLayout(self.input_file_layout)

    def setup_visualizer_section(self, layout: QVBoxLayout) -> None:
        """Set up buttons for interaction and the visualizer itself.
        Args:
            layout (QVBoxLayout): The layout to add the items to.
        """
        # Buttons with visualizer tools
        self.vis_btn_layout = QHBoxLayout()
        self.vis_btn_layout.setAlignment(Qt.AlignTop)
        self.vis_btn_layout.setSpacing(2)
        self.vis_btn_layout.setContentsMargins(0, 0, 0, 0)
        self.distance_tool_btn = QPushButton()
        self.distance_tool_btn.setIcon(QIcon(get_file_placement_path("resources/distanceOFF.ico")))
        self.distance_tool_btn.setToolTip("Calculate distance between points")
        self.distance_tool_btn.setEnabled(False)
        self.distance_tool_btn.setCheckable(True)
        self.distance_tool_btn.setChecked(False)
        self.distance_tool_btn.clicked.connect(self.distance_tool_btn_callback)
        self.area_tool_btn = QPushButton()
        self.area_tool_btn.setIcon(QIcon(get_file_placement_path("resources/areaOFF.ico")))
        self.area_tool_btn.setToolTip("Calculate area of interest")
        self.area_tool_btn.setEnabled(False)
        self.area_tool_btn.setCheckable(True)
        self.area_tool_btn.setChecked(False)
        self.area_tool_btn.clicked.connect(self.area_tool_btn_callback)
        self.volume_tool_btn = QPushButton()
        self.volume_tool_btn.setIcon(QIcon(get_file_placement_path("resources/volumeOFF.ico")))
        self.volume_tool_btn.setToolTip("Calculate mesh volume")
        self.volume_tool_btn.setEnabled(False)
        self.volume_tool_btn.setCheckable(True)
        self.volume_tool_btn.setChecked(False)
        self.volume_tool_btn.clicked.connect(self.volume_tool_btn_callback)
        self.delete_tool_btn = QPushButton()
        self.delete_tool_btn.setIcon(QIcon(get_file_placement_path("resources/deletePointsOFF.ico")))
        self.delete_tool_btn.setToolTip("Delete selected points")
        self.delete_tool_btn.setEnabled(False)
        self.delete_tool_btn.setCheckable(True)
        self.delete_tool_btn.setChecked(False)
        self.delete_tool_btn.clicked.connect(self.delete_tool_btn_callback)
        self.elevation_tool_btn = QPushButton()
        self.elevation_tool_btn.setIcon(QIcon(get_file_placement_path("resources/elevationOFF.ico")))
        self.elevation_tool_btn.setToolTip("Elevation tool")
        self.elevation_tool_btn.setEnabled(False)
        self.elevation_tool_btn.setCheckable(True)
        self.elevation_tool_btn.setChecked(False)
        self.elevation_tool_btn.clicked.connect(self.elevation_tool_btn_callback)
        self.vis_btn_layout.addWidget(self.distance_tool_btn)
        self.vis_btn_layout.addWidget(self.area_tool_btn)
        self.vis_btn_layout.addWidget(self.volume_tool_btn)
        self.vis_btn_layout.addWidget(self.delete_tool_btn)
        self.vis_btn_layout.addWidget(self.elevation_tool_btn)
        self.visualizer_tools_btns = [
            self.distance_tool_btn, self.area_tool_btn, self.volume_tool_btn, 
            self.delete_tool_btn, self.elevation_tool_btn
        ]
        # Pyvista visualizer
        self.visualizer = QtInteractor(self)
        self.visualizer.set_background(color="gray")
        self.visualizer.add_axes()
        # Add to the incoming layout
        layout.addLayout(self.vis_btn_layout)
        layout.addWidget(self.visualizer.interactor, stretch=1)

    def setup_right_panel(self, layout: QVBoxLayout) -> None:
        """Set up the right panel with the visualizer and option buttons.
        Args:
            layout (QVBoxLayout): The layout to add the items to.
        """
        # Text panel for logs and status
        self.text_panel = QTextEdit()
        self.text_panel.setPlaceholderText(
            "Logs, status, or descriptions here...")
        self.text_panel.setReadOnly(True)
        self.download_meshes_btn = QPushButton("Download Meshes")
        self.download_meshes_btn.setEnabled(False)
        self.download_meshes_btn.clicked.connect(self.download_meshes_btn_callback)        
        layout.addWidget(self.text_panel)
        layout.addWidget(self.download_meshes_btn)

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

    # endregion
    # region Input buttons Callbacks

    def input_file_browse_btn_callback(self) -> None:
        """Open a file dialog to select the input file.
        """
        self.log_output(self.log_splitter)
        self.disable_buttons()
        self.log_output("Opening file dialog to select input file...")
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Input File", "",
                                                   "OBJ or PLY Files (*.obj *.ply);;OBJ Files (*.obj);;PLY Files (*.ply)",
                                                   options=options)
        if file_path:
            self.input_file_text_edit.setText(file_path)
            # Do the proper processing according to the file type
            if file_path.endswith(".ply"):
                # We must create a mesh from the point cloud
                self.log_output("PLY file selected. Click 'Mesh the Point Cloud!' to process it and create a mesh.")
                self.mesh_ptc_btn.setVisible(True)
                self.mesh_ptc_btn.setEnabled(True)
                self.ply_file_path = file_path
                ptc_polydata = read_pyvista_cloud(self.ply_file_path)
                self.ptc_actor = self.visualizer.add_mesh(ptc_polydata, name="ptc_actor", 
                                                          scalars=ptc_polydata.point_data["RGB"], rgb=True)
                self.prepare_actors_for_visualization()
            elif file_path.endswith(".obj"):
                self.mesh_ptc_btn.setVisible(False)
                self.mesh_ptc_btn.setEnabled(False)
                # We must load the mesh from the OBJ file and its MTL file
                self.log_output("OBJ file selected. Reading the materials in the file directory...")
                self.obj_file_path = file_path
                self.mtl_file_path = file_path.replace(".obj", ".mtl")
                if not os.path.exists(self.mtl_file_path):
                    self.log_output("No MTL file found. Please ensure the OBJ file has a corresponding MTL file.")
                    self.log_output("Process wont run until the MTL file is found.")
                else:
                    # Load the mesh with texture in a separate thread so it does not block the window with big meshes
                    self.log_output("MTL file found. Loading the mesh with texture. It will show up in the visualizer once it is loaded.")
                    self.log_output("It can take some time depending on the mesh size, please wait...")
                    self.thread = QThread()
                    self.worker = WorkerObj(self.obj_file_path)
                    self.worker.moveToThread(self.thread)
                    self.thread.started.connect(self.worker.run)
                    self.worker.finished.connect(self._on_mesh_loaded)
                    self.worker.finished.connect(self.thread.quit)
                    self.worker.finished.connect(self.worker.deleteLater)
                    self.thread.finished.connect(self.thread.deleteLater)
                    self.thread.start()
        else:
            self.log_output("No file selected.")
            self.enable_buttons()

    def _on_mesh_loaded(self, mesh_actor: pv.PolyData, mesh_texture: pv.Texture) -> None:
        """Callback for when the mesh is loaded.
        Args:
            mesh_actor (pv.PolyData): The loaded mesh actor.
            mesh_texture (pv.Texture): The loaded mesh texture.
        """
        self.mesh_texture = mesh_texture
        self.mesh_actor = self.visualizer.add_mesh(mesh_actor, name="mesh_actor", texture=self.mesh_texture)
        self.prepare_actors_for_visualization()
        self.log_output("Mesh loaded successfully.")
        self.enable_buttons()
                    
    def mesh_ptc_btn_callback(self) -> None:
        """Callback for the mesh point cloud button.
        """
        self.log_output(self.log_splitter)
        self.log_output("Processing the point cloud to create a mesh...")
        # Apply a Delaunay triangulation to the point cloud
        ptc_polydata = self.ptc_actor.GetMapper().GetInput()
        mesh_polydata = ptc_polydata.delaunay_2d()
        # Update the mesh in the visualizer
        self.visualizer.remove_actor("ptc_actor")
        self.mesh_actor = self.visualizer.add_mesh(mesh_polydata, name="mesh_actor", 
                                                   scalars=mesh_polydata.point_data["RGB"], rgb=True, reset_camera=False)
        self.log_output("Mesh created successfully.")
        self.enable_buttons()

    def disable_other_tools(self, btn) -> None:
        """Disable all other tools except the one passed as argument.

        Args:
            btn (QPushButton): The button to keep enabled.
        """
        for button in self.visualizer_tools_btns:
            if button != btn:
                button.setChecked(False)
                button.setEnabled(False)

    def download_meshes_btn_callback(self) -> None:
        """Callback for the download meshes button.
        """
        self.log_output(self.log_splitter)
        self.log_output("Downloading meshes...")
        if self.ptc_actor is None and self.mesh_actor is None:
            self.log_output("No meshes to download. Please load a point cloud or mesh first.")
            self.enable_buttons()
            return
        # Get the folder to download the meshes to
        download_folder = QFileDialog.getExistingDirectory(self, "Select Download Folder",
                                                              options=QFileDialog.ShowDirsOnly)
        if not download_folder:
            self.log_output("No folder selected. Download cancelled.")
            self.enable_buttons()
            return
        self.log_output(f"Meshes will be downloaded to: {download_folder}")
        if self.ptc_actor is not None:
            # If there is a point cloud actor, we can save it and the mesh as a PLY files
            ply_file_path = os.path.join(download_folder, "pointCloud.ply")
            self.log_output(f"Saving point cloud to: {ply_file_path}")
            polydata=pv.wrap(self.ptc_actor.GetMapper().GetInput())
            polydata.save(ply_file_path, texture="RGB")
            if self.mesh_actor is not None:
                mesh_file_path = os.path.join(download_folder, "Mesh.ply")
                self.log_output(f"Saving mesh to: {mesh_file_path}")
                polydata = pv.wrap(self.mesh_actor.GetMapper().GetInput())
                polydata.save(mesh_file_path, texture="RGB")
        else:
            # There is only textured mesh loaded in our environment, so save it
            if self.mesh_actor is not None:
                source_obj_folder = os.path.dirname(self.obj_file_path)
                # Copy MTL file with textures to the download folder
                mtl_file_name = os.path.basename(self.mtl_file_path)
                mtl_file_path = os.path.join(download_folder, mtl_file_name)
                shutil.copy(self.mtl_file_path, mtl_file_path)
                for file in os.listdir(source_obj_folder):
                    if file.endswith(".png"):
                        # Copy texture files to the download folder
                        source_texture_path = os.path.join(source_obj_folder, file)
                        destination_texture_path = os.path.join(download_folder, file)
                        shutil.copy(source_texture_path, destination_texture_path)
                # Save the OBJ file with the MTL reference
                obj_file_name = os.path.basename(self.obj_file_path)
                obj_file_path = os.path.join(download_folder, obj_file_name)
                self.log_output(f"Saving mesh to: {obj_file_path}")
                polydata = pv.wrap(self.mesh_actor.GetMapper().GetInput())
                polydata.save(obj_file_path, texture=self.mesh_texture)
        # For now, we will just log that the button was clicked
        self.log_output("Meshes downloaded successfully.")
        self.enable_buttons()

    # endregion
    # region Visualizer tools Callbacks

    def distance_tool_btn_callback(self) -> None:
        """Callback for the distance tool button.
        """
        self.log_output(self.log_splitter)
        if self.distance_tool_btn.isChecked():
            self.log_output("Distance tool activated.")
            self.distance_tool_btn.setIcon(QIcon(get_file_placement_path("resources/distanceON.ico")))
            self.disable_other_tools(self.distance_tool_btn)
            enable_point_selection_for_distance_measurement(self)
        else:
            self.log_output("Distance tool deactivated.")
            self.distance_tool_btn.setIcon(QIcon(get_file_placement_path("resources/distanceOFF.ico")))
            disable_point_selection_for_distance_measurement(self)
            self.enable_buttons()

    def area_tool_btn_callback(self) -> None:
        """Callback for the area tool button.
        """
        self.log_output(self.log_splitter)
        if self.area_tool_btn.isChecked():
            self.log_output("Area tool activated.")
            self.area_tool_btn.setIcon(QIcon(get_file_placement_path("resources/areaON.ico")))
            self.disable_other_tools(self.area_tool_btn)
            enable_polygon_selection_for_area_measurement(self)
        else:
            self.log_output("Area tool deactivated.")
            self.area_tool_btn.setIcon(QIcon(get_file_placement_path("resources/areaOFF.ico")))
            disable_polygon_selection_for_area_measurement(self)
            self.enable_buttons()

    def volume_tool_btn_callback(self) -> None:
        """Callback for the volume tool button.
        """
        self.log_output(self.log_splitter)
        if self.volume_tool_btn.isChecked():
            self.log_output("Volume tool activated.")
            self.volume_tool_btn.setIcon(QIcon(get_file_placement_path("resources/volumeON.ico")))
            self.disable_other_tools(self.volume_tool_btn)
            enable_volume_calculation(self)
        else:
            self.log_output("Volume tool deactivated.")
            self.volume_tool_btn.setIcon(QIcon(get_file_placement_path("resources/volumeOFF.ico")))
            disable_volume_calculation(self)
            self.enable_buttons()

    def delete_tool_btn_callback(self) -> None:
        """Callback for the delete tool button.
        """
        self.log_output(self.log_splitter)
        if self.delete_tool_btn.isChecked():
            self.log_output("Delete tool activated.")
            self.delete_tool_btn.setIcon(QIcon(get_file_placement_path("resources/deletePointsON.ico")))
            self.disable_other_tools(self.delete_tool_btn)
            enable_box_selection_for_deletion(self)
        else:
            self.log_output("Delete tool deactivated.")
            self.delete_tool_btn.setIcon(QIcon(get_file_placement_path("resources/deletePointsOFF.ico")))
            disable_box_selection_for_deletion(self)
            self.enable_buttons()

    def elevation_tool_btn_callback(self) -> None:
        """Callback for the elevation tool button.
        """
        self.log_output(self.log_splitter)
        if self.elevation_tool_btn.isChecked():
            self.log_output("Elevation tool activated.")
            self.elevation_tool_btn.setIcon(QIcon(get_file_placement_path("resources/elevationON.ico")))
            self.disable_other_tools(self.elevation_tool_btn)
            enable_elevation_tool(self)
        else:
            self.log_output("Elevation tool deactivated.")
            self.elevation_tool_btn.setIcon(QIcon(get_file_placement_path("resources/elevationOFF.ico")))
            disable_elevation_tool(self)
            self.enable_buttons()

    def prepare_actors_for_visualization(self) -> None:
        """Prepare the actors for visualization by shifting to the center of the scene, avoiding UTM coordinates.
        """
        if self.mesh_actor is None:
            self.log_output("No mesh actor found. Please load a mesh first.")
            return
        # Get the center of the scene
        if not hasattr(self, 'scene_center'):
            self.scene_center = self.mesh_actor.GetMapper().GetInput().center
        # Shift the actors to the center
        for actor in list(self.visualizer.actors.values()):
            mesh_polydata = actor.GetMapper().GetInput()
            if np.linalg.norm(mesh_polydata.center) < 1e3:
                continue
            mesh_polydata.points -= self.scene_center
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
        self.input_file_browse_btn.setEnabled(False)
        if self.mesh_ptc_btn.isVisible():
            self.mesh_ptc_btn.setEnabled(False)
        self.distance_tool_btn.setEnabled(False)
        self.area_tool_btn.setEnabled(False)
        self.volume_tool_btn.setEnabled(False)
        self.delete_tool_btn.setEnabled(False)
        self.elevation_tool_btn.setEnabled(False)
        self.input_file_text_edit.setEnabled(False)
        self.download_meshes_btn.setEnabled(False)
        
    def enable_buttons(self) -> None:
        """Enable the buttons in the processing section.
        """
        self.input_file_browse_btn.setEnabled(True)
        if self.mesh_ptc_btn.isVisible():
            self.mesh_ptc_btn.setEnabled(True)
        self.distance_tool_btn.setEnabled(True)
        self.area_tool_btn.setEnabled(True)
        self.volume_tool_btn.setEnabled(True)
        self.delete_tool_btn.setEnabled(True)
        self.elevation_tool_btn.setEnabled(True)
        self.input_file_text_edit.setEnabled(True)
        self.download_meshes_btn.setEnabled(True)

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
    window = SmartmodelWindow()
    QTimer.singleShot(1000, timer.stop)
    QTimer.singleShot(1000, splash.close)
    QTimer.singleShot(1000, window.show)
    exit(app.exec())


if __name__ == '__main__':
    main()

# endregion
