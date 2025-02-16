#include "HelperTexRecon.h"

#include <fstream>

#include <Eigen/Dense>

#include <wx/log.h>

#include "Camera.h"
#include "Utils.h"
#include "ImageIO.h"

bool HelperTexRecon::executeTexRecon(const std::string & inputCamerasFile, const std::string & inputMesh, const std::string & outputMesh, const TexRecon::Options & options)
{
	//Remove the .obj since TexRecon does not use it
	std::string outputPath = outputMesh.substr(0, outputMesh.find_last_of('.'));
	if (!createCamerasFile(inputCamerasFile, outputPath + ".cameras"))
	{
		wxLogError("Error creating the .cameras file for TexRecon");
		return 0;
	}
	std::stringstream texReconParameters;
	texReconParameters << Utils::preparePath(Utils::getExecutionPath() + "/TexRecon/texrecon.exe") <<
		" --data_term=" + options.getDataTerm() <<
		" --outlier_removal=" + options.getOutlierRemoval() <<
		" --tone_mapping=" + options.getToneMapping() << " --no_intermediate_results ";
	if (!options.geometricVisibilityTest)
	{
		texReconParameters << "--skip_geometric_visibility_test ";
	}
	if (!options.globalSeamLeveling)
	{
		texReconParameters << "--skip_global_seam_leveling ";
	}
	if (!options.localSeamLeveling)
	{
		texReconParameters << "--skip_local_seam_leveling ";
	}
	if (!options.holeFilling)
	{
		texReconParameters << "--skip_hole_filling ";
	}
	if (options.keepUnseenFaces)
	{
		texReconParameters << "--keep_unseen_faces ";
	}
	texReconParameters << Utils::preparePath(outputPath + ".cameras") << " " <<
		Utils::preparePath(inputMesh) << " " <<
		Utils::preparePath(outputPath);
	if (!Utils::startProcess(texReconParameters.str()))
	{
		wxLogError("Error with TexRecon");
		return 0;
	}
	if (!Utils::exists(outputMesh))
	{
		wxLogError("No textured mesh generated with TexRecon");
		return 0;
	}
	return 1;
}

bool HelperTexRecon::createCamerasFile(const std::string & inputCamerasFile, const std::string & outputCamerasFile)
{
	if (!Utils::exists(inputCamerasFile))
	{
		return 0;
	}
	std::vector<Camera*> cameras;
	if (!ImageIO::loadCameraParameters(inputCamerasFile, cameras))
	{
		return 0;
	}
	//Write .cameras file
	std::ofstream camerasFile(outputCamerasFile);
	if (!camerasFile.is_open())
	{
		return 0;
	}
	camerasFile << cameras.size() << "\n";
	for (const auto& camera : cameras)
	{
		camerasFile << camera->filePath << " ";
		auto matrixRt = camera->getMatrixRt();
		//Translation
		for (size_t j = 0; j < 3; j++)
		{
			camerasFile << matrixRt(j, 3) << " ";
		}
		//Rotation
		for (size_t i = 0; i < 3; i++)
		{
			for (size_t j = 0; j < 3; j++)
			{
				camerasFile << matrixRt(i, j) << " ";
			}
		}
		camerasFile << camera->getFocalX() / static_cast<float>(camera->getWidth()) << " 0 0 " <<
			static_cast<float>(camera->getFocalX()) / static_cast<float>(camera->getFocalY()) <<
			" " << camera->getPrincipalPointX() / static_cast<float>(camera->getWidth()) <<
			" " << camera->getPrincipalPointY() / static_cast<float>(camera->getHeight()) << "\n";
	}
	camerasFile.close();
	return 1;
}
