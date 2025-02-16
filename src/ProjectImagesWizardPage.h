#pragma once
#include <wx/wizard.h>

class wxStaticText;
class wxListCtrl;
class wxCheckBox;

class ProjectImagesWizardPage : public wxWizardPageSimple
{
public:
	ProjectImagesWizardPage(wxWizard *parent, wxWizardPage *prev = nullptr, wxWizardPage *next = nullptr, const wxBitmap &bitmap = wxNullBitmap);
	~ProjectImagesWizardPage() {};

	wxArrayString GetImagesPath();
	bool GetMoveImagesToProjectDir();

private:
	wxStaticText* selectedImagesStatText;
	wxListCtrl* selectedImagesList;
	wxCheckBox* ckMoveImages;
	
	void OnBtAddImages(wxCommandEvent& event);
	void OnBtAddDirectory(wxCommandEvent& event);
	void OnBtRemoveSelected(wxCommandEvent& event);
	void OnBtClearList(wxCommandEvent& event);
	void OnPageShown(wxCommandEvent& event);

	void updateSelectedImagesText();
};