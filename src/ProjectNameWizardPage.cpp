#include "ProjectNameWizardPage.h"

#include <wx/sizer.h>
#include <wx/stattext.h>
#include <wx/textctrl.h>
#include <wx/filepicker.h>
#include <wx/stdpaths.h>

ProjectNameWizardPage::ProjectNameWizardPage(wxWizard * parent, wxWizardPage * prev, wxWizardPage * next, const wxBitmap & bitmap) :
	wxWizardPageSimple(parent, prev, next, bitmap)
{
	auto bSizer = new wxBoxSizer(wxVERTICAL);

	bSizer->Add(new wxStaticText(this, wxID_ANY, "Selecione o nome do projeto e onde ele será criado."));

	bSizer->AddSpacer(15);

	auto fgSizer = new wxFlexGridSizer(0, 2, wxSize(10, 10));
	fgSizer->AddGrowableCol(1);
	fgSizer->SetFlexibleDirection(wxBOTH);
	fgSizer->SetNonFlexibleGrowMode(wxFLEX_GROWMODE_SPECIFIED);

	fgSizer->Add(new wxStaticText(this, wxID_ANY, "Nome"));

	projectName = new wxTextCtrl(this, wxID_ANY);

	fgSizer->Add(projectName, 0, wxEXPAND, 5);

	fgSizer->Add(new wxStaticText(this, wxID_ANY, "Criar em"));

	wxStandardPaths stdPaths = wxStandardPaths::Get();
	const auto projectPath = stdPaths.GetDocumentsDir() + "\\" + "SAEScan3D";
	if (!wxDirExists(projectPath))
	{
		wxMkdir(projectPath);
	}
	projectDir = new wxDirPickerCtrl(this, wxID_ANY, projectPath);

	fgSizer->Add(projectDir, 0, wxEXPAND, 5);

	bSizer->Add(fgSizer, 0, wxEXPAND, 5);

	nameWarning = new wxStaticText(this, wxID_ANY, "");
	nameWarning->SetForegroundColour(wxColour(255, 0, 0));

	fgSizer->Add(nameWarning);

	this->SetSizer(bSizer);

	projectName->Connect(wxEVT_COMMAND_TEXT_UPDATED, wxCommandEventHandler(ProjectNameWizardPage::OnTextCtrl), nullptr, this);
	projectDir->Connect(wxEVT_DIRPICKER_CHANGED, wxCommandEventHandler(ProjectNameWizardPage::OnDirPickerCtrl), nullptr, this);
	this->Connect(wxEVT_WIZARD_PAGE_SHOWN, wxCommandEventHandler(ProjectNameWizardPage::OnDirPickerCtrl), nullptr, this);
	this->Layout();
}

std::string ProjectNameWizardPage::GetProjectPath()
{
	return std::string(projectDir->GetPath() + "\\" + projectName->GetValue());
}

void ProjectNameWizardPage::OnTextCtrl(wxCommandEvent& event)
{
	CheckProjectName();
}

void ProjectNameWizardPage::OnDirPickerCtrl(wxCommandEvent& event)
{
	CheckProjectName();
}

void ProjectNameWizardPage::CheckProjectName()
{
	auto foward = this->FindWindowById(wxID_FORWARD);
	if (foward)
	{
		foward->Disable();
	}
	if (projectDir->GetPath() == "" || projectName->GetValue() == "")
	{
		return;
	}
	std::string badSymbols = "\\/:*?\"<>|";
	for (auto cha : badSymbols)
	{
		if (projectName->GetValue().find(cha) != std::string::npos)
		{
			nameWarning->SetLabel("O nome não pode conter os caracteres \\ / : * ? \" < > |");
			return;
		}
	}
	const auto projectPath = projectDir->GetPath() + "\\" + projectName->GetValue();
	if (wxDirExists(projectPath))
	{
		nameWarning->SetLabel("Nome já utilizado");
	}
	else
	{
		nameWarning->SetLabel("");
		if (foward)
		{
			foward->Enable();
		}
	}
}
