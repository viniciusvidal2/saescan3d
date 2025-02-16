#include "Utils.h"

#include <vector>
#include <sstream>
//#include <Windows.h>

#include <wx/log.h>
#include <wx/image.h>
#include <wx/stdpaths.h>
#include <wx/msgdlg.h>
#include <wx/filedlg.h>


Utils::Utils()
{
}

Utils::~Utils()
{
}

std::wstring Utils::s2ws(const std::string & s)
{
	int len;
	int slength = (int)s.length() + 1;
	len = MultiByteToWideChar(CP_ACP, 0, s.c_str(), slength, 0, 0);
	wchar_t* buf = new wchar_t[len];
	MultiByteToWideChar(CP_ACP, 0, s.c_str(), slength, buf, len);
	std::wstring r(buf);
	delete[] buf;
	return r;
}

int Utils::startProcess(const std::string& path_with_command)
{
	std::wstring stemp = s2ws(path_with_command);
	LPWSTR path_command = const_cast<LPWSTR>(stemp.c_str());

	STARTUPINFO si;
	PROCESS_INFORMATION pi;

	ZeroMemory(&si, sizeof(si));
	si.cb = sizeof(si);
	ZeroMemory(&pi, sizeof(pi));

	// Start the child process. 
	if (!CreateProcess(NULL,   // No module name (use command line)
		path_command,        // Command line
		NULL,           // Process handle not inheritable
		NULL,           // Thread handle not inheritable
		FALSE,          // Set handle inheritance to FALSE
		0,              // No creation flags
		NULL,           // Use parent's environment block
		NULL,           // Use parent's starting directory 
		&si,            // Pointer to STARTUPINFO structure
		&pi)           // Pointer to PROCESS_INFORMATION structure
		)
	{
		wxLogError("CreateProcess failed (%d).\n", GetLastError());
		return 0;
	}

	// Wait until child process exits.
	WaitForSingleObject(pi.hProcess, INFINITE);

	// Close process and thread handles. 
	CloseHandle(pi.hProcess);
	CloseHandle(pi.hThread);
	return 1;
}

int Utils::startProcess(const std::string& path_with_command, const std::string& workingDirectory)
{
	std::wstring stemp = s2ws(path_with_command);
	LPWSTR path_command = const_cast<LPWSTR>(stemp.c_str());

	std::wstring stemp2 = s2ws(workingDirectory);
	LPCWSTR working_dir = stemp2.c_str();

	STARTUPINFO si;
	PROCESS_INFORMATION pi;

	ZeroMemory(&si, sizeof(si));
	si.cb = sizeof(si);
	ZeroMemory(&pi, sizeof(pi));

	// Start the child process. 
	if (!CreateProcess(NULL,   // No module name (use command line)
		path_command,        // Command line
		NULL,           // Process handle not inheritable
		NULL,           // Thread handle not inheritable
		FALSE,          // Set handle inheritance to FALSE
		0,              // No creation flags
		NULL,           // Use parent's environment block
		working_dir,           // Use parent's starting directory 
		&si,            // Pointer to STARTUPINFO structure
		&pi)           // Pointer to PROCESS_INFORMATION structure
		)
	{
		wxLogError("CreateProcess failed (%d).\n", GetLastError());
		return 0;
	}

	// Wait until child process exits.
	WaitForSingleObject(pi.hProcess, INFINITE);

	// Close process and thread handles. 
	CloseHandle(pi.hProcess);
	CloseHandle(pi.hThread);
	return 1;
}

int Utils::startProcess(const std::string& path_exec, const std::string& parameters, const std::string& workingDirectory)
{
	std::wstring stemp = s2ws(path_exec);
	LPWSTR path_exe = const_cast<LPWSTR>(stemp.c_str());

	std::wstring stemp2 = s2ws(workingDirectory);
	LPCWSTR working_dir = stemp2.c_str();

	std::wstring stemp3 = s2ws(parameters);
	LPCWSTR param = stemp3.c_str();

	SHELLEXECUTEINFO shExInfo = { 0 };
	shExInfo.cbSize = sizeof(shExInfo);
	shExInfo.fMask = SEE_MASK_NOCLOSEPROCESS;
	shExInfo.hwnd = 0;
	shExInfo.lpVerb = _T("runas");                // Operation to perform
	shExInfo.lpFile = path_exe;       // Application to start    
	shExInfo.lpParameters = param;                  // Additional parameters
	shExInfo.lpDirectory = working_dir;
	shExInfo.nShow = SW_SHOW;
	shExInfo.hInstApp = 0;

	if (ShellExecuteEx(&shExInfo))
	{
		WaitForSingleObject(shExInfo.hProcess, INFINITE);
		CloseHandle(shExInfo.hProcess);
	}
	else
	{
		return 0;
	}
	return 1;
}

bool Utils::exists(const std::string & name)
{
	return wxFileExists(name);
}

std::string Utils::preparePath(std::string path)
{
	std::replace(path.begin(), path.end(), '\\', '/');
	return "\"" + path + "\"";
}

std::string Utils::getExecutionPath()
{
	return Utils::getPath(wxStandardPaths::Get().GetExecutablePath().ToStdString(), false);
}

std::string Utils::getFileExtension(const std::string & filePath)
{
	if (filePath.find_last_of('.') != std::string::npos)
	{
		return filePath.substr(filePath.find_last_of('.') + 1, filePath.size());
	}
	return "";
}

std::string Utils::getFileName(const std::string & filePath, bool withExtension)
{
	std::string fileName = filePath;
	if (fileName.find_last_of('/') != std::string::npos)
	{
		fileName = fileName.substr(fileName.find_last_of('/') + 1, fileName.size());
	}
	else if (filePath.find_last_of('\\') != std::string::npos)
	{
		fileName = fileName.substr(fileName.find_last_of('\\') + 1, fileName.size());
	}
	if (fileName != "" && !withExtension)
	{
		return fileName.substr(0, fileName.find_last_of('.'));
	}
	return fileName;
}

std::string Utils::getPath(const std::string & filePath, bool returnWithLastSlash)
{
	if (filePath.find_last_of('/') != std::string::npos)
	{
		if (returnWithLastSlash)
		{
			return filePath.substr(0, filePath.find_last_of('/') + 1);
		}
		else
		{
			return filePath.substr(0, filePath.find_last_of('/'));
		}
	}
	else if (filePath.find_last_of('\\') != std::string::npos)
	{
		if (returnWithLastSlash)
		{
			return filePath.substr(0, filePath.find_last_of('\\') + 1);
		}
		else
		{
			return filePath.substr(0, filePath.find_last_of('\\'));
		}
	}
	return "";
}

std::string Utils::toUpper(const std::string & str)
{
	std::string copy = str;
	for (auto & c : copy)
	{
		c = toupper(c);
	}
	return copy;
}

bool Utils::CreateDir(const std::string & dirName)
{
	if (!wxMkdir(dirName))
	{
		wxLogError(wxString("Error creating the directory " + dirName));
		return 0;
	}
	return 1;
}

std::string Utils::GetLastDirName(const std::string & dirPath)
{
	if (dirPath.find_last_of('\\') != std::string::npos)
	{
		return dirPath.substr(dirPath.find_last_of('\\'));
	}
	return dirPath.substr(dirPath.find_last_of('/'));
}

bool Utils::RemoveFile(const std::string & path)
{
	if (exists(path))
	{
		return wxRemoveFile(path);
	}
	else
	{
		return false;
	}
}
