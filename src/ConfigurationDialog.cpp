#include "ConfigurationDialog.h"

#include <fstream>
#include <sstream>

#include <wx/sizer.h>
#include <wx/statbox.h>
#include <wx/stattext.h>
#include <wx/button.h>
#include <wx/choice.h>
#include <wx/checkbox.h>
#include <wx/spinctrl.h>
#include <wx/log.h>
#include <wx/stdpaths.h>

#include "HelperTexRecon.h"
#include "Utils.h"
#include "json.hpp"

wxBEGIN_EVENT_TABLE(ConfigurationDialog, wxDialog)
EVT_BUTTON(wxID_OK, ConfigurationDialog::OnOK)
EVT_BUTTON(idBtDefaultConfigDialog, ConfigurationDialog::OnBtDefault)
wxEND_EVENT_TABLE()

bool ConfigurationDialog::isFirstInstance = true;
//COLMAP
int ConfigurationDialog::sparseQuality = 2;
int ConfigurationDialog::denseQuality = 2;
bool ConfigurationDialog::useGPU = false;
//TexRecon
int ConfigurationDialog::dataTerm = 1;
int ConfigurationDialog::outlierRemoval = 0;
int ConfigurationDialog::toneMapping = 0;
bool ConfigurationDialog::geometricVisibilityTest = true;
bool ConfigurationDialog::globalSeamLeveling = false;
bool ConfigurationDialog::localSeamLeveling = true;
bool ConfigurationDialog::holeFilling = true;
bool ConfigurationDialog::keepUnseenFaces = false;

