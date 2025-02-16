#pragma once

#ifdef WIN32
#include "wx/msw/winundef.h"
#endif

#include <wx\app.h>

class App : public wxApp 
{
public:
	virtual bool OnInit();
private:
	wxFrame* mainFrame;
};

DECLARE_APP(App)