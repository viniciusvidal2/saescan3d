#pragma once

#include <string>
#include <vector>

class Camera;
namespace easyexif
{
	class EXIFInfo;
};

class ImageIO
{
public:
	static bool getImageSize(const std::string& imagePath, unsigned int& width, unsigned int& height);

	//Test if image paths exist
	static bool getImagePathsExist(std::vector<std::string> &imagePaths, const std::string& newImageDir = "");

	//Camera
	//Load the camera parameters
	static bool loadCameraParameters(const std::string& filePath, std::vector<Camera*> &cameras);

	static void sortCamerasByName(std::vector<Camera*>& cameras);

	static bool getCamerasFileImagePaths(const std::string& camerasFilePath, std::vector<std::string> &imagePaths);

	static bool replaceCamerasFileImageDir(const std::string& camerasFilePath, const std::string& newImgDir);

	static unsigned int GetNumberOfCameras(const std::string& camerasFilePath);

	//Output
	static bool saveCameras(const std::string& camerasFilePath, const std::vector<Camera*> &cameras);


private:

	//NVM
	//Get the image paths from a NVM file
	static bool getNVMImagePaths(const std::string& nvmPath, std::vector<std::string> &imagePaths);
	//Replace the image dir of the nvm
	static bool replaceNVMImageDir(const std::string& nvmPath, const std::string& newImgDir);
	static unsigned int GetNumberOfCamerasNVM(const std::string& camerasFilePath);
	//Input
	static Camera* getCameraFromNVMLine(const std::string& nvmLine);
	//Output
	static std::string getNVMLineFromCamera(const Camera& camera);
	static bool saveNVMFile(const std::string& filename, const std::vector<Camera*> &cameras);

	//SFM
	//Get the image paths from a SFM file
	static bool getSFMImagePaths(const std::string& sfmPath, std::vector<std::string> &imagePaths);
	//Replace the image dir of the sfm
	static bool replaceSFMImageDir(const std::string& sfmPath, const std::string& newImgDir);
	static unsigned int GetNumberOfCamerasSFM(const std::string& camerasFilePath);
	//Input
	static Camera* getCameraFromSFMLine(const std::string& sfmLine);
	//Output
	static std::string getSFMLineFromCamera(const Camera& camera);
	static bool saveSFMFile(const std::string& filename, const std::vector<Camera*> &cameras);

};