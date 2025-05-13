from PySide6.QtCore import QObject, Signal, Slot
import subprocess
import os
import shutil
import open3d as o3d
from pathlib import Path
import json
from modules.tools import (
    get_file_placement_path, convert_obj_to_ply
)

class SfmWorker(QObject):
    # Signals
    finished = Signal()
    log = Signal(str)
    run_pipeline_signal = Signal()

    def __init__(self):
        """Initialize the SfmWorker class.
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
            subprocess.run(command, check=True)
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
        command = [self.meshroom_batch_path, 
                   "--input", self.input_folder,
                   "--cache", self.cache_folder,
                   "--pipeline", self.project_file_path,
                   "--toNode", "Texturing_1",
                   "--forceCompute", "--forceStatus"]
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            self.log.emit(f"Error running the pipeline: {e}")
            return False
        # Organize output folder to have only the texture, ptc, and cameras
        self.log.emit("Organizing output folder...")
        self.organize_output_folder()
        self.log.emit("Output folder organized. Applying scale and frame transform...")

        self.finished.emit()
