#pragma once
#include <string>

class HelperSSDRecon
{
public:
	HelperSSDRecon() {};
	~HelperSSDRecon() {};

	static bool executeMeshing(std::string inputPath, std::string outputPath);

private:
	static bool executeSSD(std::string inputPath, std::string outputPath);

	static bool executeSurfaceTrimmer(std::string inputPath);

	// We need to open and save the ply because TexRecon does not read the SSDRecon ply
	static void fixBadPLY(std::string inputPath);

};