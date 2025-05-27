import pyvista as pv
import numpy as np
from PySide6.QtWidgets import QMainWindow


def add_sphere(window: QMainWindow, point: np.ndarray) -> None:
    """Add a sphere marker at the selected point.

    Args:
        window (QMainWindow): The main window instance.
        point (np.ndarray): The point where the sphere will be placed.
    """
    sphere = pv.Sphere(radius=0.5, center=point, theta_resolution=64, phi_resolution=64)
    actor = window.visualizer.add_mesh(sphere, color='green', reset_camera=False)
    window.selected_points.append((point, actor))


def connect_and_print_distance(window: QMainWindow) -> None:
    """Connect the two selected points with a line and print the distance.

    Args:
        window (QMainWindow): The main window instance.
    """
    # Create a line between the two selected points
    p1, _ = window.selected_points[0]
    p2, _ = window.selected_points[1]
    line = pv.Line(p1, p2)
    window.line_actor = window.visualizer.add_mesh(line, color='red', line_width=4, reset_camera=False)
    # Calculate the distance between the two points
    distance = np.linalg.norm(np.array(p1) - np.array(p2))
    window.visualizer.add_text(
        f"Distance: {distance:.2f} meters",
        position='upper_left',
        color='black',
        name="distance_text"
    )
    window.log_output(f"DISTANCE: {distance:.3f} meters")


def clear_all_points(window: QMainWindow) -> None:
    """Clear all selected points and the line actor.

    Args:
        window (QMainWindow): The main window instance.
    """
    # Removing the spheres and line actor
    for _, actor in window.selected_points:
        window.visualizer.remove_actor(actor)
    window.selected_points.clear()
    if window.line_actor:
        window.visualizer.remove_actor(window.line_actor)
        window.line_actor = None
    window.visualizer.render()
    

def enable_point_selection_for_distance_measurement(window: QMainWindow) -> None:
    """Enable point selection for distance measurement.
    """
    # Get a backup of the original mesh actor polydata
    window._mesh_actor_polydata_backup = window.mesh_actor.GetMapper().GetInput().copy()
    window.selected_points = []  # store (point, actor) tuples
    window.line_actor = None
    # Define the callback for right-clicking on the mesh
    def right_click_callback(point: np.ndarray, picker: object) -> None:
        """Callback for right-clicking on the mesh to select points.

        Args:
            point (np.ndarray): The point where the right-click occurred.
            picker (object): The picker object.
        """
        # Get the closest point index from the mesh
        if point is None or not isinstance(point, np.ndarray):
            return
        mesh_polydata = window.mesh_actor.GetMapper().GetInputAsDataSet()
        point_id = mesh_polydata.find_closest_point(point)
        # Create a sphere at the selected point
        selected_point = mesh_polydata.points[point_id]
        add_sphere(window, selected_point)
        if len(window.selected_points) == 2:
            connect_and_print_distance(window)
        # If more than 2 points are selected, clear the selection and add the new point
        elif len(window.selected_points) > 2:
            clear_all_points(window)
            add_sphere(window, selected_point)
    # Define the callback for key press events
    def key_press_callback(interactor: object, event: object) -> None:
        """Callback for key press events.

        Args:
            interactor (object): The interactor object.
            event (object): The event object.
        """
        # Check if the Escape key is pressed to clear the selection
        key = interactor.GetKeySym()
        if key == 'Escape':
            clear_all_points(window)
    # Enable point picking and set the callback for right-clicking
    window.visualizer.enable_point_picking(callback=right_click_callback, use_picker=True,
                                        show_message=False, left_clicking=False, show_point=False)
    # Connect the key press callback to the visualizer
    # Store iren and key observer tag to remove the observer later
    iren = window.visualizer.interactor.GetRenderWindow().GetInteractor()
    window._iren = iren
    window._key_observer_tag = iren.AddObserver("KeyPressEvent", key_press_callback)


def disable_point_selection_for_distance_measurement(window: QMainWindow) -> None:
    """Disable point selection for distance measurement.

    Args:
        window (QMainWindow): The main window instance.
    """
    # Clear the entire scene
    window.visualizer.clear()
    # Disable point picking and remove observers
    window.visualizer.disable_picking()
    if hasattr(window, '_iren') and hasattr(window, '_key_observer_tag'):
        window._iren.RemoveObserver(window._key_observer_tag)
        del window._iren
        del window._key_observer_tag
    if hasattr(window, 'selected_points') or hasattr(window, 'line_actor'):
        clear_all_points(window)
    # Re-add the original mesh to the visualizer
    if hasattr(window, '_mesh_actor_polydata_backup'):
        window.mesh_actor = window.visualizer.add_mesh(
            window._mesh_actor_polydata_backup, texture=window.mesh_texture, name="mesh_actor", reset_camera=False
        )
        del window._mesh_actor_polydata_backup
