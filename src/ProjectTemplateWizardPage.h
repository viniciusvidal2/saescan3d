#pragma once
#include <wx/wizard.h>

class wxChoice;
class wxCheckBox;

class ProjectTemplateWizardPage : public wxWizardPageSimple
{
public:
	ProjectTemplateWizardPage(wxWizard *parent, wxWizardPage *prev = nullptr, wxWizardPage *next = nullptr, const wxBitmap &bitmap = wxNullBitmap);
	~ProjectTemplateWizardPage() {};

	int GetProjectQuality();
	bool GetGenerateTexture();

private:
	wxChoice* chQuality;
	wxCheckBox* ckGenerateTexture;

	void OnChoiceQuality(wxCommandEvent& event);
	void OnBtQuality(wxCommandEvent& event);
};