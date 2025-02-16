#include "ImageIO.h"

#include <sstream>
#include <iostream>
#include <fstream>

#include <windows.h>
//  Define min max macros required by GDI+ headers.
//#ifndef max
//#define max(a,b) (((a) > (b)) ? (a) : (b))
//#else
//#error max macro is already defined
//#endif
//#ifndef min
//#define min(a,b) (((a) < (b)) ? (a) : (b))
//#else
//#error min macro is already defined
//#endif

#include <gdiplus.h>

//  Undefine min max macros so they won't collide with <limits> header content.
#undef min
#undef max

#include <Eigen/Dense>

#include "Utils.h"
#include "Camera.h"


bool ImageIO::getImageSize(const std::string& imagePath, unsigned int& width, unsigned int& height)
{
	if (!Utils::exists(imagePath))
	{
		return 0;
	}
	Gdiplus::GdiplusStartupInput gdiplusStartupInput;
	ULONG_PTR gdiplusToken;
	GdiplusStartup(&gdiplusToken, &gdiplusStartupInput, NULL);
	std::wstring wide_string = std::wstring(imagePath.begin(), imagePath.end());
	Gdiplus::Image* img = new Gdiplus::Image(wide_string.c_str());
	if (img)
	{
		height = img->GetHeight();
		width = img->GetWidth();
		delete img;
		Gdiplus::GdiplusShutdown(gdiplusToken);
		return 1;
	}
	delete img;
	Gdiplus::GdiplusShutdown(gdiplusToken);
	return 0;
}

bool ImageIO::getImagePathsExist(std::vector<std::string>& imagePaths, const std::string& newImageDir)
{
	if (imagePaths.size() == 0)
	{
		return 0;
	}
	for (auto imagePath : imagePaths)
	{
		if (newImageDir != "")
		{
			std::string imageName = "";
			if (imagePath.find_last_of('/') != std::string::npos)
			{
				imageName = imagePath.substr(imagePath.find_last_of('/') + 1, imagePath.size());
				imagePath = newImageDir + "/" + imageName;
			}
			else
			{
				imageName = imagePath.substr(imagePath.find_last_of('\\') + 1, imagePath.size());
				imagePath = newImageDir + "\\" + imageName;
			}
		}
		if (!Utils::exists(imagePath))
		{
			return 0;
		}
	}
	return 1;
}

bool ImageIO::loadCameraParameters(const std::string& filePath, std::vector<Camera*>& cameras)
{
	std::ifstream parametersFile(filePath);
	if (!parametersFile.good())
	{
		return 0;
	}
	std::string line;
	unsigned int qtdCameras = 0;
	const std::string extension = Utils::getFileExtension(filePath);
	//SFM
	if (extension == "sfm")
	{
		std::getline(parametersFile, line, '\n');
		qtdCameras = std::stoi(line);
		std::getline(parametersFile, line, '\n');
	}
	else if(extension == "nvm")//NVM
	{
		std::getline(parametersFile, line, '\n');
		std::getline(parametersFile, line, '\n');
		std::getline(parametersFile, line, '\n');
		qtdCameras = std::stoi(line);
	}
	cameras.reserve(qtdCameras);
	for (unsigned int i = 0; i < qtdCameras; i++)
	{
		std::getline(parametersFile, line, '\n');
		Camera* camera;
		if (extension == "sfm")
		{
			camera = getCameraFromSFMLine(line);
		}
		else if (extension == "nvm")
		{
			camera = getCameraFromNVMLine(line);
		}
		if (camera)
		{
			cameras.emplace_back(camera);
		}
		else
		{
			for (auto cam : cameras)
			{
				delete cam;
			}
			return 0;
		}
	}
	sortCamerasByName(cameras);
	parametersFile.close();
	return 1;
}

void ImageIO::sortCamerasByName(std::vector<Camera*>& cameras)
{
	auto sortByFilename = [] (Camera* i, Camera* j) {
		return (i->filePath < j->filePath);
	};
	std::sort(cameras.begin(), cameras.end(), sortByFilename);
}

bool ImageIO::getCamerasFileImagePaths(const std::string& camerasFilePath, std::vector<std::string>& imagePaths)
{
	if (Utils::getFileExtension(camerasFilePath) == "sfm")
	{
		return ImageIO::getSFMImagePaths(camerasFilePath, imagePaths);
	}
	else if (Utils::getFileExtension(camerasFilePath) == "nvm")
	{
		return ImageIO::getNVMImagePaths(camerasFilePath, imagePaths);
	}
	return 0;
}

