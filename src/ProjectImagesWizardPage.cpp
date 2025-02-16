#include "ProjectImagesWizardPage.h"

#include <wx/sizer.h>
#include <wx/stattext.h>
#include <wx/listctrl.h>
#include <wx/filepicker.h>
#include <wx/checkbox.h>
#include <wx/dir.h>
#include <wx/msgdlg.h>

#include "Utils.h"

ProjectImagesWizardPage::ProjectImagesWizardPage(wxWizard * parent, wxWizardPage * prev, wxWizardPage * next, const wxBitmap & bitmap) :
	wxWizardPageSimple(parent, prev, next, bitmap)
{
	auto bSizer = new wxBoxSizer(wxVERTICAL);

	bSizer->Add(new wxStaticText(this, wxID_ANY, "Selecione as imagens a serem utilizadas."));

	bSizer->AddSpacer(15);

	auto fgSizer = new wxFlexGridSizer(0, 6, wxSize(10, 10));
	fgSizer->AddGrowableCol(0);
	fgSizer->SetFlexibleDirection(wxBOTH);
	fgSizer->SetNonFlexibleGrowMode(wxFLEX_GROWMODE_SPECIFIED);

	selectedImagesStatText = new wxStaticText(this, wxID_ANY, "0 imagens selecionadas");
	fgSizer->Add(selectedImagesStatText);

	auto btAddImages = new wxButton(this, wxID_ANY, "Adicionar imagens...");
	auto btAddDirectory = new wxButton(this, wxID_ANY, "Adicionar diretório...");
	auto btRemoveSelected = new wxButton(this, wxID_ANY, "Remover selecionadas");
	auto btClearList = new wxButton(this, wxID_ANY, "Remover todas");
	fgSizer->Add(btAddImages);
	fgSizer->Add(btAddDirectory);
	fgSizer->Add(btRemoveSelected);
	fgSizer->Add(btClearList);
	
	bSizer->Add(fgSizer, 0, wxEXPAND, 5);

	auto fgSizerText = new wxFlexGridSizer(0, 0, wxSize(10, 10));
	fgSizerText->AddGrowableRow(0);
	fgSizerText->AddGrowableCol(0);
	fgSizerText->SetFlexibleDirection(wxBOTH);
	fgSizerText->SetNonFlexibleGrowMode(wxFLEX_GROWMODE_SPECIFIED);

	selectedImagesList = new wxListCtrl(this, wxID_ANY, wxDefaultPosition, wxDefaultSize, wxLC_LIST | wxLC_SORT_ASCENDING);

	fgSizerText->Add(selectedImagesList, 0, wxEXPAND, 10);

	bSizer->Add(fgSizerText, 1, wxEXPAND, 5);

	ckMoveImages = new wxCheckBox(this, wxID_ANY, "Mover as imagens para o diretório do projeto (caso contrário elas serão copiadas)");

	bSizer->Add(ckMoveImages, 0, wxALIGN_LEFT, 5);

	this->SetSizer(bSizer);

	btAddImages->Connect(wxEVT_COMMAND_BUTTON_CLICKED, wxCommandEventHandler(ProjectImagesWizardPage::OnBtAddImages), nullptr, this);
	btAddDirectory->Connect(wxEVT_COMMAND_BUTTON_CLICKED, wxCommandEventHandler(ProjectImagesWizardPage::OnBtAddDirectory), nullptr, this);
	btRemoveSelected->Connect(wxEVT_COMMAND_BUTTON_CLICKED, wxCommandEventHandler(ProjectImagesWizardPage::OnBtRemoveSelected), nullptr, this);
	btClearList->Connect(wxEVT_COMMAND_BUTTON_CLICKED, wxCommandEventHandler(ProjectImagesWizardPage::OnBtClearList), nullptr, this);
	this->Connect(wxEVT_WIZARD_PAGE_SHOWN, wxCommandEventHandler(ProjectImagesWizardPage::OnPageShown), nullptr, this);
	this->Layout();
}

wxArrayString ProjectImagesWizardPage::GetImagesPath()
{
	wxArrayString paths;
	long item = selectedImagesList->GetNextItem(-1);
	while (item != -1)
	{
		paths.Add(selectedImagesList->GetItemText(item));
		item = selectedImagesList->GetNextItem(item);
	}
	return paths;
}

bool ProjectImagesWizardPage::GetMoveImagesToProjectDir()
{
	return ckMoveImages->IsChecked();
}

void ProjectImagesWizardPage::OnBtAddImages(wxCommandEvent & event)
{
	wxFileDialog imagesDialog(this, "Selecione as imagens", "", "",
		"JPG and JPEG files (*.jpg;*.jpeg)|*.jpg;*.jpeg", wxFD_FILE_MUST_EXIST |wxFD_MULTIPLE);
	if (imagesDialog.ShowModal() == wxID_OK)
	{
		wxArrayString paths;
		imagesDialog.GetPaths(paths);
		for (const auto& path : paths)
		{
			selectedImagesList->InsertItem(selectedImagesList->GetItemCount(), path);
		}
		updateSelectedImagesText();
	}
}

void ProjectImagesWizardPage::OnBtAddDirectory(wxCommandEvent & event)
{
	wxDirDialog dirDialog(this, "Selecione o diretório com as imagens", "", wxDD_DEFAULT_STYLE);
	if (dirDialog.ShowModal() == wxID_OK)
	{
		wxDir directory(dirDialog.GetPath());
		if (!directory.IsOpened())
		{
			wxMessageBox("Não foi possível abrir o diretório", "Error", wxICON_ERROR);
			return;
		}
		wxArrayString files;
		directory.GetAllFiles(dirDialog.GetPath(), &files, wxEmptyString, wxDIR_FILES);
		std::string extension;
		for (const auto & file : files)
		{
			extension = Utils::toUpper(Utils::getFileExtension(file.ToStdString()));
			if (extension == "JPG" || extension == "JPEG")
			{
				selectedImagesList->InsertItem(selectedImagesList->GetItemCount(), file);
			}
		}
		updateSelectedImagesText();
	}
}

void ProjectImagesWizardPage::OnBtRemoveSelected(wxCommandEvent & event)
{
	long item = -1;
	while (selectedImagesList->GetSelectedItemCount() !=0)
	{
		item = selectedImagesList->GetNextItem(item,
			wxLIST_NEXT_ALL,
			wxLIST_STATE_SELECTED);
		selectedImagesList->DeleteItem(item);
	}
	updateSelectedImagesText();
}

void ProjectImagesWizardPage::OnBtClearList(wxCommandEvent & event)
{
	selectedImagesList->ClearAll();
	updateSelectedImagesText();
}

void ProjectImagesWizardPage::OnPageShown(wxCommandEvent & event)
{
	updateSelectedImagesText();
}

void ProjectImagesWizardPage::updateSelectedImagesText()
{
	const auto numberOfSelectedImages = selectedImagesList->GetItemCount();
	selectedImagesStatText->SetLabel(std::to_string(numberOfSelectedImages) + " imagens selecionadas");
	auto foward = this->FindWindowById(wxID_FORWARD);
	if (foward)
	{
		if (numberOfSelectedImages > 3)
		{
			foward->Enable();
		}
		else
		{
			foward->Disable();
		}
	}
}
