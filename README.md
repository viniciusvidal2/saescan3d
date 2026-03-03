# SAESCAN3D

<p align="center">
  <img src="resources/saescan3d.png" alt="My Image" width="400"/>
</p>

This software is meant so process point clouds that come from different sources, and also produce a point cloud using an SfM pipeline.

## Dependencies
The program currently relies on Python 3.8, and runs in both Windows and Linux (we recommend Ubuntu 20.04 for python compatibility). Bear in mind that virtual environments may conflict with the GUI execution, so we recommend using everything in the default python interpreter.

To install the project dependencies use the command:

```bash
cd path/to/saescan3d
pip install -r requirements/requirements_python_3_8.txt
```

## Creating the installer

### Windows

Use [this link](https://drive.google.com/file/d/1nlUXU9BMSpa88z4btUJpEUHa06c8Fw7t/view?usp=sharing) to download the compressed dependencies we need to run the SfM module pipeline, and place it under __/path/to/saescan3d/dependencies__ structure.

We use pyinstaller to generate the executable. Use the following command to create it in the subfolders __build__ and __dist__

```bash
cd path/to/sae-sam
pyinstaller.exe --clean --noconfirm saescan3d.spec
```

We use inno setup ([download with this link](https://jrsoftware.org/isdl.php#stable)) to generate the installer based on the executable generated in the previous step. The file with the instructions is in the root folder named __installer.iss__. Use it inside inno setup to compile the installer, and optionally run it in your machine to have it installed.

## Running with sample data
Get the sample data from [this link](https://drive.google.com/file/d/1vNUsQ9BndlQOqcm5lJdRDsnte_YPp17v/view?usp=sharing). Use it in this way:

- SfM Engine: load the images by selecting the folder, and start the pipeline. You should see a point cloud pop up at the end, and then you can export it to manipulate in the Mesh Manipulator model with all the available tools.
