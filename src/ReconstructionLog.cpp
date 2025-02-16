#include "ReconstructionLog.h"

#include <sstream>

#include "ConfigurationDialog.h"

ReconstructionLog::ReconstructionLog(std::string pathToLogFile)
{
	logFile = std::ofstream(pathToLogFile, std::ofstream::out | std::ofstream::app);
	write("Started log file", true);
	logFile << "Parameters:\n";
	logFile << ConfigurationDialog::getParameters();
	initialTimer = std::clock();
}

ReconstructionLog::~ReconstructionLog()
{
	if (logFile.is_open())
	{
		logFile << "Total elapsed time: " << formatTime(initialTimer, std::clock());
		logFile.close();
	}
}

void ReconstructionLog::write(std::string var, bool addTime, bool computeTime)
{
	if (!logFile.is_open())
	{
		return;
	}
	if (addTime)
	{
		logFile << "[" << getCurrentDateTime() << "] ";
	}
	logFile << var;
	if (computeTime)
	{
		// start timer
		if (timer == -1)
		{
			timer = std::clock();
		}
		else
		{
			logFile << " elapsed time: " << formatTime(timer, std::clock());
			timer = -1;
		}
	}
	logFile << "\n";
}

void ReconstructionLog::addSeparator()
{
	logFile << "------------------------------------------------------\n";
}

std::string ReconstructionLog::getCurrentDateTime()
{
	time_t now = time(0);
	struct tm tstruct;
	char buf[80];
	tstruct = *localtime(&now);
	strftime(buf, sizeof(buf), "%Y-%m-%d %X", &tstruct);
	return buf;
}

std::string ReconstructionLog::addZerosToTheLeft(int amount, int value)
{
	if (value < amount && amount != 1)
	{
		return "0" + addZerosToTheLeft(amount / 10, value);
	}
	return "";
}

std::string ReconstructionLog::formatTime(std::clock_t startTime, std::clock_t endTime)
{
	std::clock_t time = endTime - startTime;
	int seconds = (int)(time / 1000) % 60;
	int milisseconds = time - (seconds * 1000);
	int minutes = (int)((time / (1000 * 60)) % 60);
	int hours = (int)((time / (1000 * 60 * 60)) % 24);
	std::stringstream result;
	result << addZerosToTheLeft(10, hours) << hours << ":" <<
		addZerosToTheLeft(10, minutes) << minutes << ":" <<
		addZerosToTheLeft(10, seconds) << seconds << "." <<
		addZerosToTheLeft(1000, milisseconds) << milisseconds;
	return result.str();
}
