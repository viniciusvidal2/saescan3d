from PySide6.QtCore import QObject, Signal, Slot
import subprocess
import json
from modules.path_tool import get_file_placement_path

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
                   "--pipeline", self.pipelines[pipeline]]
        print(command)
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            self.log.emit(f"Error creating project file: {e}")
            return False
        # Read the project content as JSON and change the output texture format to PNG
        with open(self.project_file_path, "r") as project_file:
            project_content = json.load(project_file)
            project_content["outputTextureFileType"] = "png"
            project_file.close()
        # Write the modified project content back to the project file
        with open(self.project_file_path, "w") as project_file:
            json.dump(project_content, project_file, indent=4)
            project_file.close()
        return True

    @Slot()
    def run_pipeline(self) -> None:
        """Run the specified pipeline.
        """
        self.log.emit(f"Running pipeline '{self.pipeline}'...")
        # Prepare the project file
        if not self.create_project_file(self.pipeline):
            self.log.emit(f"Failed to create project file at {self.output_folder}.")
            self.finished.emit()
            return
        self.log.emit(f"Project file created at {self.project_file_path}.")
        # Run the desired pipeline
        command = [self.meshroom_batch_path, 
                   "--project_file", self.project_file_path, 
                   "--output", self.output_folder]
        print(command)
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proc:
            for line in proc.stdout:
                self.log.emit(line.strip())
            exit_code = proc.wait()
        if exit_code == 0:
            self.log.emit("Pipeline finished successfully.")
        else:
            self.log.emit(f"Pipeline failed with exit code {exit_code}.")
        self.finished.emit()
