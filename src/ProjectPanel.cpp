#include "ProjectPanel.h"

#include <fstream>
#include <string>

#include <wx/wx.h>
#include <wx/log.h>
#include <wx/progdlg.h>

#include "ProjectNameWizardPage.h"
#include "ProjectImagesWizardPage.h"
#include "ProjectTemplateWizardPage.h"
#include "Utils.h"
#include "Reconstruction.h"
#include "ProjectPanel.h"

BEGIN_EVENT_TABLE(ProjectPanel, wxPanel)
EVT_PAINT(ProjectPanel::paintEvent)
END_EVENT_TABLE()


ProjectPanel::ProjectPanel(wxFrame* parent) : wxPanel(parent)
{
	// load the file... ideally add a check to see if loading was successful
	image.LoadFile("BITMAP_PANEL", wxBITMAP_TYPE_BMP_RESOURCE);
	
	auto btCreateProject = new wxButton(this, wxID_ANY, "Criar projeto...", wxPoint(430, 430), wxSize(120, 50));
	btCreateProject->Bind(wxEVT_BUTTON, &ProjectPanel::OnBtCreateProject, this);

	versionText << "Versão 0.0.1 ";
	
	this->Layout();
	this->Fit();
	this->Centre(wxBOTH);
}

void ProjectPanel::OnBtCreateProject(wxCommandEvent & event)
{
	wxWizard wizard(nullptr, wxID_ANY, "SAEScan3D");
	wizard.SetPageSize(wxSize(700, 400));
	std::vector<wxWizardPageSimple*> wizardPages;
	wizardPages.emplace_back(new ProjectNameWizardPage(&wizard));
	wizardPages.emplace_back(new ProjectImagesWizardPage(&wizard));
	wizardPages.emplace_back(new ProjectTemplateWizardPage(&wizard));
	for (size_t i = 1; i < wizardPages.size(); i++)
	{
		wizardPages[i]->SetPrev(wizardPages[i - 1]);
		wizardPages[i - 1]->SetNext(wizardPages[i]);
	}
	if (!wizard.RunWizard(wizardPages[0]))
	{
		return;
	}
	//Name
	const auto namePage = dynamic_cast<ProjectNameWizardPage*>(wizardPages[0]);
	const auto projectFolder = namePage->GetProjectPath();
	if (!Utils::CreateDir(projectFolder))
	{
		wxLogError("Não foi possível criar o diretório do projeto");
		return;
	}
	//Write the project file
	std::ofstream projectFile(projectFolder + "\\" + Utils::GetLastDirName(projectFolder) + ".project");
	std::string line;
	if (projectFile.is_open())
	{
		projectFile << "is360=0\n";
		projectFile.close();
	}
	else
	{
		wxLogError("Não foi possível criar o arquivo do projeto");
		return;
	}
	//Images
	const auto imagesPage = dynamic_cast<ProjectImagesWizardPage*>(wizardPages[1]);
	const auto imagesPaths = imagesPage->GetImagesPath();
	const auto imagesFolder = projectFolder + "\\images";
	if (!Utils::CreateDir(imagesFolder))
	{
		wxLogError("Não foi possível criar o diretório das imagens");
		return;
	}
	wxProgressDialog* progressDialog;
	if (imagesPage->GetMoveImagesToProjectDir())
	{
		progressDialog = new wxProgressDialog("Movendo imagens", "Movendo imagens", imagesPaths.size());
	}
	else
	{
		progressDialog = new wxProgressDialog("Copiando imagens", "Copiando imagens", imagesPaths.size());
	}
	unsigned int imageCount = 0;
	for (const auto& path : imagesPaths)
	{
		const auto newPath = imagesFolder + "\\" + Utils::getFileName(path.ToStdString());
		if (!wxCopyFile(path, newPath))
		{
			wxLogError("Erro copiando o arquivo " + path);
		}
		else if (imagesPage->GetMoveImagesToProjectDir())
		{
			if (!wxRemoveFile(path))
			{
				wxLogError("Erro removendo o arquivo " + path);
			}
		}
		progressDialog->Update(imageCount);
		imageCount++;
	}
	delete progressDialog;
	//Project options
	const auto generateTexture = dynamic_cast<ProjectTemplateWizardPage*>(wizardPages[2])->GetGenerateTexture();
	//Start processing
	if (Reconstruction::Reconstruct(projectFolder, generateTexture))
	{
		wxLogInfo("Projecto criado com sucesso!");
	}
}

/*
 * Called by the system of by wxWidgets when the panel needs
 * to be redrawn. You can also trigger this call by
 * calling Refresh()/Update().
 */
void ProjectPanel::paintEvent(wxPaintEvent & evt)
{
	// depending on your system you may need to look at double-buffered dcs
	wxPaintDC dc(this);
	render(dc);
}

/*
 * Alternatively, you can use a clientDC to paint on the panel
 * at any time. Using this generally does not free you from
 * catching paint events, since it is possible that e.g. the window
 * manager throws away your drawing when the window comes to the
 * background, and expects you will redraw it when the window comes
 * back (by sending a paint event).
 */
void ProjectPanel::paintNow()
{
	// depending on your system you may need to look at double-buffered dcs
	wxClientDC dc(this);
	render(dc);
}

/*
 * Here we do the actual rendering. I put it in a separate
 * method so that it can work no matter what type of DC
 * (e.g. wxPaintDC or wxClientDC) is used.
 */
void ProjectPanel::render(wxDC&  dc)
{
	dc.DrawBitmap(image, 0, 0, false);
	dc.SetBackgroundMode(wxTRANSPARENT);
	dc.SetFont(wxFont(15, wxFONTFAMILY_DEFAULT, wxFONTSTYLE_NORMAL, wxFONTWEIGHT_BOLD, false, wxT("Arial")));
	dc.SetTextForeground(wxColour(255, 255, 255));
	//dc.DrawText(versionText, 567, 60);
}
