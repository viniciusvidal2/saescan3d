from sys import exit
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QSplashScreen,
    QHBoxLayout, QVBoxLayout, QLabel, QWidget, QSizePolicy
)
from PySide6.QtGui import QPixmap, QPalette, QBrush, QFont, QGuiApplication
from PySide6.QtCore import Qt, QTimer
from windows.saescan3d_window import Saescan3dWindow
from windows.smartmodel_window import SmartmodelWindow
from modules.tools import get_file_placement_path


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        """Initialize the main window with a background image and buttons.
        The main window contains buttons to open different functionalities of the application.
        The buttons are connected to their respective functions which open new windows.
        """
        super().__init__()
        # The windows we can open from the main interface
        self.child_windows = []
        # Variables to control labels
        self.label_size = (300, 180)
        self.saescan3d_label_path = get_file_placement_path("resources/saescan3d.png")
        self.smartmodel_label_path = get_file_placement_path("resources/smartmodel.png")
        # Title, icons, and position/sizes
        self.setWindowTitle("SAEScan3D")
        self.setWindowIcon(QPixmap(get_file_placement_path("resources/saescan3d.ico")))
        self.setFixedWidth(500)
        self.setFixedHeight(self.label_size[1])
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.geometry()
        window_geometry = self.frameGeometry()
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        self.move(x, y)
        # Background
        self.setup_background()
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        # Left panel with the buttons
        self.left_panel = QWidget()
        left_layout = QVBoxLayout(self.left_panel)
        self.setup_buttons(left_layout)
        # Right panel with the label
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        self.setup_label_panel(right_layout)
        # Add the panels to the main layout
        main_layout.addWidget(self.left_panel)
        main_layout.addWidget(self.right_panel)

    def setup_background(self) -> None:
        """Set up the background image for the main window.
        """
        self.background = QPixmap(get_file_placement_path("resources/background.png"))
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(self.background.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)))
        self.setPalette(palette)

    def resizeEvent(self, event: None) -> None:
        """Resize the contents when the window is resized.
        """
        # Resizing background
        scaled_bg = self.background.scaled(
            self.size(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(scaled_bg))
        self.setPalette(palette)

    def setup_buttons(self, layout: QVBoxLayout) -> None:
        """Set up the buttons for the main window.
        """
        # Create one button for each isolated program module
        self.sfm_btn = QPushButton("SfM Engine", self)
        self.sfm_btn.clicked.connect(self.sfm_btn_callback)
        self.sfm_btn.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.sfm_btn.enterEvent = lambda event: self.label_programs.setPixmap(
            QPixmap(self.saescan3d_label_path).scaled(
                self.label_size[0], self.label_size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.sfm_btn.setStyleSheet("""
            QPushButton {
                background-color: #a0a0a0;
                color: black;
                font-size: 18px;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #b0b0b0;
            }
            QPushButton:pressed {
                background-color: #8a8a8a;
            }
        """)
        self.smartmodel_btn = QPushButton("Mesh Manipulator", self)
        self.smartmodel_btn.clicked.connect(self.smartmodel_btn_callback)
        self.smartmodel_btn.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.smartmodel_btn.enterEvent = lambda event: self.label_programs.setPixmap(
            QPixmap(self.smartmodel_label_path).scaled(
                self.label_size[0], self.label_size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.smartmodel_btn.setStyleSheet("""
            QPushButton {
                background-color: #8fbf88;
                color: black;
                font-size: 18px;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #9fd998;
            }
            QPushButton:pressed {
                background-color: #7aad73;
            }
        """)
        # Add the buttons to the layout
        layout.addWidget(self.sfm_btn)
        layout.addWidget(self.smartmodel_btn)

    def setup_label_panel(self, layout: QVBoxLayout) -> None:
        """Set up the label panel for the main window.
        """
        # Label that will contain an image with each program illustrative image
        self.label_programs = QLabel(self)
        self.label_programs.setStyleSheet(
            "border: 1px solid white; background-color: rgba(0,0,0,50);")
        self.label_programs.setAlignment(Qt.AlignCenter)
        # Add the label to the layout
        layout.addWidget(self.label_programs)

    def sfm_btn_callback(self) -> None:
        """Open the Saescan3d window.
        """
        # Create and add to the list of child windows
        # The child windows are stored in a list to be closed when the main window is closed
        saescan3d_window = Saescan3dWindow()
        self.child_windows.append(saescan3d_window)
        saescan3d_window.setAttribute(Qt.WA_DeleteOnClose)
        saescan3d_window.destroyed.connect(
            lambda: self.child_windows.remove(saescan3d_window))
        saescan3d_window.show()

    def smartmodel_btn_callback(self) -> None:
        """Open the Smartmodel window.
        """
        # Create and add to the list of child windows
        # The child windows are stored in a list to be closed when the main window is closed
        smartmodel_window = SmartmodelWindow()
        self.child_windows.append(smartmodel_window)
        smartmodel_window.setAttribute(Qt.WA_DeleteOnClose)
        smartmodel_window.destroyed.connect(
            lambda: self.child_windows.remove(smartmodel_window))
        smartmodel_window.show()

    def closeEvent(self, event: None) -> None:
        """Close all child windows when the main window is closed.
        """
        for window in self.child_windows:
            if window is not None and window.isVisible():
                window.close()
        event.accept()


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
    timer.start(1000)

    # After some seconds, close splash and open main window
    window = MainWindow()
    QTimer.singleShot(3000, timer.stop)
    QTimer.singleShot(3000, splash.close)
    QTimer.singleShot(3000, window.show)
    exit(app.exec())


if __name__ == '__main__':
    main()
