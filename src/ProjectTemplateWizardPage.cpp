#include "ProjectTemplateWizardPage.h"

#include <wx/sizer.h>
#include <wx/stattext.h>
#include <wx/choice.h>
#include <wx/checkbox.h>
#include <wx/bmpbuttn.h>

#include "ConfigurationDialog.h"

ProjectTemplateWizardPage::ProjectTemplateWizardPage(wxWizard * parent, wxWizardPage * prev, wxWizardPage * next, const wxBitmap & bitmap) :
	wxWizardPageSimple(parent, prev, next, bitmap)
{
	auto bSizer = new wxBoxSizer(wxVERTICAL);

	bSizer->Add(new wxStaticText(this, wxID_ANY, "Selecione a qualidade desejada."));

	bSizer->AddSpacer(15);

	auto fgSizer = new wxFlexGridSizer(0, 2, wxSize(10, 10));
	fgSizer->AddGrowableCol(1);
	fgSizer->SetFlexibleDirection(wxBOTH);
	fgSizer->SetNonFlexibleGrowMode(wxFLEX_GROWMODE_SPECIFIED);

	fgSizer->Add(new wxStaticText(this, wxID_ANY, "Qualidade"));

	wxArrayString typeQuality;
	typeQuality.Add("Baixa"); typeQuality.Add("Média"); typeQuality.Add("Alta"); typeQuality.Add("Extrema");
	chQuality = new wxChoice(this, wxID_ANY, wxDefaultPosition, wxDefaultSize, typeQuality);
	chQuality->SetSelection(1);
	fgSizer->Add(chQuality);

	fgSizer->Add(new wxStaticText(this, wxID_ANY, "Gerar textura"));

	ckGenerateTexture = new wxCheckBox(this, wxID_ANY, "");

	fgSizer->Add(ckGenerateTexture);

	fgSizer->Add(new wxStaticText(this, wxID_ANY, "Configurações avançadas"));

	auto btAdvancedQuality = new wxBitmapButton(this, wxID_ANY, wxICON(ICON_CONFIG));

	fgSizer->Add(btAdvancedQuality);
	
	bSizer->Add(fgSizer, 0, wxEXPAND, 5);

	this->SetSizer(bSizer);
	chQuality->Connect(wxEVT_CHOICE, wxCommandEventHandler(ProjectTemplateWizardPage::OnChoiceQuality), nullptr, this);
	btAdvancedQuality->Connect(wxEVT_COMMAND_BUTTON_CLICKED, wxCommandEventHandler(ProjectTemplateWizardPage::OnBtQuality), nullptr, this);
	this->Layout();
	// We need to create a ConfigurationDialog to load the default configurations
	ConfigurationDialog config(this);
	ConfigurationDialog::SetQuality(chQuality->GetSelection());
}

int ProjectTemplateWizardPage::GetProjectQuality()
{
	return chQuality->GetSelection();
}

bool ProjectTemplateWizardPage::GetGenerateTexture()
{
	return ckGenerateTexture->IsChecked();
}

void ProjectTemplateWizardPage::OnChoiceQuality(wxCommandEvent & event)
{
	ConfigurationDialog::SetQuality(chQuality->GetSelection());
}

void ProjectTemplateWizardPage::OnBtQuality(wxCommandEvent & event)
{
	ConfigurationDialog  configDialog(this);
	configDialog.ShowModal();
}
