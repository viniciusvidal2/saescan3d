from PySide6.QtWidgets import QMainWindow


def enable_elevation_tool(window: QMainWindow) -> None:
    """Enables the elevation slicing tool with a draggable plane and a Z-based colormap.

    Args:
        window (QMainWindow): The main window of the application.
    """
    # Get the bounds of the mesh actor
    bounds = window.mesh_actor.bounds
    z_min, z_max = bounds[4], bounds[5]
    z_center = (z_min + z_max) / 2
    window._elevation_bounds = (z_min, z_max)
    # Backup the scalar data
    if not hasattr(window, "_elevation_colormap_backup"):
        window._elevation_colormap_backup = window.mesh_actor.active_scalars_name
    # Apply initial colormap and show scalar bar
    apply_elevation_colormap(window=window, reference_z=z_center)
    # Add draggable plane widget
    def widget_callback(*args):
        if hasattr(window, "_elevation_plane_widget"):
            z = window._elevation_plane_widget.GetOrigin()[2]
            print(f"Current Z plane: {z}")
            apply_elevation_colormap(window=window, reference_z=z)
    window._elevation_plane_widget = window.visualizer.add_plane_widget(
        callback=widget_callback,
        normal=(0, 0, 1),
        origin=((bounds[0] + bounds[1]) / 2, (bounds[2] + bounds[3]) / 2, z_center),
        bounds=(bounds[0], bounds[1], bounds[2], bounds[3], z_min, z_max),
        factor=1.2,
        assign_to_axis="z",
        outline_translation=False,
    )


def disable_elevation_tool(window: QMainWindow) -> None:
    """Disables the elevation slicing tool and cleans up.
    
    Args:
        window (QMainWindow): The main window of the application.
    """
    # Remove the elevation plane widget
    if hasattr(window, "_elevation_plane_widget"):
        window._elevation_plane_widget.EnabledOff()
        del window._elevation_plane_widget
    # Restore the original scalar data
    if hasattr(window, "_elevation_colormap_backup"):
        # window.mesh_actor.clear_data()
        window.mesh_actor = window.visualizer.add_mesh(window.mesh_actor, name="mesh_actor", texture=window.mesh_texture, reset_camera=False)
        del window._elevation_colormap_backup
    # Remove the scalar bar
    try:
        window.visualizer.remove_scalar_bar()
    except Exception:
        pass
    window.visualizer.render()


def apply_elevation_colormap(window: QMainWindow, reference_z: float) -> None:
    """Applies viridis colormap based on Z elevation and shows scalar bar.
    
    Args:
        window (QMainWindow): The main window of the application.
        reference_z (float): The Z elevation value to slice at.
    """
    # Get the scalar data bounds
    z_bound_min, z_bound_max = window._elevation_bounds
    if reference_z < z_bound_min:
        reference_z = z_bound_min + 0.1
    if reference_z > z_bound_max:
        reference_z = z_bound_max - 0.1
    # Get the Z elevation data
    window.mesh_actor.point_data['Z Elevation'] = window.mesh_actor.points[:, 2].copy()
    # Remove any previous scalar bar
    try:
        window.visualizer.remove_scalar_bar()
    except Exception:
        pass
    # Set the active scalars to Z Elevation
    window.visualizer.add_mesh(
        window.mesh_actor,
        scalars='Z Elevation',
        cmap='viridis',
        clim=(reference_z, z_bound_max),
        reset_camera=False,
        show_scalar_bar=True,
        scalar_bar_args={
            "title": "Z Elevation",
            "n_labels": 5,
            "fmt": "%.2f",
            "vertical": True,
            "title_font_size": 16,
            "label_font_size": 12,
            "position_x": 0.85,
            "position_y": 0.05,
        },
    )
    window.visualizer.render()
