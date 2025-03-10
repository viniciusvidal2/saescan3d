#pragma once
#include <sstream>
#include <string>

class HelperScalePtcs
{
public:
	HelperScalePtcs() {};
	~HelperScalePtcs() {};

	// Run method to scale ptcs according to GPS coordinates
	static bool executeScalePtcs(const std::string &inputCamerasFile, const std::string &inputImagesFolder,
								 const std::string &inputPtc, const std::string &texturePath);
};
