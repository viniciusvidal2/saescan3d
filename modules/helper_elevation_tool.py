import pyvista as pv
import numpy as np
from PySide6.QtWidgets import QMainWindow


def enable_elevation_tool(window: QMainWindow) -> None:
    """Enables the elevation slicing tool with a draggable plane and a Z-based colormap."""
    bounds = window.mesh_actor.bounds
    z_min, z_max = bounds[4], bounds[5]
    z_center = (z_min + z_max) / 2

    window._elevation_bounds = (z_min, z_max)

    # Backup
    if not hasattr(window, "_elevation_colormap_backup"):
        window._elevation_colormap_backup = window.mesh_actor.active_scalars_name

    # Apply initial colormap and show scalar bar
    _apply_elevation_colormap(window, z_center)

    # Add draggable plane widget
    def widget_callback(plane, event=None):
        if isinstance(plane, tuple):
            z = plane[2]
        else:
            z = plane.center[2]
        _apply_elevation_colormap(window, z)

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
    """Disables the elevation slicing tool and cleans up."""
    if hasattr(window, "_elevation_plane_widget"):
        window._elevation_plane_widget.EnabledOff()
        del window._elevation_plane_widget

    if hasattr(window, "_elevation_colormap_backup"):
        window.mesh_actor.clear_data()
        window.visualizer.add_mesh(window.mesh_actor, color="white", reset_camera=False)
        del window._elevation_colormap_backup

    try:
        window.visualizer.remove_scalar_bar()
    except Exception:
        pass

    window.visualizer.render()


def _apply_elevation_colormap(window: QMainWindow, reference_z: float) -> None:
    """Applies viridis colormap based on Z elevation and shows scalar bar."""
    z_min, z_max = window._elevation_bounds
    z_values = window.mesh_actor.points[:, 2]

    # Store Z as scalar data
    window.mesh_actor.point_data['Z Elevation'] = z_values

    window.visualizer.add_mesh(
        window.mesh_actor,
        scalars='Z Elevation',
        cmap='viridis',
        clim=[z_min, z_max],
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
