import time
from typing import Tuple
import requests
from pandas import read_csv
from pointset.pointset import PointSet
import matplotlib.pyplot as plt
import logging
import numpy as np

# logging configuration
logging.basicConfig(
    format="%(levelname)-8s %(asctime)s.%(msecs)03d - %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

API_URL = "http://127.0.0.1:8000/api"

EPSG = 25832


def main():
    """ """

    # positions
    pos_file = read_csv("./data/M2RoverPhase.pos", delim_whitespace=True, skiprows=list(range(1000)))

    traj = PointSet(
        xyz=pos_file.iloc[:, 2:5].to_numpy(),
        epsg=4936,
    )
    traj.to_epsg(EPSG)

    plt.figure(figsize=(10, 5))
    ax = plt.subplot(111, projection="polar")
    for p in traj.xyz:
        start_time = time.time()
        request_url = f"{API_URL}/?pos_x={p[0]}&pos_y={p[1]}&pos_z={p[2]}&epsg={EPSG}"
        response = requests.get(request_url)

        azimuth, elevation = handle_response(response)
        ax.plot(azimuth, np.pi / 2 - elevation)
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)

        plt.pause(0.01)
        plt.cla()
        ax.clear()
        end_time = time.time()
        logging.info(f"Requested: position={p[0]},{p[1]},{p[2]}&epsg={EPSG} in {(end_time-start_time)*1000:.3f} ms")


def handle_response(response) -> Tuple[np.ndarray, np.ndarray]:
    oaem_list = response.json()["Data"].split(",")
    azimuth = []
    elevation = []
    for mask_item in oaem_list:
        if mask_item:
            az_el_pair = mask_item.split(":")
            azimuth.append(float(az_el_pair[0]))
            elevation.append(float(az_el_pair[1]))

    return np.array(azimuth), np.array(elevation)


if __name__ == "__main__":
    main()
