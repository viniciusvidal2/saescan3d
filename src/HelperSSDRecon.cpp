#include "HelperSSDRecon.h"

#include <fstream>

#include <wx/log.h>

#include "Utils.h"
#include "tinyply.h"

bool HelperSSDRecon::executeMeshing(std::string inputPath, std::string outputPath)
{
	if (!executeSSD(inputPath, outputPath))
	{
		return 0;
	}
	if (!executeSurfaceTrimmer(outputPath))
	{
		return 0;
	}
	fixBadPLY(outputPath);
	return 1;
}

bool HelperSSDRecon::executeSSD(std::string inputPath, std::string outputPath)
{
	std::string ssdParameters(Utils::preparePath(Utils::getExecutionPath() + "/SSDRecon/SSDRecon.exe") +
		" --in " + Utils::preparePath(inputPath) +
		" --out " + Utils::preparePath(outputPath) +
		" --depth 12" +
		" --samplesPerNode 12" +
		" --density"
	);
	if (!Utils::startProcess(ssdParameters))
	{
		wxLogError("Error with SSDRecon");
		return 0;
	}
	if (!Utils::exists(outputPath))
	{
		wxLogError("No mesh was created with SSDRecon");
		return 0;
	}
	return 1;
}

bool HelperSSDRecon::executeSurfaceTrimmer(std::string inputPath)
{
	std::string surfaceParameters(Utils::preparePath(Utils::getExecutionPath() + "/SSDRecon/SurfaceTrimmer.exe") +
		" --in " + Utils::preparePath(inputPath) +
		" --out " + Utils::preparePath(inputPath) +
		" --trim 5"
	);
	if (!Utils::startProcess(surfaceParameters))
	{
		wxLogError("Error with SurfaceTrimmer");
		return 0;
	}
	return 1;
}

std::vector<uint8_t> read_file_binary(const std::string & pathToFile)
{
	std::ifstream file(pathToFile, std::ios::binary);
	std::vector<uint8_t> fileBufferBytes;

	if (file.is_open())
	{
		file.seekg(0, std::ios::end);
		size_t sizeBytes = file.tellg();
		file.seekg(0, std::ios::beg);
		fileBufferBytes.resize(sizeBytes);
		if (file.read((char*)fileBufferBytes.data(), sizeBytes)) return fileBufferBytes;
	}
	else throw std::runtime_error("could not open binary ifstream to path " + pathToFile);
	return fileBufferBytes;
}

struct memory_buffer : public std::streambuf
{
	char * p_start{ nullptr };
	char * p_end{ nullptr };
	size_t size;

	memory_buffer(char const * first_elem, size_t size)
		: p_start(const_cast<char*>(first_elem)), p_end(p_start + size), size(size)
	{
		setg(p_start, p_start, p_end);
	}

	pos_type seekoff(off_type off, std::ios_base::seekdir dir, std::ios_base::openmode which) override
	{
		if (dir == std::ios_base::cur) gbump(static_cast<int>(off));
		else setg(p_start, (dir == std::ios_base::beg ? p_start : p_end) + off, p_end);
		return gptr() - p_start;
	}

	pos_type seekpos(pos_type pos, std::ios_base::openmode which) override
	{
		return seekoff(pos, std::ios_base::beg, which);
	}
};

struct memory_stream : virtual memory_buffer, public std::istream
{
	memory_stream(char const * first_elem, size_t size)
		: memory_buffer(first_elem, size), std::istream(static_cast<std::streambuf*>(this)) {}
};

struct float3 { float x, y, z; };
struct uint3 { uint32_t x, y, z; };

void HelperSSDRecon::fixBadPLY(std::string inputPath)
{
	//Read
	std::unique_ptr<std::istream> file_stream;
	std::vector<uint8_t> byte_buffer;

	std::vector<float3> verts;
	std::vector<uint3> triangles;

	try
	{
		//For most files < 1gb, pre-loading the entire file upfront and wrapping it into a 
		//stream is a net win for parsing speed, about 40% faster.
		byte_buffer = read_file_binary(inputPath);
		file_stream.reset(new memory_stream((char*)byte_buffer.data(), byte_buffer.size()));

		if (!file_stream || file_stream->fail()) throw std::runtime_error("file_stream failed to open " + inputPath);

		file_stream->seekg(0, std::ios::end);
		const float size_mb = file_stream->tellg() * float(1e-6);
		file_stream->seekg(0, std::ios::beg);

		tinyply::PlyFile file;
		file.parse_header(*file_stream);

		// Because most people have their own mesh types, tinyply treats parsed data as structured/typed byte buffers. 
		// See examples below on how to marry your own application-specific data structures with this one. 
		std::shared_ptr<tinyply::PlyData> vertices, faces;

		// The header information can be used to programmatically extract properties on elements
		// known to exist in the header prior to reading the data. For brevity of this sample, properties 
		// like vertex position are hard-coded: 
		try { vertices = file.request_properties_from_element("vertex", { "x", "y", "z" }); }
		catch (const std::exception & e) { wxLogError("tinyply exception"); }

		// Providing a list size hint (the last argument) is a 2x performance improvement. If you have 
		// arbitrary ply files, it is best to leave this 0. 
		try { faces = file.request_properties_from_element("face", { "vertex_indices" }, 3); }
		catch (const std::exception & e) { wxLogError("tinyply exception"); }

		file.read(*file_stream);

		verts.resize(vertices->count);
		std::memcpy(verts.data(), vertices->buffer.get(), vertices->buffer.size_bytes());

		triangles.resize(faces->count);
		std::memcpy(triangles.data(), faces->buffer.get(), faces->buffer.size_bytes());

	}
	catch (const std::exception & e)
	{
		wxLogError("Caught tinyply exception");
	}

	//Write
	std::filebuf fb_binary;
	fb_binary.open(inputPath, std::ios::out | std::ios::binary);
	std::ostream outstream_binary(&fb_binary);
	if (outstream_binary.fail()) throw std::runtime_error("failed to open " + inputPath);

	tinyply::PlyFile plyFile;

	plyFile.add_properties_to_element("vertex", { "x", "y", "z" },
		tinyply::Type::FLOAT32, verts.size(), reinterpret_cast<uint8_t*>(verts.data()), tinyply::Type::INVALID, 0);

	plyFile.add_properties_to_element("face", { "vertex_indices" },
		tinyply::Type::UINT32, triangles.size(), reinterpret_cast<uint8_t*>(triangles.data()), tinyply::Type::UINT8, 3);


	// Write a binary file
	plyFile.write(outstream_binary, true);
}
