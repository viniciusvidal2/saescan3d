#include "HelperScalePtcs.h"
#include "Utils.h"
#include <fstream>
#include <wx/log.h>

bool HelperScalePtcs::executeScalePtcs(const std::string &inputCamerasFile, const std::string &inputImagesFolder,
									   const std::string &inputPtc, const std::string &texturePath)
{
	std::string scalePtcsCommand(Utils::preparePath(Utils::getExecutionPath() + "/ScalePtcs/scale_ptcs.exe") +
								 " --folder " + Utils::preparePath(inputImagesFolder) +
								 " --nvm " + Utils::preparePath(inputCamerasFile) +
								 " --cloud " + Utils::preparePath(inputPtc) +
								 " --obj " + Utils::preparePath(texturePath));
	if (!Utils::startProcess(scalePtcsCommand))
	{
		wxLogError("Error with Scale Reconstruction Process");
		return 0;
	}
	return 1;
}
