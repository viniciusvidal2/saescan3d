#pragma once

#include <string>

class Utils
{
public:
	Utils();
	~Utils();

	static std::wstring s2ws(const std::string& s);

	static int startProcess(const std::string& path_with_command);
	static int startProcess(const std::string& path_with_command, const std::string& workingDirectory);
	//startProcess and ask for admin permission
	static int startProcess(const std::string& path_exec, const std::string& parameters, const std::string& workingDirectory);

	//True if the file exists, false otherwise
	static bool exists(const std::string& name);

	//Adjust the path to be used with external processes
	static std::string preparePath(std::string path);

	static std::string getExecutionPath();

	//Get file extesion without the dot
	static std::string getFileExtension(const std::string & filePath);

	static std::string getFileName(const std::string & filePath, bool withExtension = true);

	static std::string getPath(const std::string & filePath, bool returnWithLastSlash = true);

	static std::string toUpper(const std::string & str);

	static bool CreateDir(const std::string& dirName);

	static std::string GetLastDirName(const std::string& dirPath);

	// Delete a file, check if it exists first
	static bool RemoveFile(const std::string& path);
};