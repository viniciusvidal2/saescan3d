#include "HelperCOLMAP.h"

#include <fstream>

#include <wx/log.h>
#include <wx/dir.h>

#include "ConfigurationDialog.h"
#include "ImageIO.h"
#include "Utils.h"

bool HelperCOLMAP::modelConverter(std::string inputPath, std::string outputPath, std::string outputType)
{
	std::string colmapParameters(Utils::preparePath(Utils::getExecutionPath() + "/COLMAP/COLMAP.bat") +
		" model_converter --input_path=" + Utils::preparePath(inputPath) +
		" --output_path=" + Utils::preparePath(outputPath) +
		" --output_type=" + Utils::preparePath(outputType)
	);
	if (!Utils::startProcess(colmapParameters))
	{
		wxLogError("Error with COLMAP model converter");
		return 0;
	}
	if (!Utils::exists(outputPath))
	{
		wxLogError("No file was generated");
		return 0;
	}
	return 1;
}

bool HelperCOLMAP::executeSparse(std::string imagesPath, std::string nvmPath)
{
	std::string colmapParameters(Utils::preparePath(Utils::getExecutionPath() + "/COLMAP/COLMAP.bat") +
		" automatic_reconstructor --image_path=" + Utils::preparePath(imagesPath) +
		" --workspace_path=" + Utils::preparePath(Utils::getPath(nvmPath, false)) +
		" --quality=" + ConfigurationDialog::getSparseQuality() +
		" --use_gpu=" + ConfigurationDialog::getUseGPU() +
		" --dense=0"
	);
	if (!Utils::startProcess(colmapParameters))
	{
		wxLogError("Error with COLMAP sparse");
		return 0;
	}
	std::string camerasBinPath = Utils::getPath(nvmPath, false);
	camerasBinPath += "/sparse/0/cameras.bin";
	if (!Utils::exists(camerasBinPath))
	{
		wxLogError("No camera was generated");
		return 0;
	}
	//Convert cameras.bin to .nvm
	if (!modelConverter(Utils::getPath(nvmPath, false) + "/sparse/0", nvmPath))
	{
		return 0;
	}
	ImageIO::replaceCamerasFileImageDir(nvmPath, imagesPath);
	return 1;
}

bool HelperCOLMAP::executeDense(std::string imagesPath, std::string tempDir, std::string pointCloudOutputPath)
{
	if (!executeImageUndistorter(imagesPath, tempDir + "/sparse/0", tempDir + "/dense", "COLMAP"))
	{
		return 0;
	}
	if (!executePatchMachStereo(tempDir + "/dense", "COLMAP"))
	{
		return 0;
	}
	if (!executeStereoFusion(tempDir + "/dense", "COLMAP", pointCloudOutputPath))
	{
		return 0;
	}
	return 1;
}

bool HelperCOLMAP::executeImageUndistorter(const std::string imagesPath, const std::string inputPath,
	const std::string outputPath, const std::string outputType)
{
	// Quality
	auto quality = ConfigurationDialog::getDenseQuality();

	int max_image_size = -1;

	if (quality == "low")
	{
		max_image_size = 1000;
	}
	else if (quality == "medium")
	{
		max_image_size = 1600;
	}
	else if (quality == "high")
	{
		max_image_size = 2400;
	}

	std::string colmapParameters(Utils::preparePath(Utils::getExecutionPath() + "/COLMAP/COLMAP.bat") +
		" image_undistorter --image_path=" + Utils::preparePath(imagesPath) +
		" --input_path=" + Utils::preparePath(inputPath) +
		" --output_path=" + Utils::preparePath(outputPath) +
		" --output_type=" + outputType +
		" --max_image_size=" + std::to_string(max_image_size)
	);
	if (!Utils::startProcess(colmapParameters))
	{
		wxLogError("Error with COLMAP image undistorter");
		return 0;
	}
	wxDir dir(outputPath + "/images");
	if (!dir.IsOpened())
	{
		wxLogError("Error with COLMAP image undistorter results");
		return 0;
	}
	if (!dir.HasFiles())
	{
		wxLogError("No images created with COLMAP image undistorter");
		return 0;
	}
	return 1;
}

