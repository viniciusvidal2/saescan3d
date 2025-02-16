#pragma once
#include <string>

class HelperCOLMAP
{
public:
	HelperCOLMAP() {};
	~HelperCOLMAP() {};

	static bool modelConverter(std::string inputPath, std::string outputPath, std::string outputType = "nvm");

	static bool executeSparse(std::string imagesPath, std::string nvmPath);

	static bool executeDense(std::string imagesPath, std::string tempDir, std::string pointCloudOutputPath);

private:
	static bool executeImageUndistorter(const std::string imagesPath, const std::string inputPath,
		const std::string outputPath, const std::string outputType);

	static bool executePatchMachStereo(const std::string workspacePath, const std::string workspaceFormat);

	static bool executeStereoFusion(const std::string workspacePath, const std::string workspaceFormat, const std::string outputPath,
		const std::string inputType = "geometric");
};