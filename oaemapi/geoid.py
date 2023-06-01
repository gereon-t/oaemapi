from enum import Enum
from functools import lru_cache
import logging
from pandas import read_csv

from pointset import PointSet
from scipy.interpolate import NearestNDInterpolator, LinearNDInterpolator

from oaemapi.config import GEOID_EPSG, GEOID_INTERP_EPSG, GEOID_RES

# logger configuration
logger = logging.getLogger("root")


class InvalidInterpolatorError(Exception):
    """"""


class Interpolator(Enum):
    NEAREST = 0
    LINEAR = 1


class Geoid:
    def __init__(
        self,
        filename: str,
        epsg: int = GEOID_EPSG,
        interpolator: Interpolator = Interpolator.LINEAR,
    ):
        # read csv
        data = read_csv(filename, header=None, delim_whitespace=True)
        data = data.to_numpy()

        self.pos = PointSet(xyz=data[:, 0:3], epsg=epsg)
        self.pos.to_epsg(GEOID_INTERP_EPSG)

        # Interpolator
        if interpolator == Interpolator.NEAREST:
            self.__interp = NearestNDInterpolator(self.pos.xyz[:, 0:2], self.pos.z)
        elif interpolator == Interpolator.LINEAR:
            self.__interp = LinearNDInterpolator(self.pos.xyz[:, 0:2], self.pos.z)
        else:
            raise InvalidInterpolatorError()

        logger.info(f"Initialized geoid from: {filename}, Number of grid points: {len(data)}")

    @lru_cache(maxsize=2048)
    def interpolate(self, pos: PointSet) -> float:
        """
        Get geoid undulation for query position
        """
        pos.to_epsg(GEOID_INTERP_EPSG)
        pos.round_to(GEOID_RES)
        logger.info(f"Interpolating geoid undulation for position: {pos}")

        # interpolate
        return self.__interp(pos.x, pos.y)