ConfigurationDialog::ConfigurationDialog(wxWindow * parent, wxWindowID id, const wxString & title, const wxPoint & pos, const wxSize & size, long style) : wxDialog(parent, id, title, pos, size, style)
{
	if (isFirstInstance)
	{
		loadDefaultConfig();
		isFirstInstance = false;
	}
	this->SetSizeHints(wxDefaultSize, wxDefaultSize);

	wxBoxSizer* bSizer = new wxBoxSizer(wxVERTICAL);

	wxBoxSizer* bSizerMesh = new wxBoxSizer(wxHORIZONTAL);

	//COLMAP
	wxStaticBoxSizer* sbSizerCOLMAP = new wxStaticBoxSizer(new wxStaticBox(this, wxID_ANY, "COLMAP"), wxVERTICAL);

	wxFlexGridSizer* fgSizerCOLMAP = new wxFlexGridSizer(5, 2, 0, 0);
	fgSizerCOLMAP->SetFlexibleDirection(wxBOTH);
	fgSizerCOLMAP->SetNonFlexibleGrowMode(wxFLEX_GROWMODE_SPECIFIED);

	//Sparse quality
	fgSizerCOLMAP->Add(new wxStaticText(sbSizerCOLMAP->GetStaticBox(), wxID_ANY, "Sparse quality"), 0, wxALL, 5);
	wxArrayString choicesQuality;
	choicesQuality.Add("Low"); choicesQuality.Add("Medium"); choicesQuality.Add("High"); choicesQuality.Add("Extreme");
	choiceSparseQuality = new wxChoice(sbSizerCOLMAP->GetStaticBox(), wxID_ANY, wxDefaultPosition, wxDefaultSize, choicesQuality);
	choiceSparseQuality->SetSelection(sparseQuality);
	fgSizerCOLMAP->Add(choiceSparseQuality, 0, wxALL, 5);
	//------

	//Dense quality
	fgSizerCOLMAP->Add(new wxStaticText(sbSizerCOLMAP->GetStaticBox(), wxID_ANY, "Dense quality"), 0, wxALL, 5);
	choiceDenseQuality = new wxChoice(sbSizerCOLMAP->GetStaticBox(), wxID_ANY, wxDefaultPosition, wxDefaultSize, choicesQuality);
	choiceDenseQuality->SetSelection(denseQuality);
	fgSizerCOLMAP->Add(choiceDenseQuality, 0, wxALL, 5);
	//------

	//Use GPU
	fgSizerCOLMAP->Add(new wxStaticText(sbSizerCOLMAP->GetStaticBox(), wxID_ANY, "Use GPU"), 0, wxALL, 5);
	ckBUseGPU = new wxCheckBox(sbSizerCOLMAP->GetStaticBox(), wxID_ANY, wxEmptyString);
	ckBUseGPU->SetValue(useGPU);
	fgSizerCOLMAP->Add(ckBUseGPU, 0, wxALL, 5);
	//------

	sbSizerCOLMAP->Add(fgSizerCOLMAP, 1, wxEXPAND, 5);

	bSizerMesh->Add(sbSizerCOLMAP, 0, wxEXPAND, 5);

	wxBoxSizer* bSizerTexture = new wxBoxSizer(wxHORIZONTAL);

	//TexRecon
	wxStaticBoxSizer* sbSizerTexRecon = new wxStaticBoxSizer(new wxStaticBox(this, wxID_ANY, "TexRecon"), wxVERTICAL);

	wxFlexGridSizer* fgSizerTexRecon = new wxFlexGridSizer(9, 2, 0, 0);
	fgSizerTexRecon->SetFlexibleDirection(wxBOTH);
	fgSizerTexRecon->SetNonFlexibleGrowMode(wxFLEX_GROWMODE_SPECIFIED);


	fgSizerTexRecon->Add(new wxStaticText(sbSizerTexRecon->GetStaticBox(), wxID_ANY, "Data Term"), 0, wxALL, 5);
	wxArrayString choicesDataTerm;
	choicesDataTerm.Add("Area"); choicesDataTerm.Add("Gmi");
	choiceDataTerm = new wxChoice(sbSizerTexRecon->GetStaticBox(), wxID_ANY, wxDefaultPosition, wxDefaultSize, choicesDataTerm);
	choiceDataTerm->SetSelection(dataTerm);
	fgSizerTexRecon->Add(choiceDataTerm, 0, wxALL, 5);

	fgSizerTexRecon->Add(new wxStaticText(sbSizerTexRecon->GetStaticBox(), wxID_ANY, "Outlier removal"), 0, wxALL, 5);
	wxArrayString choicesOutlierRemoval;
	choicesOutlierRemoval.Add("None"); choicesOutlierRemoval.Add("Gauss damping"); choicesOutlierRemoval.Add("Gauss clamping");
	choiceOutlierRemoval = new wxChoice(sbSizerTexRecon->GetStaticBox(), wxID_ANY, wxDefaultPosition, wxDefaultSize, choicesOutlierRemoval);
	choiceOutlierRemoval->SetSelection(outlierRemoval);
	fgSizerTexRecon->Add(choiceOutlierRemoval, 0, wxALL, 5);

	fgSizerTexRecon->Add(new wxStaticText(sbSizerTexRecon->GetStaticBox(), wxID_ANY, "Tone mapping"), 0, wxALL, 5);
	wxArrayString choicesToneMapping;
	choicesToneMapping.Add("None"); choicesToneMapping.Add("Gamma");
	choiceToneMapping = new wxChoice(sbSizerTexRecon->GetStaticBox(), wxID_ANY, wxDefaultPosition, wxDefaultSize, choicesToneMapping);
	choiceToneMapping->SetSelection(toneMapping);
	fgSizerTexRecon->Add(choiceToneMapping, 0, wxALL, 5);

	fgSizerTexRecon->Add(new wxStaticText(sbSizerTexRecon->GetStaticBox(), wxID_ANY, "Geometric visibility test"), 0, wxALL, 5);
	ckBGeometricVisibilityTest = new wxCheckBox(sbSizerTexRecon->GetStaticBox(), wxID_ANY, wxEmptyString);
	ckBGeometricVisibilityTest->SetValue(geometricVisibilityTest);
	fgSizerTexRecon->Add(ckBGeometricVisibilityTest, 0, wxALL, 5);

	fgSizerTexRecon->Add(new wxStaticText(sbSizerTexRecon->GetStaticBox(), wxID_ANY, "Global seam leveling"), 0, wxALL, 5);
	ckBGlobalSeamLeveling = new wxCheckBox(sbSizerTexRecon->GetStaticBox(), wxID_ANY, wxEmptyString);
	ckBGlobalSeamLeveling->SetValue(globalSeamLeveling);
	fgSizerTexRecon->Add(ckBGlobalSeamLeveling, 0, wxALL, 5);

	fgSizerTexRecon->Add(new wxStaticText(sbSizerTexRecon->GetStaticBox(), wxID_ANY, "Local seam leveling"), 0, wxALL, 5);
	ckBLocalSeamLeveling = new wxCheckBox(sbSizerTexRecon->GetStaticBox(), wxID_ANY, wxEmptyString);
	ckBLocalSeamLeveling->SetValue(localSeamLeveling);
	fgSizerTexRecon->Add(ckBLocalSeamLeveling, 0, wxALL, 5);

	fgSizerTexRecon->Add(new wxStaticText(sbSizerTexRecon->GetStaticBox(), wxID_ANY, "Hole filling"), 0, wxALL, 5);
	ckBHoleFilling = new wxCheckBox(sbSizerTexRecon->GetStaticBox(), wxID_ANY, wxEmptyString);
	ckBHoleFilling->SetValue(holeFilling);
	fgSizerTexRecon->Add(ckBHoleFilling, 0, wxALL, 5);

	fgSizerTexRecon->Add(new wxStaticText(sbSizerTexRecon->GetStaticBox(), wxID_ANY, "Keep unseen faces"), 0, wxALL, 5);
	ckBKeepUnseenFaces = new wxCheckBox(sbSizerTexRecon->GetStaticBox(), wxID_ANY, wxEmptyString);
	ckBKeepUnseenFaces->SetValue(keepUnseenFaces);
	fgSizerTexRecon->Add(ckBKeepUnseenFaces, 0, wxALL, 5);

	sbSizerTexRecon->Add(fgSizerTexRecon, 1, wxEXPAND, 5);


	bSizerTexture->Add(sbSizerTexRecon, 0, wxEXPAND, 5);

	//Add mesh and texture box sizers
	bSizer->Add(bSizerMesh, 0, wxEXPAND, 5);
	bSizer->Add(bSizerTexture, 0, wxEXPAND, 5);

	wxBoxSizer* bSizerBts = new wxBoxSizer(wxHORIZONTAL);

	bSizerBts->Add(new wxButton(this, idBtDefaultConfigDialog, "Default"), 0, wxALL, 5);

	bSizerBts->Add(new wxButton(this, wxID_OK, "OK"), 0, wxALL, 5);

	bSizerBts->Add(new wxButton(this, wxID_CANCEL, "Cancel"), 0, wxALL, 5);

	bSizer->Add(bSizerBts, 0, wxALIGN_RIGHT, 5);
	this->SetSizer(bSizer);
	this->Layout();
	this->Fit();
	this->Centre(wxBOTH);
}