bool ImageIO::replaceCamerasFileImageDir(const std::string& camerasFilePath, const std::string& newImgDir)
{
	if (Utils::getFileExtension(camerasFilePath) == "sfm")
	{
		return ImageIO::replaceSFMImageDir(camerasFilePath, newImgDir);
	}
	else if (Utils::getFileExtension(camerasFilePath) == "nvm")
	{
		return ImageIO::replaceNVMImageDir(camerasFilePath, newImgDir);
	}
	return 0;
}

unsigned int ImageIO::GetNumberOfCameras(const std::string & camerasFilePath)
{
	if (!Utils::exists(camerasFilePath))
	{
		return 0;
	}
	if (Utils::getFileExtension(camerasFilePath) == "sfm")
	{
		return ImageIO::GetNumberOfCamerasSFM(camerasFilePath);
	}
	else if (Utils::getFileExtension(camerasFilePath) == "nvm")
	{
		return ImageIO::GetNumberOfCamerasNVM(camerasFilePath);
	}
	return 0;
}

bool ImageIO::saveCameras(const std::string & camerasFilePath, const std::vector<Camera*>& cameras)
{
	if (Utils::getFileExtension(camerasFilePath) == "sfm")
	{
		return saveSFMFile(camerasFilePath, cameras);
	}
	else if(Utils::getFileExtension(camerasFilePath) == "nvm")
	{
		return saveNVMFile(camerasFilePath, cameras);
	}
	return 0;
}

//NVM
bool ImageIO::getNVMImagePaths(const std::string& nvmPath, std::vector<std::string>& imagePaths)
{
	std::ifstream in(nvmPath.c_str());
	if (!in.good())
	{
		return 0;
	}
	//Check NVM file signature
	std::string signature;
	in >> signature;
	if (signature != "NVM_V3")
	{
		return 0;
	}
	//Discard the rest of the line
	std::getline(in, signature);
	//Read number of views
	int qtdCameras = 0;
	in >> qtdCameras;
	if (qtdCameras < 0 || qtdCameras > 10000)
	{
		return 0;
	}
	//Read views
	std::string filePath;
	imagePaths.reserve(qtdCameras);
	for (int i = 0; i < qtdCameras; ++i)
	{
		//get the filePath
		in >> filePath;
		imagePaths.emplace_back(filePath);
		//Used to jump to the next line
		std::getline(in, signature);
	}
	in.close();
	return 1;
}

bool ImageIO::replaceNVMImageDir(const std::string& nvmPath, const std::string& newImgDir)
{
	std::ifstream in(nvmPath.c_str());
	std::stringstream out;
	if (!in.good())
	{
		return 0;
	}
	//NVM_V3 line
	std::string line;
	std::getline(in, line, '\n');
	out << line << "\n\n";
	/* Read number of views. */
	int num_views = 0;
	in >> num_views;
	out << num_views << "\n";
	if (num_views < 0 || num_views > 10000)
	{
		return 0;
	}
	std::string imagePath;
	std::string imgName;
	for (int i = 0; i < num_views; ++i)
	{
		/* Filename*/
		in >> imagePath;
		imgName = Utils::getFileName(imagePath, true);
		out << newImgDir << "/" << imgName << " ";
		double temp;
		for (int j = 0; j < 10; j++)
		{
			in >> temp;
			if (j != 9)
			{
				out << temp << " ";
			}
			else
			{
				out << temp;
			}
		}
		//Avoid double space when we finish the cameras
		if (i < num_views - 1)
		{
			out << "\n";
		}
		in.eof();
	}
	while (getline(in, line, '\n'))
	{
		out << line << "\n";
	}
	in.close();
	//Overwrite the file
	std::ofstream outFile(nvmPath.c_str());
	if (!outFile.good())
	{
		return 0;
	}
	outFile << out.rdbuf();
	outFile.close();
	return 1;
}

unsigned int ImageIO::GetNumberOfCamerasNVM(const std::string & camerasFilePath)
{
	std::ifstream nvmFile(camerasFilePath);
	std::string line;
	if (nvmFile.is_open())
	{
		getline(nvmFile, line, '\n');
		getline(nvmFile, line, '\n');
		getline(nvmFile, line, '\n');
		nvmFile.close();
		return std::atoi(line.c_str());
	}
	return 0;
}

