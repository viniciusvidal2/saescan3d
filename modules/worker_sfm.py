from PySide6.QtCore import QObject, Signal, Slot
import pyvista as pv
import numpy as np
import subprocess
import os
import shutil
import open3d as o3d
import json
import re
from modules.tools import (
    get_file_placement_path, convert_obj_to_ply, read_pyvista_cloud
)
from modules.scale_ptcs import (
    get_camera_poses_utm_frame, compute_transformation_from_sfm,
    transform_save_obj, transform_save_ptc
)

class WorkerSfm(QObject):
    # Signals
    finished = Signal()
    log = Signal(str)
    run_pipeline_signal = Signal()
    # region Constructor, gets, sets
    def __init__(self):
        """Initialize the WorkerSfm class.
        """
        super().__init__()
        # Folders
        self.output_folder = None
        self.input_folder = None
        self.project_file_path = None
        self.meshroom_batch_path = get_file_placement_path("dependencies/meshroom/meshroom_batch")
        # Pipelines
        self.pipelines = {"mesh": None,
                          "full": "photogrammetry"}
        self.pipeline = "full"
        # Signals
        self.run_pipeline_signal.connect(self.run_pipeline)
        # Cameras
        self.cameras = dict()
        # Point cloud
        self.point_cloud_polydata = None
        self.scene_center = None

    def set_input_folder(self, input_folder) -> None:
        """Set the input folder for the SFM worker.

        Args:
            input_folder (str): The input folder path.
        """
        self.input_folder = input_folder

    def set_output_folder(self, output_folder) -> None:
        """Set the output folder for the SFM worker.

        Args:
            output_folder (str): The output folder path.
        """
        self.output_folder = output_folder
        self.cache_folder = os.path.join(self.output_folder, "MeshroomCache")

    def set_pipeline(self, pipeline: str) -> None:
        """Set the pipeline to run.

        Args:
            pipeline (str): The pipeline to run.
        """
        if pipeline in self.pipelines:
            self.pipeline = pipeline
        else:
            self.log.emit(f"Pipeline '{pipeline}' is not supported. Going with 'full' instead.")
            self.pipeline = "full"

    def get_textured_mesh_paths(self) -> tuple:
        """Get the textured mesh related paths.

        Returns:
            tuple: The paths to the obj and mtl files.
        """
        # Checking files and paths
        if not self.output_folder:
            self.log.emit("Output folder is not set.")
            return "", ""
        obj_path = os.path.join(self.output_folder, "Texturing", "texturedMesh.obj")
        mtl_path = os.path.join(self.output_folder, "Texturing", "texturedMesh.mtl")
        if not os.path.exists(obj_path) or not os.path.exists(mtl_path):
            self.log.emit("Textured mesh not found in the output folder.")
            return "", ""
        return obj_path, mtl_path
    
    def get_cameras(self) -> dict:
        """Get the cameras.

        Returns:
            dict: The cameras with arrows as axis in the world frame.
        """
        if not self.output_folder:
            self.log.emit("Output folder is not set to obtain cameras.")
            return {}
        if not self.cameras:
            scale, global_R_scaled, global_t_scaled = compute_transformation_from_sfm(
                sfm_path=os.path.join(self.output_folder, "cameras.sfm"))
            camera_poses = get_camera_poses_utm_frame(sfm_path=os.path.join(self.output_folder, "cameras.sfm"),
                                                      scale=scale,
                                                      rotation=global_R_scaled,
                                                      t=global_t_scaled)
            if self.create_pyvista_cameras(camera_poses=camera_poses):
                self.log.emit("Cameras created successfully.")
            else:
                self.log.emit("Failed to create cameras, no point cloud or mesh set.")
                return {}
        return self.cameras
    
    def get_scene_center(self) -> np.ndarray:
        """Get the scene center from the point cloud.

        Returns:
            np.ndarray: The scene center.
        """
        if self.scene_center:
            return self.scene_center
        if not self.output_folder:
            self.log.emit("Output folder is not set to obtain scene center.")
            return None
        if self.point_cloud_polydata:
            self.scene_center = self.point_cloud_polydata.center
        else:
            ptc_path = os.path.join(self.output_folder, "pointCloud.ply")
            if not os.path.exists(ptc_path):
                self.log.emit("Point cloud not found in the output folder.")
                return None
            self.point_cloud_polydata = read_pyvista_cloud(ptc_path=ptc_path)
            self.scene_center = self.point_cloud_polydata.center
        return self.scene_center
    
    def get_pyvista_cloud(self) -> pv.PolyData:
        """Get the point cloud.

        Returns:
            pv.PolyData: The point cloud.
        """
        if not self.point_cloud_polydata:
            ptc_path = os.path.join(self.output_folder, "pointCloud.ply")
            if not os.path.exists(ptc_path):
                self.log.emit("Point cloud not found in the output folder.")
                return None
            self.point_cloud_polydata = read_pyvista_cloud(ptc_path=ptc_path)
        return self.point_cloud_polydata
    
    # endregion
    # region Methods

    def create_project_file(self, pipeline: str) -> bool:
        """Create a project file for the SFM worker.
        Args:
            pipeline (str): The pipeline to run.

        Returns:
            bool: True if the project file was created successfully, False otherwise.
        """
        # Security checks
        if not self.input_folder or not self.output_folder:
            self.log.emit("Input or output folder is not set.")
            return False
        if pipeline not in self.pipelines:
            self.log.emit(f"Pipeline '{pipeline}' is not supported.")
            return False
        # Project file with the output folder name in the output folder
        self.project_file_path = f"{self.output_folder}/{self.output_folder.split('/')[-1]}.mg"
        # Create the project file from the input images
        command = [self.meshroom_batch_path, 
                   "--input", self.input_folder, 
                   "--save", self.project_file_path,
                   "--pipeline", self.pipelines[pipeline],
                   "--cache", self.cache_folder,
                   "--toNode", "CameraInit"]
        try:
            subprocess.run(command, check=True, 
                           creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        except subprocess.CalledProcessError as e:
            self.log.emit(f"Error creating project file: {e}")
            return False
        # Read the project content as JSON and change the output texture format to PNG
        with open(self.project_file_path, "r") as project_file:
            project_content = json.load(project_file)
            project_content["graph"]["Texturing_1"]["inputs"]["colorMapping"]["colorMappingFileType"] = "png"
            project_content["graph"]["Texturing_1"]["outputs"]["outputTextures"] = \
                project_content["graph"]["Texturing_1"]["outputs"]["outputTextures"].replace(".exr", ".png")
            project_file.close()
        # Write the modified project content back to the project file
        with open(self.project_file_path, "w") as project_file:
            json.dump(project_content, project_file, indent=4)
            project_file.close()
        return True
    
    def organize_output_folder(self) -> None:
        """Organize the output folder by maintaining only the interesting results.
        """
        if not self.output_folder:
            self.log.emit("Output folder is not set.")
            return
        # Move texture obj to the output folder
        output_texture_folder = os.path.join(self.output_folder, "Texturing")
        os.makedirs(output_texture_folder, exist_ok=True)
        texture_folder = os.path.join(self.cache_folder, "Texturing")
        texture_hash_folder = os.path.join(texture_folder, os.listdir(texture_folder)[0])
        shutil.copy2(os.path.join(texture_hash_folder, "texturedMesh.obj"),
                      os.path.join(output_texture_folder, "texturedMesh.obj"))
        # Move the MTL and PNG files to the output folder
        shutil.copy2(os.path.join(texture_hash_folder, "texturedMesh.mtl"),
                     os.path.join(output_texture_folder, "texturedMesh.mtl"))
        for file in os.listdir(texture_hash_folder):
            if file.endswith(".png"):
                shutil.copy2(os.path.join(texture_hash_folder, file),
                             os.path.join(output_texture_folder, file))
        # Move the cameras to the output folder
        sfm_folder = os.path.join(self.cache_folder, "StructureFromMotion")
        sfm_hash_folder = os.path.join(sfm_folder, os.listdir(sfm_folder)[0])
        shutil.copy2(os.path.join(sfm_hash_folder, "cameras.sfm"),
                     os.path.join(self.output_folder, "cameras.sfm"))
        # Create a the point cloud, which we generate from the obj texture file, and save
        ptc = convert_obj_to_ply(obj_path=os.path.join(output_texture_folder, "texturedMesh.obj"))
        ptc_path = os.path.join(self.output_folder, "pointCloud.ply")
        o3d.io.write_point_cloud(ptc_path, ptc)
        # Remove the cache folder
        shutil.rmtree(self.cache_folder)

    def create_pyvista_cameras(self, camera_poses: dict) -> bool:
        """Create the cameras from the camera poses.

        Args:
            camera_poses (dict): The camera poses.

        Returns:
            bool: True if the cameras were created successfully, False otherwise.
        """
        # Create a pyvista object axis for each camera
        base_size = 1
        height = 1.5
        for key, cam in camera_poses.items():
            pos = cam["position"]
            rot = cam["orientation"]
            # Define pyramid points in local (camera) frame
            p0 = [-base_size, -base_size, height]
            p1 = [ base_size, -base_size, height]
            p2 = [ base_size,  base_size, height]
            p3 = [-base_size,  base_size, height]
            p4 = [0.0, 0.0, 0.0]  # tip (camera position)
            # Create a pyramid cell
            pyramid = pv.Pyramid([p0, p1, p2, p3, p4])
            # Transform the pyramid to the world frame
            transform = np.eye(4)
            transform[:3, :3] = rot
            transform[:3, 3] = pos
            pyramid.transform(transform)
            self.cameras[key] = pyramid
        return True

    # endregion
    # region Slots

    @Slot()
    def run_pipeline(self) -> None:
        """Run the specified pipeline.
        """
        if not self.input_folder or not self.output_folder or not self.cache_folder:
            self.log.emit("Input or output folder is not set.")
            return
        self.log.emit(f"Running pipeline '{self.pipeline}'...")
        # Prepare the project file
        if not self.create_project_file(self.pipeline):
            self.log.emit(f"Failed to create project file at {self.output_folder}.")
            self.finished.emit()
            return
        self.log.emit(f"Project file created at {self.project_file_path}.")
        # Run the desired pipeline
        try:
            command = [self.meshroom_batch_path, 
                    "--input", self.input_folder,
                    "--cache", self.cache_folder,
                    "--pipeline", self.project_file_path,
                    "--toNode", "Texturing_1",
                    "--forceCompute", "--forceStatus"]
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            # Print the steps to the user in the GUI
            pattern = re.compile(r"\[\d+/11\]")
            for line in process.stdout:
                if "Nodes to execute" in line or pattern.search(line):
                    self.log.emit(line)
            process.stdout.close()
            process.wait()
        except Exception as e:
            self.log.emit(f"Error running the pipeline: {e}")
            return False
        # Organize output folder to have only the texture, ptc, and cameras
        self.log.emit("Organizing output folder...")
        self.organize_output_folder()
        self.log.emit("Output folder organized. Applying scale and frame transform...")
        # Apply the scale and frame transform to the point cloud and textured mesh
        scale, global_R_scaled, global_t_scaled = compute_transformation_from_sfm(
            sfm_path=os.path.join(self.output_folder, "cameras.sfm"))
        camera_poses = get_camera_poses_utm_frame(sfm_path=os.path.join(self.output_folder, "cameras.sfm"),
                                                  scale=scale,
                                                  rotation=global_R_scaled,
                                                  t=global_t_scaled)
        transform_save_obj(
            obj_path=os.path.join(self.output_folder, "Texturing", "texturedMesh.obj"),
            mtl_path=os.path.join(self.output_folder, "Texturing", "texturedMesh.mtl"),
            scale=scale,
            rotation=global_R_scaled,
            t=global_t_scaled
        )
        ptc_path = os.path.join(self.output_folder, "pointCloud.ply")
        transform_save_ptc(
            filename=ptc_path,
            scale=scale,
            rotation=global_R_scaled,
            t=global_t_scaled
        )
        self.log.emit("Transformations applied to world frame with UTM coordinate system.")
        self.point_cloud_polydata = read_pyvista_cloud(ptc_path=ptc_path)
        self.scene_center = self.point_cloud_polydata.center
        # Working with cameras
        self.log.emit("Reading cameras...")
        self.create_pyvista_cameras(camera_poses=camera_poses)
        self.log.emit("Cameras read.")
        self.log.emit("Pipeline finished succesfully!")
        self.finished.emit()
