from sys import exit
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QSplashScreen, QTextEdit,
    QHBoxLayout, QVBoxLayout, QLabel, QWidget, QFileDialog, QSplitter, QLineEdit
)
from PySide6.QtGui import (
    QPixmap, QPalette, QBrush, QFont, QGuiApplication, QResizeEvent, QIcon
)
from PySide6.QtCore import Qt, QTimer
from pyvistaqt import QtInteractor
from modules.tools import get_file_placement_path


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
        # Left panel layout - data input btns, process btns and text panel
        self.left_panel = QWidget()
        left_layout = QVBoxLayout(self.left_panel)
        self.setup_input_data_section(left_layout)
        self.setup_visualizer_section(left_layout)
        # Right panel with the label
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        self.setup_right_panel(right_layout)
        # Add the panels to the main layout
        splitter.addWidget(self.left_panel)
        splitter.addWidget(self.right_panel)
        splitter.setSizes([2 * self.width() // 3, self.width() // 3])
        main_layout.addWidget(splitter)
        # Log splitter
        self.log_splitter = "--------------------------------"
        
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
        self.distance_tool_btn.setToolTip("Mesh distance calculation tool")
        self.distance_tool_btn.setEnabled(True)
        self.distance_tool_btn.setCheckable(True)
        self.distance_tool_btn.setChecked(False)
        self.distance_tool_btn.clicked.connect(self.distance_tool_btn_callback)
        self.area_tool_btn = QPushButton()
        self.area_tool_btn.setIcon(QIcon(get_file_placement_path("resources/areaOFF.ico")))
        self.area_tool_btn.setToolTip("Mesh area calculation tool")
        self.area_tool_btn.setEnabled(True)
        self.area_tool_btn.setCheckable(True)
        self.area_tool_btn.setChecked(False)
        self.area_tool_btn.clicked.connect(self.area_tool_btn_callback)
        self.volume_tool_btn = QPushButton()
        self.volume_tool_btn.setIcon(QIcon(get_file_placement_path("resources/volumeOFF.ico")))
        self.volume_tool_btn.setToolTip("Mesh volume calculation tool")
        self.volume_tool_btn.setEnabled(True)
        self.volume_tool_btn.setCheckable(True)
        self.volume_tool_btn.setChecked(False)
        self.volume_tool_btn.clicked.connect(self.volume_tool_btn_callback)
        self.vis_btn_layout.addWidget(self.distance_tool_btn)
        self.vis_btn_layout.addWidget(self.area_tool_btn)
        self.vis_btn_layout.addWidget(self.volume_tool_btn)
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
        layout.addWidget(self.text_panel)

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

    def input_file_browse_btn_callback(self) -> None:
        """Open a file dialog to select the input file.
        """
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Input File", "",
                                                   "All Files (*);;PLY Files (*.ply);;OBJ Files (*.obj)",
                                                   options=options)
        if file_name:
            self.input_file_text_edit.setText(file_name)

    def mesh_ptc_btn_callback(self) -> None:
        pass

    def distance_tool_btn_callback(self) -> None:
        pass

    def area_tool_btn_callback(self) -> None:
        pass

    def volume_tool_btn_callback(self) -> None:
        pass

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
        self.mesh_ptc_btn.setEnabled(False)
        self.distance_tool_btn.setEnabled(False)
        self.area_tool_btn.setEnabled(False)
        self.volume_tool_btn.setEnabled(False)
        self.input_file_text_edit.setEnabled(False)
        
    def enable_buttons(self) -> None:
        """Enable the buttons in the processing section.
        """
        self.input_file_browse_btn.setEnabled(True)
        self.mesh_ptc_btn.setEnabled(True)
        self.distance_tool_btn.setEnabled(True)
        self.area_tool_btn.setEnabled(True)
        self.volume_tool_btn.setEnabled(True)
        self.input_file_text_edit.setEnabled(True)

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
