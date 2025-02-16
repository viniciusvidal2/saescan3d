#pragma once

#include <Eigen/Dense>

class Camera
{
private:
	// {focal_x, focal_y}
	float focalDistance[2];
	// {center_x, center_y}
	float principalPoint[2];
	unsigned int width;
	unsigned int height;
	Eigen::Matrix4d matrixRt;
public:
	Camera();
	Camera(const std::string& filePath, const float focalDistance[2], const float principalPoint[2], 
		const unsigned int width, const unsigned int height, const Eigen::Matrix4d matrixRt, const bool is360 = false);
	~Camera();

	std::string filePath = "";

	float getFocalX() const { return focalDistance[0]; };
	float getFocalY() const { return focalDistance[1]; };
	float getPrincipalPointX() const { return principalPoint[0]; };
	float getPrincipalPointY() const { return principalPoint[1]; };
	unsigned int getWidth() const { return width; };
	unsigned int getHeight() const { return height; };

	void setMatrixRt(Eigen::Matrix4d matrixRt);
	Eigen::Matrix4d getMatrixRt() const;
};