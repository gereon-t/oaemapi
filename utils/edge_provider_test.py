import numpy as np
import pandas as pd
from app.edge_provider import LocalEdgeProvider, WFSEdgeProvider
import matplotlib.pyplot as plt
from pointset import PointSet
from app.oaem import oaem_from_edge_list
from app.geoid import Geoid
from tqdm import tqdm


def main():
    # positions
    pos_file = pd.read_csv("./data/M2RoverPhase.pos", delim_whitespace=True, skiprows=list(range(1000)))

    traj = PointSet(
        xyz=pos_file.iloc[:, 2:5].to_numpy(),
        epsg=4936,
    )
    traj.to_epsg(25832)

    wfs_provider = WFSEdgeProvider()
    local_provider_lod1 = LocalEdgeProvider(data_path="data/bonn_lod1", lod=1)
    local_provider_lod2 = LocalEdgeProvider(data_path="data/bonn_lod2", lod=2)

    # geoid
    geoid = Geoid()

    plt.figure(figsize=(10, 5))
    ax_local_lod1 = plt.subplot(131, projection="polar")
    ax_local_lod2 = plt.subplot(132, projection="polar")
    ax_wfs = plt.subplot(133, projection="polar")

    for p in tqdm(traj.xyz):
        pos = PointSet(xyz=p, epsg=25832, init_local_transformer=False)
        pos.z -= geoid.interpolate(pos)
        wfs_edge_list = wfs_provider.get_edges(pos)
        local_edge_list_lod1 = local_provider_lod1.get_edges(pos)
        local_edge_list_lod2 = local_provider_lod2.get_edges(pos)

        local_oaem_lod1 = oaem_from_edge_list(local_edge_list_lod1, pos)
        local_oaem_lod2 = oaem_from_edge_list(local_edge_list_lod2, pos)
        wfs_oaem = oaem_from_edge_list(wfs_edge_list, pos)

        ax_local_lod1.plot(local_oaem_lod1.azimuth, np.pi / 2 - local_oaem_lod1.elevation)
        ax_local_lod1.set_theta_zero_location("N")
        ax_local_lod1.set_theta_direction(-1)
        ax_local_lod1.set_title("Local LOD1")

        ax_local_lod2.plot(local_oaem_lod2.azimuth, np.pi / 2 - local_oaem_lod2.elevation)
        ax_local_lod2.set_theta_zero_location("N")
        ax_local_lod2.set_theta_direction(-1)
        ax_local_lod2.set_title("Local LOD2")

        ax_wfs.plot(wfs_oaem.azimuth, np.pi / 2 - wfs_oaem.elevation)
        ax_wfs.set_theta_zero_location("N")
        ax_wfs.set_theta_direction(-1)
        ax_wfs.set_title("WFS LOD1")

        plt.pause(0.1)
        ax_wfs.clear()
        ax_local_lod1.clear()
        ax_local_lod2.clear()


if __name__ == "__main__":
    main()
