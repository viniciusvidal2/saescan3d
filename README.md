# SAEscan 3D #

## Configuration ##
Use Visual Studio 2022 and CMake >= 3.31.5.

### Libraries ###  
1 - wxWidgest == 3.2.6 - Compile the wx_vc17.sln (folder "wxWidgets-3.1.2\build\msw") and the wxrc_14.sln for the executable. Compile in Release mode.  
2 - Eigen >= 3.4 - Matrix manipulation. You must build it to use CMake configuration.
3 - NSIS == 3.10 - For creating the installer.  

Use CMake to set everything up (both program and installer projects), or open a new project with existing code in Visual Studio (only program). If going for the second option, you must set includes, unicode, and link libraries properly.

### Dependencies  
1 - installers - Download the .7z from the lastest release in the **Releases** page. Extract it to the **saescan3d** folder (same level of the CMakeLists.txt file).  
2 - dependencies - Download the .7z from the lastest release in the **Releases** page. Extract it to the **saescan3d** folder (same level of the CMakeLists.txt file).  

## Installing ##
Download and execute the program installer from the latest release, in the **Releases** page.

## Creating the installer ##
After creating the project in Visual Studio with CMake, open it and compile and __PACKAGE__ project.
  