ConfigurationDialog::~ConfigurationDialog()
{
}

void ConfigurationDialog::loadDefaultConfig()
{
	nlohmann::json jsonFile;
	try
	{
		std::ifstream parametersFile(Utils::getExecutionPath() + "/parameters.json");
		if (!parametersFile.is_open())
		{
			wxLogError("Falha ao carregar o arquivos com os parâmetros padrões.");
			return;
		}
		jsonFile = nlohmann::json::parse(parametersFile);
	}
	catch (const std::exception&)
	{
		wxLogError("Falha ao carregar o arquivos com os parâmetros padrões.");
		return;
	}
	sparseQuality = jsonFile["COLMAP"]["sparseQuality"];
	denseQuality =	jsonFile["COLMAP"]["denseQuality"];
	useGPU =		jsonFile["COLMAP"]["useGPU"];

	dataTerm =					jsonFile["TexRecon"]["dataTerm"];
	outlierRemoval =			jsonFile["TexRecon"]["outlierRemoval"];
	toneMapping =				jsonFile["TexRecon"]["toneMapping"];
	geometricVisibilityTest =	jsonFile["TexRecon"]["geometricVisibilityTest"];
	globalSeamLeveling =		jsonFile["TexRecon"]["globalSeamLeveling"];
	localSeamLeveling =			jsonFile["TexRecon"]["localSeamLeveling"];
	holeFilling =				jsonFile["TexRecon"]["holeFilling"];
	keepUnseenFaces =			jsonFile["TexRecon"]["keepUnseenFaces"];
}

