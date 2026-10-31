# Vendored from VAST-AI-Research/TripoSR (MIT). Changed: torchmcubes replaced by
# scikit-image marching cubes. See ../SOURCE.md.
from typing import Tuple

import numpy as np
import torch
import torch.nn as nn
from skimage.measure import marching_cubes


class IsosurfaceHelper(nn.Module):
    points_range: Tuple[float, float] = (0, 1)

    @property
    def grid_vertices(self) -> torch.FloatTensor:
        raise NotImplementedError


class MarchingCubeHelper(IsosurfaceHelper):
    def __init__(self, resolution: int) -> None:
        super().__init__()
        self.resolution = resolution
        self._grid_vertices = None

    @property
    def grid_vertices(self) -> torch.FloatTensor:
        if self._grid_vertices is None:
            # keep the vertices on CPU so that we can support very large resolution
            x, y, z = (
                torch.linspace(*self.points_range, self.resolution),
                torch.linspace(*self.points_range, self.resolution),
                torch.linspace(*self.points_range, self.resolution),
            )
            x, y, z = torch.meshgrid(x, y, z, indexing="ij")
            verts = torch.cat(
                [x.reshape(-1, 1), y.reshape(-1, 1), z.reshape(-1, 1)], dim=-1
            ).reshape(-1, 3)
            self._grid_vertices = verts
        return self._grid_vertices

    def forward(
        self,
        level: torch.FloatTensor,
    ) -> Tuple[torch.FloatTensor, torch.LongTensor]:
        """Extract the zero level set. `level` is negative inside the object.

        The grid is indexed (x, y, z) because `grid_vertices` uses an "ij" meshgrid. skimage
        returns vertices in that same index order, so unlike torchmcubes (which expects a
        z, y, x volume) no axis flip is needed. `gradient_direction="descent"` gives outward
        triangle winding here. `ascent` gave inward faces, caught by tests/test_isosurface.py.
        """
        volume = level.detach().cpu().view(self.resolution, self.resolution, self.resolution)
        verts, faces, _, _ = marching_cubes(
            volume.numpy(), level=0.0, gradient_direction="descent"
        )
        v_pos = torch.from_numpy(np.ascontiguousarray(verts, dtype=np.float32))
        v_pos = v_pos / (self.resolution - 1.0)
        t_pos_idx = torch.from_numpy(np.ascontiguousarray(faces, dtype=np.int64))
        return v_pos.to(level.device), t_pos_idx.to(level.device)
