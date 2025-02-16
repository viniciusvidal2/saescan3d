#pragma once
#include <wx/dialog.h>

class wxChoice;
class wxCheckBox;
class wxSpinCtrlDouble;

namespace TexRecon
{
	struct Options;
}

class ConfigurationDialog : public wxDialog
{
public:
	ConfigurationDialog(wxWindow* parent, wxWindowID id = wxID_ANY, const wxString& title = "Configuration",
		const wxPoint& pos = wxDefaultPosition, const wxSize& size = wxSize(610, 580), long style = wxDEFAULT_DIALOG_STYLE);
	~ConfigurationDialog();

	static void loadDefaultConfig();
	static std::string getParameters();

	//COLMAP
	//0 - Low 1 - Medium 2 - High 3 - Extreme
	static std::string getSparseQuality();
	//0 - Low 1 - Medium 2 - High 3 - Extreme
	static std::string getDenseQuality();
	static std::string getUseGPU();

	//TexRecon
	static TexRecon::Options getTexReconOptions();

	static void SetQuality(int quality);

private:
	DECLARE_EVENT_TABLE()

	void OnOK(wxCommandEvent& WXUNUSED(event));
	void OnBtDefault(wxCommandEvent& WXUNUSED(event));

	//COLMAP
	wxChoice* choiceSparseQuality;
	wxChoice* choiceDenseQuality;
	wxCheckBox* ckBUseGPU;

	//TexRecon
	wxChoice* choiceDataTerm;
	wxChoice* choiceOutlierRemoval;
	wxChoice* choiceToneMapping;
	wxCheckBox* ckBGeometricVisibilityTest;
	wxCheckBox* ckBGlobalSeamLeveling;
	wxCheckBox* ckBLocalSeamLeveling;
	wxCheckBox* ckBHoleFilling;
	wxCheckBox* ckBKeepUnseenFaces;
	wxCheckBox* ckBForceTexReconTexture;

	//Used to load the default parameters
	static bool isFirstInstance;
	//COLMAP
	static int sparseQuality;
	static int denseQuality;
	static bool useGPU;
	//TexRecon
	static int dataTerm;
	static int outlierRemoval;
	static int toneMapping;
	static bool geometricVisibilityTest;
	static bool globalSeamLeveling;
	static bool localSeamLeveling;
	static bool holeFilling;
	static bool keepUnseenFaces;

};
enum EnumConfigDialog
{
	idBtDefaultConfigDialog
};