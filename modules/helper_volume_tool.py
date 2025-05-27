from PySide6.QtWidgets import QMainWindow
import numpy as np
import pyvista as pv


def perform_volume_clipping(window: QMainWindow) -> None:
    """Clip the mesh using the box's planes and extrude to calculate volume.

    Args:
        window (QMainWindow): The main window instance.
    """
    # Clip the mesh in every direction but the Z-max one
    clipped_mesh = pv.wrap(window.mesh_actor.GetMapper().GetInput()).copy()
    for name, plane in window._volume_box_planes.items():
        if name == "Z-max":
            continue
        clipped_mesh = clipped_mesh.clip(normal=-plane["normal"], origin=plane["origin"])
    if clipped_mesh.n_points == 0:
        window.log_output("No points in the clipped mesh. Exiting volume calculation.")
        return
    # Extrude the clipped mesh using the Z-min plane
    extrude_plane, extrude_direction = get_plane_params(plane=window._volume_box_planes["Z-min"])
    extruded_mesh = clipped_mesh.extrude_trim(direction=extrude_direction, trim_surface=extrude_plane, extrusion="boundary_edges")
    # Get the extruded mesh volume and add to the visualizer
    window.log_output(f"VOLUME of the extruded mesh: {extruded_mesh.volume:.2f} cubic meters.")
    window.visualizer.add_text(
        f"Volume: {extruded_mesh.volume:.2f} cubic meters",
        position='upper_left',
        color='black',
        name="volume_text"
    )
    # Add the clipped and extruded meshes to the visualizer
    window.clipped_mesh_actor = window.visualizer.add_mesh(
        clipped_mesh, color='blue', opacity=0.8, name="clipped_mesh_actor", reset_camera=False
    )
    window.extruded_mesh_actor = window.visualizer.add_mesh(
        extruded_mesh, color='orange', opacity=0.6, name="extruded_mesh_actor", reset_camera=False
    )
    

def get_planes_from_box_widget(box_points: np.ndarray) -> dict:
    """Get the planes from the box widget points.

    Args:
        box_points (np.ndarray): The points of the box widget.
    
    Returns:
        dict: A dictionary containing the planes' origins, normals, and corner points.
    """
    # Box center
    center = box_points[-1]
    # Mapping of faces to their midpoints and corner points
    faces = {
        "X-min": {"origin_idx": 8, "corner_indices": [0, 3, 4, 7]},
        "X-max": {"origin_idx": 9, "corner_indices": [1, 2, 5, 6]},
        "Y-min": {"origin_idx": 10, "corner_indices": [0, 1, 4, 5]},
        "Y-max": {"origin_idx": 11, "corner_indices": [2, 3, 6, 7]},
        "Z-min": {"origin_idx": 12, "corner_indices": [0, 1, 2, 3]},
        "Z-max": {"origin_idx": 13, "corner_indices": [4, 5, 6, 7]},
    }
    planes_info_dict = {}
    for name, face in faces.items():
        origin = box_points[face["origin_idx"]]
        face_corners = box_points[face["corner_indices"]]
        # Compute two edge vectors
        v1 = face_corners[1] - face_corners[0]
        v2 = face_corners[3] - face_corners[0]
        normal = np.cross(v1, v2)
        normal /= np.linalg.norm(normal)
        # Ensure normal points inwards
        to_center = center - origin
        if np.dot(normal, to_center) < 0:
            normal = -normal
        # Store the plane information
        planes_info_dict[name] = {
            "origin": origin,
            "normal": normal,
            "corners": face_corners,
        }
    return planes_info_dict


def get_plane_params(plane: dict) -> tuple:
    """Get the extrude plane and direction based on the provided plane.
    
    Args:
        plane (dict): A dictionary containing the origin and normal of the plane.
    
    Returns:
        tuple: A tuple containing the extrude plane (as a PolyData) and the extrude direction (as a numpy array).
    """
    # Create a plane mesh
    i_size = np.linalg.norm(plane["corners"][0] - plane["corners"][1])
    j_size = np.linalg.norm(plane["corners"][0] - plane["corners"][3])
    extrude_plane = pv.Plane(center=np.array(plane["origin"]), 
                             direction=np.array(plane["normal"]), 
                             i_size=i_size, j_size=j_size)
    # Define the extrude direction as the negative of the normal
    extrude_direction = -np.array(plane["normal"])
    return extrude_plane, extrude_direction


