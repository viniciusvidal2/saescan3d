#pragma once

#include <string>

class ReconstructionLog;

class Reconstruction
{
public:
	Reconstruction() {};
	~Reconstruction() {};

	static bool Reconstruct(const std::string& projectFolder, bool generateTexture);

	//SFM
	static bool SFM(const std::string& imagesPath, const std::string& nvmPath, ReconstructionLog & log);
	//Dense
	static bool Dense(const std::string& imagesPath, const std::string & tempDir, const std::string& pointCloudOutputPath, ReconstructionLog & log);
	//Meshing
	static bool Meshing(const std::string & pointCloudInputPath, const std::string& meshOutputPath, ReconstructionLog & log);
	//Texturization
	static bool Texturization(const std::string& meshPath, const std::string& camerasPath,
		const std::string& outputPath, ReconstructionLog & log);

private:

};