#include "Camera.h"

#include <sstream>

#include "ImageIO.h"
#include "Utils.h"

Camera::Camera()
{
}

Camera::Camera(const std::string & filePath, const float focalDistance[2], const float principalPoint[2],
	const unsigned int width, const unsigned int height, const Eigen::Matrix4d matrixRt, const bool is360) :
	filePath(filePath), focalDistance{ focalDistance[0], focalDistance[1] }, principalPoint{ principalPoint[0], principalPoint[1] },
	width(width), height(height)
{
	setMatrixRt(matrixRt);
}

Camera::~Camera()
{
}

void Camera::setMatrixRt(Eigen::Matrix4d matrixRt)
{
	this->matrixRt = matrixRt;
}

Eigen::Matrix4d Camera::getMatrixRt() const
{
	return matrixRt;
}