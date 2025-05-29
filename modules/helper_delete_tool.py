from PySide6.QtWidgets import QMainWindow
import pyvista as pv
import numpy as np


def find_box_data(box_corners: np.ndarray) -> dict:
    """Find the box origin and axes from the corners of the box.

    Args:
        box_corners (np.ndarray): The corners of the box in 3D space, shape (8, 3).

    Returns:
        dict: A dict containing the origin of the box and the axes as numpy arrays.
    """
    # Step 1: Find the corner with the smallest (x + y + z) as origin
    origin = box_corners[0]
    # Normalize axes
    x_axis = box_corners[1] - origin
    y_axis = box_corners[3] - origin
    z_axis = box_corners[4] - origin
    Lx = np.linalg.norm(x_axis)
    Ly = np.linalg.norm(y_axis)
    Lz = np.linalg.norm(z_axis)
    x_axis = x_axis / Lx
    y_axis = y_axis / Ly
    z_axis = z_axis / Lz
    # Return the full data
    return {"o": origin, "x": x_axis, "y": y_axis, "z": z_axis,
            "Lx": Lx, "Ly": Ly, "Lz": Lz}


def point_outside_box(point: np.ndarray, box_data: dict, thresh_distance: float) -> bool:
    """Check if a point is outside the box defined by its corners.

    Args:
        point (np.ndarray): The query point in 3D space.
        box_data (dict): A dict containing the origin and axes of the box.
        thresh_distance (float): The threshold distance to consider a point outside the box.

    Returns:
        bool: True if the point is inside the box, False otherwise.
    """
    # If the point is too far from the box, it is considered outside
    if np.linalg.norm(point - box_data["o"]) > thresh_distance:
        return True
    # Transform point to box local coordinates
    v = point - box_data["o"]
    cx = np.dot(v, box_data["x"])
    cy = np.dot(v, box_data["y"])
    cz = np.dot(v, box_data["z"])
    # Check if outside bounds
    if (0 <= cx <= box_data["Lx"]) and \
       (0 <= cy <= box_data["Ly"]) and \
       (0 <= cz <= box_data["Lz"]):
        return False
    else:
        return True

def delete_inside_box(window: QMainWindow) -> None:
    """Deletes the mesh region inside the box.
    
    Args:
        window (QMainWindow): The main window of the application.
    """
    # Find box origin, axis and projected lenghts
    box_data = find_box_data(box_corners=window._box_widget_corners)
    max_box_distance = np.linalg.norm(window._box_widget_corners[0] - window._box_widget_corners[6])
    # For each point, check if it is outside the box and create mask
    outside_box_mask = [point_outside_box(point=point, box_data=box_data, thresh_distance=max_box_distance)
                        for point in window._current_mesh.points]
    # Obtain the points that are outside the box
    remaining = window._current_mesh.extract_points(outside_box_mask, adjacent_cells=True)
    window._current_mesh = remaining
    # Update visualization
    if window._current_mesh.n_points == 0:
        window.visualizer.remove_actor(window.mesh_actor, reset_camera=False)
        window.mesh_actor = None
        window.log_output("No points left after deletion.")
        return
    if window.project_mesh_level == "ptc" or window.project_mesh_level == "mesh":
        window.visualizer.remove_actor(window.mesh_actor, reset_camera=False)
        if window._current_mesh.n_points > 0:
            window.mesh_actor = window.visualizer.add_mesh(
                window._current_mesh, name="mesh_actor", 
                scalars=window._current_mesh.point_data["RGB"], rgb=True, reset_camera=False
            )
    else:
        window.visualizer.remove_actor(window.mesh_actor, reset_camera=False)
        if window._current_mesh.n_points > 0:
            window.mesh_actor = window.visualizer.add_mesh(
                window._current_mesh, texture=window.mesh_texture, name="mesh_actor", reset_camera=False
            )
    window.visualizer.render()
    window.log_output("Deleted region inside the box.")


def reset_mesh(window: QMainWindow) -> None:
    """Resets the mesh to its original state.
    
    Args:
        window (QMainWindow): The main window of the application.
    """
    if not hasattr(window, '_original_mesh'):
        window.log_output("Original mesh not stored.")
        return
    # Restore the original mesh
    window._current_mesh = window._original_mesh.copy()
    if window.project_mesh_level == "ptc" or window.project_mesh_level == "mesh":
        window.mesh_actor = window.visualizer.add_mesh(
            window._current_mesh, name="mesh_actor", 
            scalars=window._current_mesh.point_data["RGB"], rgb=True, reset_camera=False
        )
    else:
        window.mesh_actor = window.visualizer.add_mesh(
            window._current_mesh, texture=window.mesh_texture, name="mesh_actor", reset_camera=False
        )
    window.visualizer.render()
    window.log_output("Mesh has been reset to its original state.")


def enable_box_selection_for_deletion(window: QMainWindow) -> None:
    """Enable interactive box selection for mesh deletion.
    
    Args:
        window (QMainWindow): The main window of the application.
    """
    mesh_polydata = window.mesh_actor.GetMapper().GetInput().copy()
    window._original_mesh = mesh_polydata.copy()
    window._current_mesh = mesh_polydata.copy()
    # Callback for box widget
    def box_callback(box: pv.Box) -> None:
        """Callback function for the box widget to update bounds.

        Args:
            box (pv.Box): The box widget instance.
        """
        # Get the corners of the box, 0-3 from Z-min to and 4-7 from Z-max
        window._box_widget_corners = box.points.reshape(-1, 3)[:8]
    # Create box widget
    window._box_widget = window.visualizer.add_box_widget(
        callback=box_callback,
        bounds=window._current_mesh.bounds,
        use_planes=False,
        rotation_enabled=True,
        color='red'
    )
    # Key press handler
    def key_press_callback(interactor, event: object) -> None:
        """Callback function for key press events during box selection.

        Args:
            interactor: The interactor instance.
            event (object): The key press event.
        """
        key = interactor.GetKeySym()
        if key == 'Return':
            delete_inside_box(window)
        elif key.lower() == 'r':
            reset_mesh(window)
    # Attach key observer
    iren = window.visualizer.interactor.GetRenderWindow().GetInteractor()
    window._delete_iren = iren
    window._delete_key_observer_tag = iren.AddObserver("KeyPressEvent", key_press_callback)


def disable_box_selection_for_deletion(window: QMainWindow) -> None:
    """Disable the box selection tool and apply the deletion result.
    
    Args:
        window (QMainWindow): The main window of the application.
    """
    # Clear the entire scene
    window.visualizer.clear()
    # Clean internal variables
    if hasattr(window, '_box_widget'):
        del window._box_widget
    if hasattr(window, '_box_bounds'):
        del window._box_bounds
    if hasattr(window, '_delete_iren') and hasattr(window, '_delete_key_observer_tag'):
        window._delete_iren.RemoveObserver(window._delete_key_observer_tag)
        del window._delete_iren
        del window._delete_key_observer_tag
    # Re-add mesh
    if window.project_mesh_level == "ptc" or window.project_mesh_level == "mesh":
        window.mesh_actor = window.visualizer.add_mesh(
            window._current_mesh, name="mesh_actor", 
            scalars=window._current_mesh.point_data["RGB"], rgb=True, reset_camera=False
        )
    else:
        window.mesh_actor = window.visualizer.add_mesh(
            window._current_mesh, texture=window.mesh_texture, name="mesh_actor", reset_camera=False
        )
    if hasattr(window, '_original_mesh'):
        del window._original_mesh
    if hasattr(window, '_current_mesh'):
        del window._current_mesh
    window.visualizer.render()
