cmake_minimum_required(VERSION 3.14)
project(SaeScan3d)

add_definitions(/openmp)

#wxWidgets
set(wxWidgets_CONFIGURATION mswu)
find_package(wxWidgets COMPONENTS html core base REQUIRED)
include(${wxWidgets_USE_FILE})

#Eigen
find_package(Eigen3 3.4 REQUIRED NO_MODULE)

add_executable(${PROJECT_NAME}		src/App.cpp
									src/App.h
									src/Utils.cpp
									src/Utils.h
									src/ProjectImagesWizardPage.cpp
									src/ProjectImagesWizardPage.h
									src/ProjectNameWizardPage.cpp
									src/ProjectNameWizardPage.h
									src/ProjectTemplateWizardPage.cpp
									src/ProjectTemplateWizardPage.h
									src/ConfigurationDialog.cpp
									src/ConfigurationDialog.h
									src/Reconstruction.cpp
									src/Reconstruction.h
									src/ReconstructionLog.cpp
									src/ReconstructionLog.h
									src/HelperCOLMAP.cpp
									src/HelperCOLMAP.h
									src/HelperSSDRecon.cpp
									src/HelperSSDRecon.h
									src/HelperTexRecon.cpp
									src/HelperTexRecon.h
									src/HelperScalePtcs.cpp
									src/HelperScalePtcs.h
									src/ImageIO.cpp
									src/ImageIO.h
									src/Camera.cpp
									src/Camera.h
									src/json.hpp
									src/tinyply.cpp
									src/tinyply.h
									src/resource.h
									src/Resource.rc
									src/ProjectPanel.cpp
									src/ProjectPanel.h)

target_link_libraries(${PROJECT_NAME} ${wxWidgets_LIBRARIES})

target_link_libraries (${PROJECT_NAME} Eigen3::Eigen)

set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} /SUBSYSTEM:WINDOWS")

add_definitions(-DNOMINMAX
		-D_SCR_SECURE_NO_WARNINGS
		-D_CRT_SECURE_NO_WARNINGS)

#INSTALL
INSTALL(TARGETS ${PROJECT_NAME} RUNTIME DESTINATION bin)

INSTALL(DIRECTORY dependencies/ DESTINATION bin)

INSTALL(DIRECTORY installers/ DESTINATION dep)

#INSTALL(FILES programIcon.ico DESTINATION bin)

#
# CPACK macros below here
#
set (CPACK_PACKAGE_NAME "SaeScan3d")
set (CPACK_PACKAGE_VENDOR "Vendor")
set (CPACK_PACKAGE_DESCRIPTION_SUMMARY "SaeScan3d")
set (CPACK_PACKAGE_VERSION "0.0.3")
set (CPACK_PACKAGE_VERSION_MAJOR "0")
set (CPACK_PACKAGE_VERSION_MINOR "0")
set (CPACK_PACKAGE_VERSION_PATCH "3")
set (CPACK_PACKAGE_INSTALL_DIRECTORY "SaeScan3d")
set (CPACK_RESOURCE_FILE_LICENSE "${CMAKE_SOURCE_DIR}/license.txt")
set (CPACK_GENERATOR "NSIS")  # Use NSIS for an .exe installer

set(CPACK_NSIS_EXTRA_INSTALL_COMMANDS "
    CreateShortCut \\\"$DESKTOP\\\\${PROJECT_NAME}.lnk\\\" \\\"$INSTDIR\\\\bin\\\\${PROJECT_NAME}.exe\\\"
")

set(CPACK_NSIS_EXTRA_UNINSTALL_COMMANDS "
    Delete \\\"$DESKTOP\\\\${PROJECT_NAME}.lnk\\\"
")

list(APPEND CPACK_NSIS_EXTRA_INSTALL_COMMANDS " 
		ExecWait '$INSTDIR\\\\dep\\\\vcredist_x64_2015_2019.exe'
        ")

string (REPLACE ";" "\n" CPACK_NSIS_EXTRA_INSTALL_COMMANDS "${CPACK_NSIS_EXTRA_INSTALL_COMMANDS}")

# Must be after the last CPACK macros
include(CPack)

add_definitions(-DSAESCAN3D_VERSION_MAJOR=${CPACK_PACKAGE_VERSION_MAJOR}
		-DSAESCAN3D_VERSION_MINOR=${CPACK_PACKAGE_VERSION_MINOR}
		-DSAESCAN3D_VERSION_PATCH=${CPACK_PACKAGE_VERSION_PATCH})