def enable_volume_calculation(window: QMainWindow) -> None:
    """Enable volume calculation in the provided window.

    Args:
        window (QMainWindow): The main window instance.
    """
    # Get a backup of the original mesh actor polydata
    window._mesh_actor_polydata_backup = window.mesh_actor.GetMapper().GetInput().copy()
    # Creates the box widget callback that will be used to generate the mesh clip and volume region
    def callback(box: pv.Box):
        """Callback function for the box widget.
        
        Args:
            box (pv.Box): The box widget instance.
        """
        # Calculate the planes of the box from the widget points
        box_widget_points = box.points.reshape(-1, 3)
        window._volume_box_planes = get_planes_from_box_widget(box_points=box_widget_points)
        # Remove any previous clipped or volume actors, plus the tools actors too
        for actor_name in list(window.visualizer.actors.keys()):
            if actor_name.startswith("Z-min-corner-") or actor_name == "extrude_direction_arrow_helper":
                window.visualizer.remove_actor(actor_name, reset_camera=False)
            elif actor_name in ["clipped_mesh_actor", "extruded_mesh_actor"]:
                window.visualizer.remove_actor(actor_name, reset_camera=False)
        # Add 4 spheres as the corners of the Z-min plane
        for i, corner in enumerate(window._volume_box_planes["Z-min"]["corners"]):
            sphere = pv.Sphere(radius=1, center=corner)
            window.visualizer.add_mesh(sphere, color='blue', opacity=0.6, name=f"Z-min-corner-{i}", reset_camera=False)
        # Add arrow to indicate extrusion direction
        extrude_plane, extrude_direction = get_plane_params(plane=window._volume_box_planes["Z-min"])
        arrow_length = np.linalg.norm(box_widget_points[13][2] - box_widget_points[12][2]) / 3
        arrow = pv.Arrow(start=extrude_plane.center, direction=-extrude_direction, scale=arrow_length)
        window.visualizer.add_mesh(arrow, color='blue', name="extrude_direction_arrow_helper", reset_camera=False)
    # Create the box widget with the specified bounds and callback
    window._volume_box_widget = window.visualizer.add_box_widget(
        callback=callback,
        bounds=pv.wrap(window.mesh_actor.GetMapper().GetInput()).bounds,
        rotation_enabled=True,
        color='red'
    )
    # Key press handler callback for volume calculation
    def key_press_callback(interactor, event: object) -> None:
        """Callback function for key press events during volume calculation.

        Args:
            interactor: The interactor instance.
            event (object): The key press event.
        """
        key = interactor.GetKeySym()
        if key == 'Return':
            perform_volume_clipping(window)
    # Create the key observer
    iren = window.visualizer.interactor.GetRenderWindow().GetInteractor()
    window._delete_iren = iren
    window._delete_key_observer_tag = iren.AddObserver("KeyPressEvent", key_press_callback)


def disable_volume_calculation(window: QMainWindow) -> None:
    """Disable volume calculation in the provided window.

    Args:
        window (QMainWindow): The main window instance.
    """
    # Clear the entire scene
    window.visualizer.clear()
    # Remove the actors added by the volume calculation
    for actor_name in list(window.visualizer.actors.keys()):
        # Tool
        if actor_name.startswith("Z-min-corner-") or actor_name == "extrude_direction_arrow_helper":
            window.visualizer.remove_actor(actor_name, reset_camera=False)
        # Clipped and extruded mesh
        elif actor_name in ["clipped_mesh_actor", "extruded_mesh_actor"]:
            window.visualizer.remove_actor(actor_name, reset_camera=False)
    # Remove the box widget and actors related to volume calculation
    if hasattr(window, '_volume_box_widget'):
        window._volume_box_widget.EnabledOff()
        del window._volume_box_widget
    if hasattr(window, '_volume_box_planes'):
        del window._volume_box_planes
    if hasattr(window, 'clipped_mesh_actor'):
        del window.clipped_mesh_actor
    if hasattr(window, 'extruded_mesh_actor'):
        del window.extruded_mesh_actor
    # Remove the key observer for volume calculation
    if hasattr(window, '_delete_iren') and hasattr(window, '_delete_key_observer_tag'):
        window._delete_iren.RemoveObserver(window._delete_key_observer_tag)
        del window._delete_iren
        del window._delete_key_observer_tag
    # Re-add the original mesh to the visualizer
    if hasattr(window, '_mesh_actor_polydata_backup'):
        window.mesh_actor = window.visualizer.add_mesh(
            window._mesh_actor_polydata_backup, texture=window.mesh_texture, name="mesh_actor", reset_camera=False
        )
        del window._mesh_actor_polydata_backup
    window.visualizer.render()