Camera* ImageIO::getCameraFromNVMLine(const std::string & nvmLine)
{
	std::vector<std::string> tokens;
	std::istringstream iss(nvmLine);
	std::string token;
	while (std::getline(iss, token, ' '))
	{
		tokens.push_back(token);
	}
	//NVM file
	if (tokens.size() != 11)
	{
		return nullptr;
	}
	std::string filePath = tokens[0];
	if (!Utils::exists(filePath))
	{
		return nullptr;
	}
	unsigned int width, height;
	if (!getImageSize(filePath, width, height))
	{
		return nullptr;
	}
	Eigen::Matrix4d matrixRT;
	float focalDistance[2] = { std::stof(tokens[1]) };
	focalDistance[1] = focalDistance[0];

	//Camera rotation and center
	double quat[4];
	for (int j = 0; j < 4; ++j)
		quat[j] = std::stod(tokens[2 + j]);

	Eigen::Quaterniond quaternion(quat[0], quat[1], quat[2], quat[3]);
	auto rotation = quaternion.toRotationMatrix();
	double center[3], trans[3];
	for (int j = 0; j < 3; ++j)
		center[j] = std::stod(tokens[6 + j]);

	trans[0] = trans[1] = trans[2] = 0;
	for (int j = 0; j < 3; j++)
	{
		for (int k = 0; k < 3; k++)
		{
			trans[j] += rotation(j, k) * (-center[k]);
		}
	}
	//Rotation
	for (int j = 0; j < 3; j++)
	{
		for (int k = 0; k < 3; k++)
		{
			matrixRT(j, k) = rotation(j, k);
		}
		//Translation
		matrixRT(j, 3) = trans[j];
	}
	//Last line
	matrixRT(3, 0) = matrixRT(3, 1) = matrixRT(3, 2) = 0; matrixRT(3, 3) = 1;
	float principalPoint[2] = { width / 2.f, height / 2.f };
	return new Camera(filePath, focalDistance, principalPoint, width, height, matrixRT);
}

std::string ImageIO::getNVMLineFromCamera(const Camera & camera)
{
	std::stringstream ss;
	ss << camera.filePath << " " << camera.getFocalX() << " ";
	//MatrixR to quaternion
	Eigen::Matrix3d matrixR;
	auto matrixRt = camera.getMatrixRt();
	for (size_t i = 0; i < 3; i++)
	{
		for (size_t j = 0; j < 3; j++)
		{
			matrixR(i, j) = matrixRt(i, j);
		}
	}
	Eigen::Quaterniond quaternion(matrixR);
	ss << quaternion.w() << " " << quaternion.x() << " " << quaternion.y() << " " << quaternion.z() << " ";
	auto inverted = matrixRt.inverse();
	double center[3] = { 0.0,0.0,0.0 };
	for (int j = 0; j < 3; j++)
	{
		for (int k = 0; k < 3; k++)
		{
			center[j] += -inverted(j, k) * matrixRt(k, 3);
		}
	}
	ss << center[0] << " " << center[1] << " " << center[2] << " 0 0" << "\n";
	return ss.str();
}

bool ImageIO::saveNVMFile(const std::string& filename, const std::vector<Camera*> &cameras)
{
	std::ofstream nvmFile;
	nvmFile.open(filename);
	if (nvmFile.is_open())
	{
		nvmFile << "NVM_V3\n\n" << cameras.size() << "\n";
		for (const auto &camera : cameras)
		{
			nvmFile << getNVMLineFromCamera(*camera);
		}
		nvmFile << "\n";
	}
	else
	{
		return 0;
	}
	nvmFile.close();
	return 1;
}

//SFM
bool ImageIO::getSFMImagePaths(const std::string& sfmPath, std::vector<std::string>& imagePaths)
{
	std::ifstream in(sfmPath.c_str());
	if (!in.good())
	{
		return 0;
	}
	//Read number of views
	int qtdCameras = 0;
	in >> qtdCameras;
	std::string temp;
	//Discard the rest of the line
	std::getline(in, temp);
	if (qtdCameras < 0 || qtdCameras > 10000)
	{
		return 0;
	}
	//Read views
	std::string filePath;
	imagePaths.reserve(qtdCameras);
	for (int i = 0; i < qtdCameras; ++i)
	{
		//get the filePath
		in >> filePath;
		imagePaths.emplace_back(filePath);
		//Used to jump to the next line
		std::getline(in, temp);
	}
	in.close();
	return 1;
}

