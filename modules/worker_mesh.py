from PySide6.QtCore import QObject, Signal
import numpy as np
import pyvista as pv


class WorkerMesh(QObject):
    # Signals to communicate with the main thread
    finished = Signal(pv.PolyData)
    log = Signal(str)

    def __init__(self, ptc: pv.PolyData, chunk_size: int) -> None:
        """Initialize the WorkerMesh class.

        Args:
            ptc (pv.PolyData): The point cloud data to mesh.
            chunk_size (int): The size of the chunks to process.
        """
        self.ptc = ptc
        self.chunk_size = chunk_size
        super().__init__()

    def spatial_chunks(self, polydata: pv.PolyData, chunk_size: str = 50.0) -> None:
        """Yield sub-clouds split into cubic regions of `chunk_size` meters.

        Args:
            polydata (pv.PolyData): The input point cloud data.
            chunk_size (float): The size of the chunks to create.
        """
        bounds = polydata.bounds  # (xmin, xmax, ymin, ymax, zmin, zmax)
        xmin, xmax, ymin, ymax, zmin, zmax = bounds
        points = polydata.points
        if "RGB" in polydata.point_data:
            rgb = polydata.point_data["RGB"]
        else:
            rgb = None
        chunk_sizes = [chunk_size, 1.1*chunk_size]  # To fill in the gaps
        # Emit the number of chunks
        n_chunks = np.ceil((xmax - xmin) / chunk_size * \
            (ymax - ymin) / chunk_size * (zmax - zmin) / chunk_size)
        self.log.emit(f"Approximate number of chunks to process the mesh on: {n_chunks}")
        for cs in chunk_sizes:
            for x0 in np.arange(xmin, xmax, cs):
                for y0 in np.arange(ymin, ymax, cs):
                    for z0 in np.arange(zmin, zmax, cs):
                        mask = (
                            (points[:, 0] >= x0) & (points[:, 0] < x0 + cs) &
                            (points[:, 1] >= y0) & (points[:, 1] < y0 + cs) &
                            (points[:, 2] >= z0) & (points[:, 2] < z0 + cs)
                        )
                        if not np.any(mask):
                            continue
                        sub_pts = points[mask]
                        sub_cloud = pv.PolyData(sub_pts)
                        if rgb is not None:
                            rgb_chunk = np.ascontiguousarray(
                                rgb[mask], dtype=np.uint8)
                            sub_cloud.point_data["RGB"] = rgb_chunk
                        yield sub_cloud

    def mesh_the_point_cloud(self) -> None:
        """Mesh point cloud in voxelized spatial chunks."""
        try:
            # Spatial chunks (50 m cube)
            meshes = []
            i = 0
            for sub_cloud in self.spatial_chunks(polydata=self.ptc, chunk_size=50.0):
                i += 1
                self.log.emit(
                    f"Meshing chunk {i} with {sub_cloud.n_points} points...")
                try:
                    mesh_chunk = sub_cloud.delaunay_2d()
                    meshes.append(mesh_chunk)
                except Exception as e:
                    self.log.emit(f"Chunk {i} failed: {e}")
            # Merge
            if meshes:
                mesh_polydata = pv.merge(meshes, merge_points=True)
                self.finished.emit(mesh_polydata)
            else:
                self.log.emit("No chunks produced any mesh!")
        except Exception as e:
            self.log.emit(str(e))
