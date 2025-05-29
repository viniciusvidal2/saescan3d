from PySide6.QtWidgets import QMainWindow
import pyvista as pv


def delete_inside_box(window: QMainWindow) -> None:
    """Deletes the mesh region inside the box.
    
    Args:
        window (QMainWindow): The main window of the application.
    """
    # Clip using the box widget polydata
    window._current_mesh = window._current_mesh.clip_box(window._delete_box_polydata, invert=True)
    # Update visualization
    window.visualizer.remove_actor(window.mesh_actor, reset_camera=False)
    if window._current_mesh.n_points == 0:
        window.mesh_actor = None
        window.log_output("No points left after deletion.")
        return
    if window.project_mesh_level == "ptc" or window.project_mesh_level == "mesh":
        window.mesh_actor = window.visualizer.add_mesh(
            window._current_mesh, name="mesh_actor", 
            scalars=window._current_mesh.point_data["RGB"], rgb=True, reset_camera=False
        )
    else:
        window.mesh_actor = window.visualizer.add_mesh(
            window._current_mesh, texture=window.mesh_texture, name="mesh_actor", reset_camera=False
        )
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
        """Callback function for the box widget.

        Args:
            box (pv.Box): The box widget polydata instance.
        """
        window._delete_box_polydata = box.copy()
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
        window.visualizer.clear_box_widgets()
        del window._box_widget
    if hasattr(window, '_delete_iren') and hasattr(window, '_delete_key_observer_tag'):
        window._delete_iren.RemoveObserver(window._delete_key_observer_tag)
        del window._delete_iren
        del window._delete_key_observer_tag
    # Re-add mesh
    if window._current_mesh.n_points == 0:
        window.mesh_actor = None
    else:
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
