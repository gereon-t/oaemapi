from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import cached_property
from app.core.oaem import Oaem
import numpy as np
import pandas as pd
from pointset import PointSet
from pvlib import solarposition


@dataclass
class SunTrack:
    time: np.ndarray
    azimuth: np.ndarray
    elevation: np.ndarray
    _vis_idx: list[int] = field(init=False, repr=False)

    @classmethod
    def at(pos: PointSet, date: datetime, freq: timedelta) -> "SunTrack":
        start_time = datetime.combine(date, datetime.min.time())
        end_time = datetime.combine(date, datetime.max.time())

        times = pd.date_range(
            start_time,
            end_time,
            freq=freq,
            tz=date.tzinfo,
        )

        solpos = solarposition.get_solarposition(time=times, latitude=pos.x, longitude=pos.y, altitude=pos.z)
        solpos = solpos.loc[solpos["apparent_elevation"] > 0, :]

        return SunTrack(
            time=np.array([time.timestamp() for time in solpos.index], dtype=float),
            azimuth=np.deg2rad(solpos["azimuth"].to_numpy(dtype=float)),
            elevation=np.deg2rad(solpos["apparent_elevation"].to_numpy(dtype=float)),
        )

    def interpolate(self, query_time: float | np.ndarray) -> tuple[float | np.ndarray, float | np.ndarray]:
        return np.interp(query_time, self.time, self.azimuth), np.interp(query_time, self.time, self.elevation)

    def intersect_with_oaem(self, oaem: Oaem) -> None:
        self._vis_idx = [
            elevation > oaem.query(azimuth=azimuth) for azimuth, elevation in zip(self.azimuth, self.elevation)
        ]

    def _time_to_index(self, query_time: float) -> int:
        return np.argmin(np.abs(self.time - query_time))

    def is_visible(self, query_time: float) -> bool:
        return self._vis_idx[self._time_to_index(query_time)]


@dataclass
class SunSpan:
    pos: PointSet

    def __post_init__(self) -> None:
        self.pos.to_epsg(4326)

    @cached_property
    def sun_track_of_day(self, date: datetime, freq: timedelta = timedelta(minutes=1)) -> list[int]:
        start_time = datetime.combine(date, datetime.min.time())
        end_time = datetime.combine(date, datetime.max.time())

        times = pd.date_range(
            start_time,
            end_time,
            freq=freq,
            tz=date.tzinfo,
        )

        solpos = solarposition.get_solarposition(
            time=times, latitude=self.pos.x, longitude=self.pos.y, altitude=self.pos.z
        )
        solpos = solpos.loc[solpos["apparent_elevation"] > 0, :]

        return SunTrack(
            time=np.array([time.timestamp() for time in solpos.index], dtype=float),
            azimuth=np.deg2rad(solpos["azimuth"].to_numpy(dtype=float)),
            elevation=np.deg2rad(solpos["apparent_elevation"].to_numpy(dtype=float)),
        )

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
        interp_elevation = oaem.query(self.azimuth)
        self.vis_idx = [
            sun_elevation > mask_elevation for sun_elevation, mask_elevation in zip(self.elevation, interp_elevation)
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

    def query_visibility(self, query_time: float) -> bool:
        pass

    def since(self, query_time: float) -> float | None:
        """Returns the first timestamp when the current visibility state started"""
        time_minute_precision = round(query_time / 60) * 60

        try:
            current_time_index = self.time.index(time_minute_precision)
        except ValueError:
            return None

        for i in range(current_time_index, 0, -1):
            if self.vis_idx[i] != self.vis_idx[current_time_index]:
                return self.time[i]

    def until(self, query_time: float) -> float | None:
        """Returns the first timestamp when the current visibility state ends"""
        time_minute_precision = float(round(query_time / 60) * 60)

        try:
            current_time_index = self.time.index(time_minute_precision)
        except ValueError:
            return None

        for i in range(current_time_index, len(self.time)):
            if self.vis_idx[i] != self.vis_idx[current_time_index]:
                return self.time[i]


def compute_sunspan(pos: PointSet, current_date: datetime) -> SunSpan:
    pos.to_epsg(4326)

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
