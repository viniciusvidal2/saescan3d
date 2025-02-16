#pragma once
#include <sstream>
#include <string>

namespace TexRecon
{
	struct Options
	{
		Options() {};
		Options(unsigned int dataTerm, unsigned int outlierRemoval, unsigned int toneMapping, bool geometricVisibilityTest,
			bool globalSeamLeveling, bool localSeamLeveling, bool holeFilling, bool keepUnseenFaces) :
			dataTerm(dataTerm), outlierRemoval(outlierRemoval), toneMapping(toneMapping), geometricVisibilityTest(geometricVisibilityTest),
			globalSeamLeveling(globalSeamLeveling), localSeamLeveling(localSeamLeveling), holeFilling(holeFilling),
			keepUnseenFaces(keepUnseenFaces) {};
		// 0 - Area 1 - Gmi
		unsigned int dataTerm;
		// 0 - None 1 - Gauss damping 2 - Gauss clamping
		unsigned int outlierRemoval;
		// 0 - None 1 - Gamma
		unsigned int toneMapping;
		bool geometricVisibilityTest;
		bool globalSeamLeveling;
		bool localSeamLeveling;
		bool holeFilling;
		bool keepUnseenFaces;

		std::string getDataTerm() const
		{
			switch (dataTerm)
			{
			case 0:
				return "area";
			case 1:
				return "gmi";
			default:
				return "gmi";
			}
		}
		std::string getOutlierRemoval() const
		{
			switch (outlierRemoval)
			{
			case 0:
				return "none";
			case 1:
				return "gauss_damping";
			case 2:
				return "gauss_clamping";
			default:
				return "none";
			}
		}
		std::string getToneMapping() const
		{
			switch (toneMapping)
			{
			case 0:
				return "none";
			case 1:
				return "gamma";
			default:
				return "none";
			}
		}
		std::string getBoolParameter(bool flag) const
		{
			if (flag)
			{
				return "true";
			}
			else
			{
				return "false";
			}
		}
		std::string print() const
		{
			std::stringstream s;
			s << "Data term " << getDataTerm() << "\n" <<
				"Outlier removal " << getOutlierRemoval() << "\n" <<
				"Tone mapping " << getToneMapping() << "\n" <<
				"Geometric visibility test " << getBoolParameter(geometricVisibilityTest) << "\n" <<
				"Global seam leveling " << getBoolParameter(globalSeamLeveling) << "\n" <<
				"Local seam leveling " << getBoolParameter(localSeamLeveling) << "\n" <<
				"Hole filling " << getBoolParameter(holeFilling) << "\n" <<
				"Keep unseen faces " << getBoolParameter(keepUnseenFaces) << "\n";
			return s.str();
		}
	};
}

class HelperTexRecon
{
public:
	HelperTexRecon() {};
	~HelperTexRecon() {};

	//Run TexRecon
	static bool executeTexRecon(const std::string& inputCamerasFile, const std::string& inputMesh, const std::string& outputMesh, const TexRecon::Options& options);
private:
	//Create the .cameras file from a nvm/sfm file.
	static bool createCamerasFile(const std::string& inputCamerasFile, const std::string& outputCamerasFile);
};