bool HelperCOLMAP::executePatchMachStereo(const std::string workspacePath, const std::string workspaceFormat)
{
	// Quality
	auto quality = ConfigurationDialog::getDenseQuality();

	int max_image_size = -1;
	int window_radius = 5;
	int window_step = 1;
	int num_samples = 15;
	int num_iterations = 5;
	const int geom_consistency = 1; // BUG: always 1!

	if (quality == "low")
	{
		max_image_size = 1000;
		window_radius = 4;
		window_step = 2;
		num_samples /= 2;
		num_iterations = 3;
	}
	else if (quality == "medium")
	{
		max_image_size = 1600;
		window_radius = 4;
		window_step = 2;
		num_samples /= 1.5;
	}
	else if (quality == "high")
	{
		max_image_size = 2400;
	}

	std::string colmapParameters(Utils::preparePath(Utils::getExecutionPath() + "/COLMAP/COLMAP.bat") +
		" patch_match_stereo --workspace_path=" + Utils::preparePath(workspacePath) +
		" --workspace_format=" + workspaceFormat +
		" --PatchMatchStereo.max_image_size=" + std::to_string(max_image_size) +
		" --PatchMatchStereo.window_radius=" + std::to_string(window_radius) +
		" --PatchMatchStereo.window_step=" + std::to_string(window_step) +
		" --PatchMatchStereo.num_samples=" + std::to_string(num_samples) +
		" --PatchMatchStereo.num_iterations=" + std::to_string(num_iterations) +
		" --PatchMatchStereo.geom_consistency=" + std::to_string(geom_consistency)
	);
	if (!Utils::startProcess(colmapParameters))
	{
		wxLogError("Error with COLMAP patch match stereo");
		return 0;
	}
	wxDir dir(workspacePath + "/stereo/depth_maps");
	if (!dir.IsOpened())
	{
		wxLogError("Error with COLMAP patch match stereo results");
		return 0;
	}
	if (!dir.HasFiles())
	{
		wxLogError("No depth maps created with COLMAP patch match stereo");
		return 0;
	}
	return 1;
}

bool HelperCOLMAP::executeStereoFusion(const std::string workspacePath, const std::string workspaceFormat, const std::string outputPath, const std::string inputType)
{
	// Quality
	auto quality = ConfigurationDialog::getDenseQuality();

	int check_num_images = 50;
	int max_image_size = -1;

	if (quality == "low")
	{
		check_num_images /= 2;
		max_image_size = 1000;
	}
	else if (quality == "medium")
	{
		check_num_images /= 1.5;
		max_image_size = 1600;
	}
	else if (quality == "high")
	{
		max_image_size = 2400;
	}

	std::string colmapParameters(Utils::preparePath(Utils::getExecutionPath() + "/COLMAP/COLMAP.bat") +
		" stereo_fusion --workspace_path=" + Utils::preparePath(workspacePath) +
		" --workspace_format=" + workspaceFormat +
		" --input_type=" + inputType +
		" --output_path=" + Utils::preparePath(outputPath) +
		" --StereoFusion.check_num_images=" + std::to_string(check_num_images) +
		" --StereoFusion.max_image_size=" + std::to_string(max_image_size)
	);
	if (!Utils::startProcess(colmapParameters))
	{
		wxLogError("Error with COLMAP stereo fusion");
		return 0;
	}
	if (!Utils::exists(outputPath))
	{
		wxLogError("No point cloud created with COLMAP stereo fusion");
		return 0;
	}
	wxStructStat strucStat;
	wxStat(outputPath, &strucStat);
	if (strucStat.st_size < 500)// File with less than 500 bytes is probably wrong
	{
		wxLogError("No valid point cloud created with COLMAP stereo fusion");
		return 0;
	}
	// Remove the temp file
	if (Utils::exists(outputPath + ".vis"))
	{
		wxRemoveFile(outputPath + ".vis");
	}
	return 1;
}
