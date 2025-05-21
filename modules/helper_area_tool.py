import pyvista as pv
import numpy as np
from PySide6.QtWidgets import QMainWindow


def add_area_marker(window: QMainWindow, point: np.ndarray) -> None:
    """Adds the area marker as a sphere when clicked

    Args:
        window (QMainWindow): The window with the visualizer to draw to
        point (np.ndarray): The point we picked
    """
    # Add a sphere marker at the selected point
    sphere = pv.Sphere(radius=0.5, center=point, theta_resolution=64, phi_resolution=64)
    actor = window.visualizer.add_mesh(sphere, color='green', reset_camera=False)
    window.polygon_points.append((point, actor))


def draw_polygon_and_compute_area(window: QMainWindow) -> None:
    """Draws polygon from selected points and computes surface area.
    
    Args:
        window (QMainWindow): The window with the visualizer to draw to
    """
    if len(window.polygon_points) < 3:
        window.log_output("Select at least 3 points to form a polygon.")
        return
    # Ensure polygon is closed
    poly_points = np.array([pt for pt, _ in window.polygon_points])
    if not np.allclose(poly_points[0], poly_points[-1]):
        poly_points = np.vstack([poly_points, poly_points[0]])
    # Create PolyData of polygon
    polygon = pv.PolyData(poly_points)
    polygon["scalars"] = np.arange(len(poly_points))  # Dummy scalar for visualization
    # Make a surface and mask original mesh using polygon
    surf = polygon.delaunay_2d()
    surf.clean(inplace=True)
    extracted = window.mesh_actor.extract_surface().select_enclosed_points(surf, check_surface=False)
    inside = extracted.threshold(0.5, scalars="SelectedPoints")
    # Try to calculate area
    if inside.n_cells > 0:
        area = inside.area
        window.log_output(f"Polygon area: {area:.3f} meters²")
        # Add extracted surface
        window._area_surface_actor = window.visualizer.add_mesh(inside, color='orange', opacity=0.9, reset_camera=False)
        window.visualizer.render()
    else:
        window.log_output("No intersecting surface found with the polygon.")


def clear_polygon_selection(window: QMainWindow) -> None:
    """Clears all polygon points and any displayed area.
    
    Args:
        window (QMainWindow): The window with the visualizer to draw to
    """
    # Remove all polygon points
    for _, actor in getattr(window, 'polygon_points', []):
        window.visualizer.remove_actor(actor)
    window.polygon_points.clear()
    # Remove the area surface actor if it exists
    if hasattr(window, '_area_surface_actor'):
        window.visualizer.remove_actor(window._area_surface_actor)
        del window._area_surface_actor
    window.visualizer.render()


def enable_polygon_selection_for_area_measurement(window: QMainWindow) -> None:
    """Enables interactive polygon selection and area measurement.

    Args:
        window (QMainWindow): The window with the visualizer to draw to
    """
    window.polygon_points = []
    # Define the callback for right-clicking on the mesh
    def right_click_callback(point: np.ndarray, picker: object) -> None:
        if point is None or not isinstance(point, np.ndarray):
            return
        point_id = window.mesh_actor.find_closest_point(point)
        selected_point = window.mesh_actor.points[point_id]
        add_area_marker(window, selected_point)
    # Define the callback for key presses
    def key_press_callback(interactor: object, event: object) -> None:
        key = interactor.GetKeySym()
        if key == 'Return':  # Enter key
            draw_polygon_and_compute_area(window)
        elif key == 'Escape':
            clear_polygon_selection(window)
    # Enable point picking and set up callbacks
    window.visualizer.enable_point_picking(
        callback=right_click_callback,
        use_picker=True,
        show_message=False,
        left_clicking=False,
        show_point=False
    )
    # Set up key press observer
    iren = window.visualizer.interactor.GetRenderWindow().GetInteractor()
    window._area_iren = iren
    window._area_key_observer_tag = iren.AddObserver("KeyPressEvent", key_press_callback)


def disable_polygon_selection_for_area_measurement(window: QMainWindow) -> None:
    """Disables polygon selection and removes any observers and visuals.
    
    Args:
        window (QMainWindow): The window with the visualizer to draw to
    """
    # Disable point picking and remove observers
    window.visualizer.disable_picking()
    if hasattr(window, '_area_iren') and hasattr(window, '_area_key_observer_tag'):
        window._area_iren.RemoveObserver(window._area_key_observer_tag)
        del window._area_iren
        del window._area_key_observer_tag
    # Clear polygon points and area surface
    clear_polygon_selection(window)
