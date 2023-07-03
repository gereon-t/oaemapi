from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from pointset import PointSet
from pvlib import solarposition

from app.core.oaem import Oaem


@dataclass
class SunSpan:
    time: np.ndarray
    azimuth: np.ndarray
    elevation: np.ndarray
    sun_start: float = 0.0
    sun_end: float = 0.0

    def __len__(self) -> int:
        return len(self.time)

    @property
    def time_range(self) -> timedelta:
        return timedelta(seconds=self.time[-1] - self.time[0])

    @property
    def future_azimuth(self) -> np.ndarray:
        return self.azimuth[len(self) // 2 :]

    @property
    def future_elevation(self) -> np.ndarray:
        return self.elevation[len(self) // 2 :]

    @property
    def future_time(self) -> np.ndarray:
        return self.time[len(self) // 2 :]

    @property
    def query_time(self) -> float:
        return self.time[len(self) // 2]

    @property
    def query_azimuth(self) -> float:
        return self.azimuth[len(self) // 2]

    @property
    def query_elevation(self) -> float:
        return self.elevation[len(self) // 2]

    @property
    def query_solpos(self) -> tuple[float, float, float]:
        return (self.query_time, self.query_azimuth, self.query_elevation)

    @classmethod
    def from_position(cls: "SunSpan", pos: PointSet, sym_half_range: timedelta) -> "SunSpan":
        pos.to_epsg(4326)
        current_time = datetime.now()
        times = pd.date_range(
            current_time - sym_half_range,
            current_time + sym_half_range,
            freq=timedelta(minutes=1),
            tz="Europe/Berlin",
        )
        solpos = solarposition.get_solarposition(times, pos.x, pos.y, altitude=pos.z)
        # remove nighttime
        solpos = solpos.loc[solpos["apparent_elevation"] > 0, :]

        return cls(
            time=[time.timestamp() for time in times],
            azimuth=np.deg2rad(solpos["azimuth"].to_numpy()),
            elevation=np.deg2rad(solpos["apparent_elevation"].to_numpy()),
        )

    def intersect_with_oaem(self, oaem: Oaem) -> None:
        interp_oaem = oaem.interpolate(self.future_azimuth)

        start_index, self.sun_start = next(
            (
                (i + 1, time)
                for i, (time, elevation, mask_elevation) in enumerate(
                    zip(self.future_time, self.future_elevation, interp_oaem.elevation)
                )
                if elevation > mask_elevation
            ),
            0.0,
        )

        self.sun_end = next(
            (
                time
                for time, elevation, mask_elevation in zip(
                    self.future_time[start_index:],
                    self.future_elevation[start_index:],
                    interp_oaem.elevation[start_index:],
                )
                if elevation < mask_elevation
            ),
            0.0,
        )
