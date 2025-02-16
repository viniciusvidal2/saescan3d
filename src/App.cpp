#include "App.h"

#include <wx/wx.h>
#include "ProjectPanel.h"

IMPLEMENT_APP(App)

bool App::OnInit()
{
	wxInitAllImageHandlers();
	mainFrame = new wxFrame(nullptr, wxID_ANY, "SAEScan 3D", wxDefaultPosition,
		wxSize(980, 570), wxMINIMIZE_BOX | wxSYSTEM_MENU | wxCAPTION | wxCLOSE_BOX | wxCLIP_CHILDREN);

	auto sizer = new wxBoxSizer(wxHORIZONTAL);
	auto projectPanel = new ProjectPanel(mainFrame);
	sizer->Add(projectPanel, 1, wxEXPAND);

	mainFrame->SetSizer(sizer);
	mainFrame->SetIcon(wxICON(ICON_AAA_SAESCAN3D));

	mainFrame->Show(true);
	this->SetTopWindow(mainFrame);
	return true;
}