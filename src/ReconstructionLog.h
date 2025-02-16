#pragma once
#include <fstream>
#include <ctime>


class ReconstructionLog
{
public:
	ReconstructionLog(std::string pathToLogFile);
	~ReconstructionLog();

	// var will be written in the log file, if addTime is true the dataTime will be added in the txt line
	// if computeTime is true, the timer will be started, if the time is already running, it will be stopped and the time added int the txt line
	void write(std::string var, bool addTime = false, bool computeTime = false);
	void addSeparator();

	// Get current date/time, format is YYYY-MM-DD.HH:mm:ss
	static std::string getCurrentDateTime();
	static std::string addZerosToTheLeft(int amount, int value);
	static std::string formatTime(std::clock_t startTime, std::clock_t endTime);

private:
	std::ofstream logFile;
	std::clock_t timer = -1;
	std::clock_t initialTimer = -1;
};