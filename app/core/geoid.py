from enum import Enum
from functools import lru_cache

from pandas import read_csv
from pointset import PointSet
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator
import numpy as np
from app.config import GEOID_EPSG, WFS_EPSG, logger


class InvalidInterpolatorError(Exception):
    """"""


class Interpolator(Enum):
    NEAREST = 0
    LINEAR = 1


class Geoid:
    """
    A class representing a geoid model.

    Attributes:
        pos (PointSet): A PointSet object representing the grid points of the geoid model.
        __interp (LinearNDInterpolator or NearestNDInterpolator): An interpolator object used to interpolate the geoid undulation.
    """

    def __init__(
        self,
        filename: str,
        epsg: int = GEOID_EPSG,
        interpolator: Interpolator = Interpolator.LINEAR,
    ):
        """
        Initializes a Geoid object from a CSV file.

        Args:
            filename (str): The path to the CSV file containing the geoid data.
            epsg (int, optional): The EPSG code of the geoid data. Defaults to GEOID_EPSG.
            interpolator (Interpolator, optional): The type of interpolator to use. Defaults to Interpolator.LINEAR.

        Raises:
            InvalidInterpolatorError: If an invalid interpolator type is provided.
        """
        # read csv
        data = read_csv(filename, header=None, delim_whitespace=True)
        data = data.to_numpy()

        self.pos = PointSet(xyz=data, epsg=epsg)
        self.pos.to_epsg(WFS_EPSG)

        # Interpolator
        if interpolator == Interpolator.NEAREST:
            self.__interp = NearestNDInterpolator(self.pos.xyz[:, 0:2], self.pos.z)
        elif interpolator == Interpolator.LINEAR:
            self.__interp = LinearNDInterpolator(self.pos.xyz[:, 0:2], self.pos.z)
        else:
            raise InvalidInterpolatorError()

        logger.info(
            f"Initialized geoid from: {filename}, Number of grid points: {len(data)}"
        )

    @lru_cache(maxsize=2048)
    def interpolate(self, pos: PointSet) -> np.ndarray:
        """
        Interpolates the geoid undulation for a given position.

        Args:
            pos (PointSet): A PointSet object representing the position to interpolate.

        Returns:
            float: The interpolated geoid undulation value.
        """
        logger.debug(f"Interpolating geoid undulation for position: {pos.xyz}")

        # interpolate
        return self.__interp(pos.x, pos.y)
