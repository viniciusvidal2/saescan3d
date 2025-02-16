#pragma once
#include <wx/panel.h>
#include <wx/bitmap.h>

class ProjectPanel : public wxPanel
{
	wxBitmap image;
	wxString versionText;

public:
	ProjectPanel(wxFrame* parent);

private:
	void OnBtCreateProject(wxCommandEvent & event);
	void paintEvent(wxPaintEvent & evt);
	void paintNow();

	void render(wxDC& dc);

	DECLARE_EVENT_TABLE()
};
