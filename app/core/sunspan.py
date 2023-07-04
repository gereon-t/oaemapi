from dataclasses import dataclass, field
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from pointset import PointSet
from pvlib import solarposition

from app.core.oaem import Oaem


@np.vectorize
def wrap_to_pi(angle: float | np.ndarray) -> float | np.ndarray:
    angle %= 2 * np.pi
    if angle > np.pi:
        angle -= 2 * np.pi
    return angle


@dataclass
class SunTrack:
    pos: PointSet
    vis_idx: np.ndarray = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.pos.to_epsg(4326)

    def get_sun_track(
        self, date: datetime, freq: timedelta = timedelta(minutes=1), daylight_only: bool = False
    ) -> "SunTrack":
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

        if daylight_only:
            solpos = solpos.loc[solpos["apparent_elevation"] > 0, :]

        return np.c_[
            np.array([time.timestamp() for time in solpos.index], dtype=float),
            wrap_to_pi(np.deg2rad(solpos["azimuth"].to_numpy(dtype=float))),
            np.deg2rad(solpos["apparent_elevation"].to_numpy(dtype=float)),
        ]

    @property
    def current_sunpos(self) -> tuple[float, float]:
        date = datetime.now().astimezone()
        solpos = solarposition.get_solarposition(
            time=date, latitude=self.pos.x, longitude=self.pos.y, altitude=self.pos.z
        )
        return wrap_to_pi(np.deg2rad(solpos["azimuth"].iloc[0])), np.deg2rad(solpos["apparent_elevation"].iloc[0])

    def intersect_with_oaem(self, oaem: Oaem) -> None:
        date = datetime.now().astimezone()
        sun_track = self.get_sun_track(date=date)
        oaem_elevations = oaem.query(sun_track[:, 1])
        self.vis_idx = np.c_[sun_track[:, 0], sun_track[:, 2] > oaem_elevations]

    @property
    def until(self) -> float | None:
        current_tstamp = datetime.now().astimezone().timestamp()
        current_idx = np.searchsorted(self.vis_idx[:, 0], current_tstamp)

        for i in range(current_idx, len(self.vis_idx) - 1):
            if self.vis_idx[i + 1, 1] != self.vis_idx[i, 1]:
                return self.vis_idx[i, 0]

        return None

    @property
    def since(self) -> float:
        current_tstamp = datetime.now().astimezone().timestamp()
        current_idx = np.searchsorted(self.vis_idx[:, 0], current_tstamp)

        for i in range(current_idx, 0, -1):
            if self.vis_idx[i - 1, 1] != self.vis_idx[i, 1]:
                return self.vis_idx[i, 0]

        return None