bool ImageIO::replaceSFMImageDir(const std::string& sfmPath, const std::string& newImgDir)
{
	std::ifstream in(sfmPath.c_str());
	std::stringstream out;
	if (!in.good())
	{
		return 0;
	}
	// Read number of views.
	int num_views = 0;
	in >> num_views;
	out << num_views << "\n";
	//Empty line
	std::string line;
	std::getline(in, line, '\n');
	out << line << "\n";
	if (num_views < 0 || num_views > 10000)
	{
		return 0;
	}
	std::string imagePath;
	std::string imgName;
	for (int i = 0; i < num_views; ++i)
	{
		/* Filename*/
		in >> imagePath;
		imgName = Utils::getFileName(imagePath, true);
		out << newImgDir << "/" << imgName << " ";
		double temp;
		for (int j = 0; j < 16; j++)
		{
			in >> temp;
			if (j != 15)
			{
				out << temp << " ";
			}
			else
			{
				out << temp;
			}
		}
		//Avoid double space when we finish the cameras
		if (i < num_views - 1)
		{
			out << "\n";
		}
		in.eof();
	}
	while (getline(in, line, '\n'))
	{
		out << line << "\n";
	}
	in.close();
	//Overwrite the file
	std::ofstream outFile(sfmPath.c_str());
	if (!outFile.good())
	{
		return 0;
	}
	outFile << out.rdbuf();
	outFile.close();
	return 1;
}

unsigned int ImageIO::GetNumberOfCamerasSFM(const std::string & camerasFilePath)
{
	std::ifstream sfmFile(camerasFilePath);
	std::string line;
	if (sfmFile.is_open())
	{
		std::getline(sfmFile, line, '\n');
		sfmFile.close();
		return std::atoi(line.c_str());
	}
	return 0;
}

Camera * ImageIO::getCameraFromSFMLine(const std::string & sfmLine)
{
	std::vector<std::string> tokens;
	std::istringstream iss(sfmLine);
	std::string token;
	while (std::getline(iss, token, ' '))
	{
		tokens.push_back(token);
	}
	
	if (tokens.size() != 17)
	{
		return nullptr;
	}
	std::string filePath = tokens[0];
	if (!Utils::exists(filePath))
	{
		return nullptr;
	}
	unsigned int width, height;
	if (!getImageSize(filePath, width, height))
	{
		return nullptr;
	}
	Eigen::Matrix4d matrixRT;
	//Rotation
	for (int j = 0; j < 3; j++)
	{
		for (int k = 0; k < 3; k++)
		{
			matrixRT(j, k) = std::stod(tokens[1 + (j * 3) + k]);
		}
		//Translation
		matrixRT(j, 3) = std::stod(tokens[10 + j]);
	}
	//Last line
	matrixRT(3, 0) = matrixRT(3, 1) = matrixRT(3, 2) = 0; matrixRT(3, 3) = 1;
	float focalDistance[2] = { std::stof(tokens[13]), std::stof(tokens[14]) };
	float principalPoint[2] = { std::stof(tokens[15]), std::stof(tokens[16]) };
	return new Camera(filePath, focalDistance, principalPoint, width, height, matrixRT);
}

std::string ImageIO::getSFMLineFromCamera(const Camera & camera)
{
	std::stringstream ss;
	ss << camera.filePath << " ";
	auto matrixRt = camera.getMatrixRt();
	//Rotation
	for (size_t i = 0; i < 3; i++)
	{
		for (size_t j = 0; j < 3; j++)
		{
			ss << matrixRt(i, j) << " ";
		}
	}
	//Translation
	for (size_t j = 0; j < 3; j++)
	{
		ss << matrixRt(j, 3) << " ";
	}
	ss << camera.getFocalX() << " " << camera.getFocalY() << " " << camera.getPrincipalPointX() << " " << camera.getPrincipalPointY() << "\n";
	return ss.str();
}

bool ImageIO::saveSFMFile(const std::string & filename, const std::vector<Camera*>& cameras)
{
	std::ofstream sfmFile;
	sfmFile.open(filename);
	if (sfmFile.is_open())
	{
		sfmFile << cameras.size() << "\n\n";
		for (const auto &camera : cameras)
		{
			sfmFile << getSFMLineFromCamera(*camera);
		}
	}
	else
	{
		return 0;
	}
	sfmFile.close();
	return 1;
}