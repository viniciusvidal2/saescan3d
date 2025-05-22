from PySide6.QtWidgets import QMainWindow
from typing import Union


def get_box_bounds(bounds: Union[dict, list, tuple]) -> list:
    """Utility to parse bounds safely.
    
    Args:
        bounds (Union[dict, list, tuple]): The bounds to parse.

    Returns:
        list: The parsed bounds.
    """
    if isinstance(bounds, dict) and 'bounds' in bounds:
        return bounds['bounds']
    elif hasattr(bounds, 'bounds'):
        return bounds.bounds
    elif isinstance(bounds, (list, tuple)) and len(bounds) == 6:
        return bounds
    else:
        raise ValueError(f"Unexpected bounds format: {bounds}")


def safe_remove_actor(window: QMainWindow, actor_name: str) -> None:
    """Safely remove an actor from the visualizer.

    Args:
        window (QMainWindow): The main window of the application.
        actor_name (str): The name of the actor to remove.
    """
    for actor in list(window.visualizer.actors.values()):
        if actor.name == actor_name:
            window.visualizer.remove_actor(actor, reset_camera=False)
            break


def delete_inside_box(window: QMainWindow) -> None:
    """Deletes the mesh region inside the box.
    
    Args:
        window (QMainWindow): The main window of the application.
    """
    if not hasattr(window, '_box_bounds'):
        window.log_output("Box not defined.")
        return
    # Get the bounds of the box
    xmin, xmax, ymin, ymax, zmin, zmax = window._box_bounds
    # Mask the points inside the box
    pts = window._current_mesh.points
    mask = (
        (pts[:, 0] < xmin) | (pts[:, 0] > xmax) |
        (pts[:, 1] < ymin) | (pts[:, 1] > ymax) |
        (pts[:, 2] < zmin) | (pts[:, 2] > zmax)
    )
    remaining = window._current_mesh.extract_points(mask, adjacent_cells=True)
    if remaining.n_points == 0:
        window.log_output("All points were deleted. Nothing left.")
        return
    window._current_mesh = remaining
    # Update visualization
    safe_remove_actor(window=window, actor_name="mesh_actor")
    window.mesh_actor = window.visualizer.add_mesh(
        window._current_mesh, texture=window.mesh_texture, name="mesh_actor"
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
    safe_remove_actor(window=window, actor_name="mesh_actor")
    window.mesh_actor = window.visualizer.add_mesh(
        window._current_mesh, texture=window.mesh_texture, name="mesh_actor"
    )
    window.visualizer.render()
    window.log_output("Mesh has been reset to its original state.")


def enable_box_selection_for_deletion(window: QMainWindow) -> None:
    """Enable interactive box selection for mesh deletion.
    
    Args:
        window (QMainWindow): The main window of the application.
    """
    window._original_mesh = window.mesh_actor.copy()
    window._current_mesh = window.mesh_actor.copy()
    window._box_bounds = list(window._current_mesh.bounds)
    # Callback for box widget
    def box_callback(bounds):
        window._box_bounds = get_box_bounds(bounds)
    # Create box widget
    window._box_widget = window.visualizer.add_box_widget(
        callback=box_callback,
        bounds=window._current_mesh.bounds,
        use_planes=False,
        rotation_enabled=True,
        color='red'
    )
    # Key press handler
    def key_press_callback(interactor, event):
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
    window.mesh_actor = window.visualizer.add_mesh(
        window._current_mesh, texture=window.mesh_texture, name="mesh_actor", reset_camera=False
    )
    if hasattr(window, '_original_mesh'):
        del window._original_mesh
    if hasattr(window, '_current_mesh'):
        del window._current_mesh
    window.visualizer.render()
