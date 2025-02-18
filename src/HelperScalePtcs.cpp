#include "HelperScalePtcs.h"
#include "Utils.h"
#include <fstream>
#include <wx/log.h>

bool HelperScalePtcs::executeScalePtcs(const std::string &inputCamerasFile, const std::string &inputImagesFolder,
									  const std::string &inputMesh, const std::string &inputPtc)
{
	std::string scalePtcsCommand(Utils::preparePath(Utils::getExecutionPath() + "/ScalePtcs/scale_ptcs.exe") +
							  " --folder " + Utils::preparePath(inputImagesFolder) +
							  " --nvm " + Utils::preparePath(inputCamerasFile) +
							  " --cloud " + Utils::preparePath(inputPtc) +
							  " --mesh " + Utils::preparePath(inputMesh));
	if (!Utils::startProcess(scalePtcsCommand))
	{
		wxLogError("Error with Scale Reconstruction Process");
		return 0;
	}
	return 1;
}
