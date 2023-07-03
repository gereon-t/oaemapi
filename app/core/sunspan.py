from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import lru_cache
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
    vis_idx: list[bool] = field(init=False, repr=False)

    def __len__(self) -> int:
        return len(self.time)

    @property
    def today_index(self) -> list[int]:
        current_date = datetime.now().date()

        start_time = datetime.combine(current_date, datetime.min.time()).timestamp()
        end_time = datetime.combine(current_date, datetime.max.time()).timestamp()

        return [idx for idx, time in enumerate(self.time) if start_time < time < end_time]

    @property
    def today_time(self) -> np.ndarray:
        return self.time[self.today_index]

    @property
    def today_elevation(self) -> np.ndarray:
        return self.elevation[self.today_index]

    @property
    def today_azimuth(self) -> np.ndarray:
        return self.azimuth[self.today_index]

    @property
    def time_range(self) -> timedelta:
        return timedelta(seconds=self.time[-1] - self.time[0])

    def intersect_with_oaem(self, oaem: Oaem) -> None:
        interp_oaem = oaem.interpolate(self.azimuth)
        self.vis_idx = [
            sun_elevation > mask_elevation
            for sun_elevation, mask_elevation in zip(self.elevation, interp_oaem.elevation)
        ]

    def query_azimuth(self, query_time: float) -> float:
        time_minute_precision = round(query_time / 60) * 60

        try:
            return self.azimuth[self.time.index(time_minute_precision)]
        except ValueError:
            return 0.0

    def query_elevation(self, query_time: float) -> float:
        time_minute_precision = round(query_time / 60) * 60

        try:
            return self.elevation[self.time.index(time_minute_precision)]
        except ValueError:
            return 0.0

    def visible(self, query_time: float) -> bool:
        time_minute_precision = round(query_time / 60) * 60

        try:
            return self.vis_idx[self.time.index(time_minute_precision)]
        except ValueError:
            return False

    def since(self, query_time: float) -> float:
        """Returns the first timestamp when the current visibility state started"""
        time_minute_precision = round(query_time / 60) * 60

        try:
            current_time_index = self.time.index(time_minute_precision)
        except ValueError:
            return 0.0

        for i in range(current_time_index, 0, -1):
            if self.vis_idx[i] != self.vis_idx[current_time_index]:
                return self.time[i]

    def until(self, query_time: float) -> float:
        """Returns the first timestamp when the current visibility state ends"""
        time_minute_precision = round(query_time / 60) * 60

        try:
            current_time_index = self.time.index(time_minute_precision)
        except ValueError:
            return 0.0

        for i in range(current_time_index, len(self.time)):
            if self.vis_idx[i] != self.vis_idx[current_time_index]:
                return self.time[i]


@lru_cache(maxsize=4096)
def compute_sunspan(pos: PointSet) -> SunSpan:
    pos.to_epsg(4326)

    current_date = datetime.now().date()
    start_time = datetime.combine(current_date - timedelta(days=1), datetime.min.time())
    end_time = datetime.combine(current_date + timedelta(days=1), datetime.max.time())
    times = pd.date_range(
        start_time,
        end_time,
        freq=timedelta(minutes=1),
        tz="Europe/Berlin",
    )
    solpos = solarposition.get_solarposition(times, pos.x, pos.y, altitude=pos.z)
    solpos = solpos.loc[solpos["apparent_elevation"] > 0, :]

    return SunSpan(
        time=[time.timestamp() for time in solpos.index],
        azimuth=np.deg2rad(solpos["azimuth"].to_numpy()),
        elevation=np.deg2rad(solpos["apparent_elevation"].to_numpy()),
    )
