from enum import Enum
from functools import lru_cache

from pandas import read_csv
from pointset import PointSet
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator

from config import GEOID_EPSG, GEOID_FILE, logger


class InvalidInterpolatorError(Exception):
    """"""


class ZeroInterpolator:
    def __call__(self, *args) -> float:
        return 0.0


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
        filename: str = GEOID_FILE,
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
        if not filename:
            self.__interp = ZeroInterpolator()
            logger.info("No geoid file provided, no undulation will be applied!")
            return

        # read csv
        data = read_csv(filename, header=None, delim_whitespace=True)

        self.pos = PointSet(xyz=data.to_numpy(), epsg=epsg)
        self.epsg = epsg

        # Interpolator
        if interpolator == Interpolator.NEAREST:
            self.__interp = NearestNDInterpolator(self.pos.xyz[:, 0:2], self.pos.z)
        elif interpolator == Interpolator.LINEAR:
            self.__interp = LinearNDInterpolator(self.pos.xyz[:, 0:2], self.pos.z)
        else:
            raise InvalidInterpolatorError()

        logger.info(
            "Initialized geoid from: %s, Number of grid points: %i",
            filename,
            len(self.pos.xyz),
        )

    @lru_cache(maxsize=2048)
    def interpolate(self, pos: PointSet) -> float:
        """
        Interpolates the geoid undulation for a given position.

        Args:
            pos (PointSet): A PointSet object representing the position to interpolate.

        Returns:
            float: The interpolated geoid undulation value.
        """
        logger.debug("Interpolating geoid undulation for position: %s", pos.xyz)

        pos.to_epsg(self.epsg)

        # interpolate
        return self.__interp(pos.x, pos.y)
