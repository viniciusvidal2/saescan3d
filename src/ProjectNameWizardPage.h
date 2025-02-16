#pragma once
#include <wx/wizard.h>

class wxStaticText;
class wxTextCtrl;
class wxDirPickerCtrl;

class ProjectNameWizardPage : public wxWizardPageSimple
{
public:
	ProjectNameWizardPage(wxWizard *parent, wxWizardPage *prev = nullptr, wxWizardPage *next = nullptr, const wxBitmap &bitmap = wxNullBitmap);
	~ProjectNameWizardPage() {};

	std::string GetProjectPath();

private:
	wxStaticText* nameWarning;
	wxTextCtrl* projectName;
	wxDirPickerCtrl* projectDir;

	void OnTextCtrl(wxCommandEvent& event);
	void OnDirPickerCtrl(wxCommandEvent& event);
	void CheckProjectName();
};