#include "Reconstruction.h"

#include <wx/filename.h>
#include <wx/log.h>

#include "HelperCOLMAP.h"
#include "HelperSSDRecon.h"
#include "HelperTexRecon.h"
#include "HelperScalePtcs.h"
#include "ReconstructionLog.h"
#include "ConfigurationDialog.h"
#include "Utils.h"

bool Reconstruction::Reconstruct(const std::string &projectFolder, bool generateTexture)
{
	const auto imagesFolder = projectFolder + "\\images";
	// Creating directories
	const auto tempDir = projectFolder + "\\temp";
	const auto reconstructionDir = projectFolder + "\\3DData";
	if (!Utils::CreateDir(tempDir) || !Utils::CreateDir(reconstructionDir))
	{
		return 0;
	}
	// Files
	const auto pointCloudPath = reconstructionDir + "\\PointCloud.ply";
	const auto surfacePath = reconstructionDir + "\\Surface.ply";
	// Start processing
	// Log
	ReconstructionLog log(projectFolder + "\\log.txt");
	auto bool2String = [](bool flag)
	{ if (flag) { return "Yes"; } return "No"; };
	log.write("Generate mesh - Yes");
	log.write("Generate texture - " + ((std::string)bool2String(generateTexture)));
	log.addSeparator();
	// SFM
	std::string nvmPath = tempDir + "\\cameras.nvm";
	if (!SFM(imagesFolder, nvmPath, log))
	{
		wxLogError("Erro durante o SFM");
		return 0;
	}
	// Copy the nvm file to the project folder
	const auto projectNvmPath = projectFolder + "\\cameras.nvm";
	if (!wxCopyFile(nvmPath, projectNvmPath))
	{
		wxLogError("Erro movendo os arquivos de c�mera");
		return 0;
	}
	// Dense
	// Create dense dir
	if (!Utils::CreateDir(tempDir + "/dense"))
	{
		wxLogError("Erro criando o diret�rio dense");
		return 0;
	}
	if (!Dense(imagesFolder, tempDir, pointCloudPath, log))
	{
		wxLogError("Erro durante o Dense");
		return 0;
	}
	// Meshing
	if (!Meshing(pointCloudPath, surfacePath, log))
	{
		wxLogError("Erro durante o meshing");
		return 0;
	}
	// Scale the point cloud
	if (!HelperScalePtcs::executeScalePtcs(projectNvmPath, imagesFolder, surfacePath, pointCloudPath))
	{
		wxLogError("Erro durante a aplicacao de escala real sobre a reconstrucao");
		return 0;
	}
	// Texturization
	if (generateTexture)
	{
		const auto texturizationDir = reconstructionDir + "\\TexturedSurface";
		if (!Utils::CreateDir(texturizationDir))
		{
			return 0;
		}
		const auto texturedSurfacePath = texturizationDir + "\\TexturedSurface.obj";
		if (!Reconstruction::Texturization(surfacePath, nvmPath, texturedSurfacePath, log))
		{
			wxLogError("Erro durante a texturiza��o");
			return 0;
		}
	}
	// Remove the temp dir
	wxFileName::Rmdir(tempDir, wxPATH_RMDIR_RECURSIVE);
	return 1;
}

bool Reconstruction::SFM(const std::string &imagesPath, const std::string &nvmPath, ReconstructionLog &log)
{
	log.write("Started SFM", true, true);
	if (!HelperCOLMAP::executeSparse(imagesPath, nvmPath))
	{
		log.write("Error during SFM", true, true);
		return 0;
	}
	log.write("Finished SFM", true, true);
	log.addSeparator();
	return 1;
}

bool Reconstruction::Dense(const std::string &imagesPath, const std::string &tempDir, const std::string &pointCloudOutputPath, ReconstructionLog &log)
{
	log.write("Started COLMAP dense reconstruction", true, true);
	if (!HelperCOLMAP::executeDense(imagesPath, tempDir, pointCloudOutputPath))
	{
		log.write("Error during COLMAP dense reconstruction", true, true);
		return 0;
	}
	log.write("Finished COLMAP dense reconstruction", true, true);
	log.addSeparator();
	return 1;
}

bool Reconstruction::Meshing(const std::string &pointCloudInputPath, const std::string &meshOutputPath, ReconstructionLog &log)
{
	log.write("Started SSD meshing", true, true);
	if (!HelperSSDRecon::executeMeshing(pointCloudInputPath, meshOutputPath))
	{
		log.write("Error during SSD meshing", true, true);
		return 0;
	}
	log.write("Finished SSD meshing", true, true);
	log.addSeparator();
	return 1;
}

bool Reconstruction::Texturization(const std::string &meshPath, const std::string &camerasPath, const std::string &outputPath, ReconstructionLog &log)
{
	// TexRecon
	log.write("Started TexRecon", true, true);
	if (!HelperTexRecon::executeTexRecon(camerasPath, meshPath, outputPath, ConfigurationDialog::getTexReconOptions()))
	{
		log.write("Error during TexRecon", true, true);
		return 0;
	}
	log.write("Finished TexRecon", true, true);
	log.addSeparator();
	return 1;
}
