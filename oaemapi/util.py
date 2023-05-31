from typing import Callable, Tuple
import numpy as np
from scipy.spatial import ConvexHull

INTERP_RES = 0.1


def lengths_from_xyz(xyz: np.ndarray) -> np.ndarray:
    """
    Returns trajectory lengths for given positions
    """
    xyz_1 = xyz[0:-1, :]
    xyz_2 = xyz[1:, :]

    diff = xyz_2 - xyz_1

    dists = np.linalg.norm(diff, axis=1)
    return np.r_[0, np.cumsum(dists)]


def compute_az_el(pcloud: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Computes azimuth and elevation from points centered around the viewpoint
    """
    azimuth = np.arctan2(pcloud[:, 0], pcloud[:, 1])
    elevation = np.arctan2(
        pcloud[:, 2],
        np.sqrt(np.power(pcloud[:, 0], 2) + np.power(pcloud[:, 1], 2)),
    )
    return azimuth, elevation


def wrap_to_2pi(angles: np.ndarray) -> np.ndarray:
    """
    Converts angles from interval [-pi, pi] to  [0 2pi]
    """
    return (angles + 2 * np.pi) % (2 * np.pi)


def azel_to_polar(azimuth: np.ndarray, elevation: np.ndarray) -> np.ndarray:
    """
    Converts azimuth and elevation to polar "sky-plot" coordinates
    """
    return np.c_[
        (np.pi / 2 - elevation) * np.cos(azimuth),
        (np.pi / 2 - elevation) * np.sin(azimuth),
    ]


def moving(
    *, x: np.ndarray, win_size: int, function: Callable[[np.ndarray], float]
) -> np.ndarray:
    """
    Function to compute values with
    a given window size and function.
    For example, if function=np.std this method computes the moving
    standard deviation.

    Returns a list.
    """
    if not callable(function):
        raise TypeError("'function' must be Callable[[np.ndarray], float]")

    if win_size == 1:
        return x

    ext = int(np.floor(win_size / 2))

    # extend array
    x = np.r_[x[-ext:], x, x[: ext + 1]]

    # moving
    mov = [function(x[i - ext : i + ext + 1]) for i in range(ext, len(x) - ext - 1)]

    return np.array(mov)


def interp_face(face_boundary):
    dists = lengths_from_xyz(face_boundary)
    grid = np.arange(0, np.sum(dists), INTERP_RES)

    x_interp = np.interp(grid, dists, face_boundary[:, 0])
    y_interp = np.interp(grid, dists, face_boundary[:, 1])
    z_interp = np.interp(grid, dists, face_boundary[:, 2])

    interp = np.c_[x_interp, y_interp, z_interp]
    return interp


def hidden_point_removal(pcloud: np.ndarray, param: float) -> np.ndarray:
    """
    Hidden Point Removal (Katz et al.)

    pcloud points must be centered around viewpoint
    Returns numpy array with indices of visible points
    """
    normp = np.linalg.norm(pcloud, axis=1, keepdims=True)
    radius = np.tile(np.max(normp) * (10**param), (len(pcloud), 1))
    spherical_flip = pcloud + 2 * (radius - normp) * pcloud / normp
    hull = ConvexHull(spherical_flip)
    return hull.vertices