std::string ConfigurationDialog::getParameters()
{
	std::stringstream parameters;
	parameters << "------------------------------------------------------\n" <<
		"COLMAP\n" <<
		"Sparse quality " << getSparseQuality() << "\n" <<
		"Dense quality " << getDenseQuality() << "\n" <<
		"Use GPU " << getUseGPU() << "\n" <<
		"------------------------------------------------------\n" <<
		"TexRecon\n" <<
		getTexReconOptions().print() <<
		"------------------------------------------------------\n";
	return parameters.str();
}

std::string ConfigurationDialog::getSparseQuality()
{
	switch (sparseQuality)
	{
	case 0:
		return "low";
	case 1:
		return "medium";
	case 2:
		return "high";
	case 3:
		return "extreme";
	default:
		return "high";
	}
}

std::string ConfigurationDialog::getDenseQuality()
{
	switch (denseQuality)
	{
	case 0:
		return "low";
	case 1:
		return "medium";
	case 2:
		return "high";
	case 3:
		return "extreme";
	default:
		return "high";
	}
}

std::string ConfigurationDialog::getUseGPU()
{
	if (useGPU)
	{
		return "1";
	}
	return "0";
}


TexRecon::Options ConfigurationDialog::getTexReconOptions()
{
	return TexRecon::Options(dataTerm, outlierRemoval, toneMapping, geometricVisibilityTest, globalSeamLeveling, localSeamLeveling, holeFilling, keepUnseenFaces);
}

void ConfigurationDialog::SetQuality(int quality)
{
	sparseQuality = quality;
	denseQuality = quality;
}

void ConfigurationDialog::OnOK(wxCommandEvent & WXUNUSED)
{
	//COLMAP
	sparseQuality = choiceSparseQuality->GetSelection();
	denseQuality = choiceDenseQuality->GetSelection();
	useGPU = ckBUseGPU->IsChecked();
	//TexRecon
	dataTerm = choiceDataTerm->GetSelection();
	outlierRemoval = choiceOutlierRemoval->GetSelection();
	geometricVisibilityTest = ckBGeometricVisibilityTest->IsChecked();
	globalSeamLeveling = ckBGlobalSeamLeveling->IsChecked();
	localSeamLeveling = ckBLocalSeamLeveling->IsChecked();
	holeFilling = ckBHoleFilling->IsChecked();
	keepUnseenFaces = ckBKeepUnseenFaces->IsChecked();
	EndModal(wxID_OK);
}

void ConfigurationDialog::OnBtDefault(wxCommandEvent & WXUNUSED)
{
	loadDefaultConfig();
	//COLMAP
	choiceSparseQuality->SetSelection(sparseQuality);
	choiceDenseQuality->SetSelection(denseQuality);
	ckBUseGPU->SetValue(useGPU);
	//TexRecon
	choiceDataTerm->SetSelection(dataTerm);
	choiceOutlierRemoval->SetSelection(outlierRemoval);
	ckBGeometricVisibilityTest->SetValue(geometricVisibilityTest);
	ckBGlobalSeamLeveling->SetValue(globalSeamLeveling);
	ckBLocalSeamLeveling->SetValue(localSeamLeveling);
	ckBHoleFilling->SetValue(holeFilling);
	ckBKeepUnseenFaces->SetValue(keepUnseenFaces);
}
