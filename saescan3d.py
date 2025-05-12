from sys import exit
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QSplashScreen, QTextEdit,
    QHBoxLayout, QVBoxLayout, QLabel, QWidget, QFileDialog, QSplitter, QLineEdit
)
from PySide6.QtGui import QPixmap, QPalette, QBrush, QFont, QGuiApplication, QResizeEvent
from PySide6.QtCore import Qt, QTimer
from pyvistaqt import QtInteractor
from modules.path_tool import get_file_placement_path


class MainWindow(QMainWindow):
    # region Main Window Creation
    def __init__(self) -> None:
        """Initialize the main window with a background image and buttons.
        """
        super().__init__()
        # Title, icons, and position/sizes
        self.setWindowTitle("SAEScan3D")
        self.setWindowIcon(QPixmap(get_file_placement_path("resources/saescan3d.ico")))
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
        sfm_output_label = QLabel("Output folder:")
        sfm_output_label.setStyleSheet(label_style)
        self.sfm_output_text_edit = QLineEdit()
        self.sfm_output_text_edit.setPlaceholderText(
            "Path to the folder where the output will be saved.")
        self.sfm_output_browse_btn = QPushButton("Browse")
        self.sfm_output_browse_btn.clicked.connect(self.sfm_output_browse_btn_callback)
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
        self.process_sfm_btn = QPushButton("Run SFM")
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
        self.vis_btn_layout.addWidget(self.ptc_vis_btn)
        self.vis_btn_layout.addWidget(self.mesh_vis_btn)
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

    # endregion
    # region Button Callbacks
    def images_browse_btn_callback(self) -> None:
        """Callback for the images browse button.
        """
        # Open file dialog to select folder
        folder = QFileDialog.getExistingDirectory(
            self, "Select folder with the input images", "", QFileDialog.ShowDirsOnly)
        if folder:
            self.images_text_edit.setText(folder)

    def sfm_output_browse_btn_callback(self) -> None:
        """Callback for the SFM output browse button.
        """
        # Open file dialog to select folder
        folder = QFileDialog.getExistingDirectory(
            self, "Select folder to store the output SFM data", "", QFileDialog.ShowDirsOnly)
        if folder:
            self.images_text_edit.setText(folder)

    def process_sfm_btn_callback(self) -> None:
        """Callback for the SFM process button.
        """
        # Placeholder for SFM processing
        self.text_panel.append("Running SFM...")
        # Here you would call the actual SFM processing function
    
    def ptc_vis_btn_callback(self) -> None:
        """Callback for the point cloud visualization button.
        """
        # Placeholder for point cloud visualization
        self.text_panel.append("Visualizing Point Cloud...")
        # Here you would call the actual point cloud visualization function

    def mesh_vis_btn_callback(self) -> None:
        """Callback for the mesh visualization button.
        """
        # Placeholder for mesh visualization
        self.text_panel.append("Visualizing Mesh...")
        # Here you would call the actual mesh visualization function
    # endregion


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

    # After 6 seconds, close splash and open main window
    window = MainWindow()
    QTimer.singleShot(1000, timer.stop)
    QTimer.singleShot(1000, splash.close)
    QTimer.singleShot(1000, window.show)
    exit(app.exec())


if __name__ == '__main__':
    main()
