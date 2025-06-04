from PySide6.QtWidgets import QMainWindow
import pyvista as pv


def smooth_mesh_region(window: QMainWindow) -> None:
    """Smooths the mesh region inside the box.
    
    Args:
        window (QMainWindow): The main window of the application.
    """
    # Clip using the box widget polydata
    mesh_to_smooth = window._current_mesh.clip_box(window._delete_box_polydata, invert=False).extract_surface()
    mesh_to_keep = window._current_mesh.clip_box(window._delete_box_polydata, invert=True).extract_surface()
    # Apply taubin smoothing to the clipped mesh
    smoothed_mesh = mesh_to_smooth.smooth_taubin(
        n_iter=window._smooth_params['n_iter'],  
        pass_band=window._smooth_params['pass_band'], 
        normalize_coordinates=True
    )
    # Combine the smoothed mesh with the rest of the mesh
    window._current_mesh = pv.PolyData()
    window._current_mesh += smoothed_mesh
    window._current_mesh += mesh_to_keep
    # Update visualization
    window.visualizer.remove_actor(window.mesh_actor, reset_camera=False)
    if window.project_mesh_level == "ptc" or window.project_mesh_level == "mesh":
        window.mesh_actor = window.visualizer.add_mesh(
            window._current_mesh, name="mesh_actor", 
            scalars=window._current_mesh.point_data["RGB"], rgb=True, reset_camera=False
        )
    else:
        window.mesh_actor = window.visualizer.add_mesh(
            window._current_mesh, texture=window.mesh_texture, name="mesh_actor", reset_camera=False
        )
    window.log_output("Smoothed region inside the box.")


def reset_mesh(window: QMainWindow) -> None:
    """Resets the mesh to its original state.
    
    Args:
        window (QMainWindow): The main window of the application.
    """
    # Restore the original mesh
    window._current_mesh = window._original_mesh.copy()
    window.visualizer.remove_actor(window.mesh_actor, reset_camera=False)
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


def enable_smooth_tool(window: QMainWindow) -> None:
    """Enable interactive box selection for mesh smooth.
    
    Args:
        window (QMainWindow): The main window of the application.
    """
    window._original_mesh = window.mesh_actor.GetMapper().GetInput().copy()
    window._current_mesh = window._original_mesh.copy()
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
            smooth_mesh_region(window)
        elif key.lower() == 'r':
            reset_mesh(window)
    # Attach key observer and instructions
    iren = window.visualizer.interactor.GetRenderWindow().GetInteractor()
    window._smooth_iren = iren
    window._smooth_key_observer_tag = iren.AddObserver("KeyPressEvent", key_press_callback)
    window.instructions_text_actor = window.visualizer.add_text(
        "Press 'Return' to smooth the mesh inside the box.\n"
        "Press 'R' to reset the mesh to its original state.\n"
        "Use the sliders to adjust smoothing parameters.",
        position='lower_left',
        color='white',
        name="instructions",
        font_size=14
    )
    # Create slider for smoothing parameters
    window._smooth_params = {
        'n_iter': 20,  # Number of iterations for smoothing
        'pass_band': 0.1,  # Pass band for smoothing
    }
    window.visualizer.add_slider_widget(
        callback=lambda value: window._smooth_params.__setitem__('pass_band', float(value)),
        value=0.1,
        rng=[0.02, 0.9],
        title="Pass Band Parameter",
        pointa=(0.05, 0.92),
        pointb=(0.25, 0.92),
        style='modern'
    )
    window.visualizer.add_slider_widget(
        callback=lambda value: window._smooth_params.__setitem__('n_iter', int(value)),
        value=20,
        rng=[1, 100],
        title="Number of Iterations",
        pointa=(0.30, 0.92),
        pointb=(0.60, 0.92),
        style='modern'
    )


def disable_smooth_tool(window: QMainWindow) -> None:
    """Disable the box selection tool and apply the smooth result.
    
    Args:
        window (QMainWindow): The main window of the application.
    """
    # Clear the texts
    if hasattr(window, 'instructions_text_actor'):
        window.visualizer.remove_actor(window.instructions_text_actor, reset_camera=False)
        del window.instructions_text_actor
    # Clean internal variables
    if hasattr(window, '_box_widget'):
        window.visualizer.clear_box_widgets()
        del window._box_widget
    window.visualizer.clear_slider_widgets()
    if hasattr(window, '_smooth_iren') and hasattr(window, '_smooth_key_observer_tag'):
        window._smooth_iren.RemoveObserver(window._smooth_key_observer_tag)
        del window._smooth_iren
        del window._smooth_key_observer_tag
    if hasattr(window, '_smooth_params'):
        del window._smooth_params
    if hasattr(window, '_original_mesh'):
        del window._original_mesh
    if hasattr(window, '_current_mesh'):
        del window._current_mesh
    window.visualizer.render()
