import numpy as np
from app.edge_provider import LocalEdgeProvider, WFSEdgeProvider
import matplotlib.pyplot as plt
from pointset import PointSet
from app.oaem import Oaem, oaem_from_edge_list
from app.geoid import Geoid


def main():
    xyz = np.array(
        [
            [364938.4000, 5621690.5000, 110.0000],
            [364895.2146, 5621150.5605, 107.4668],
            [364834.6853, 5621114.0750, 108.1602],
            [364783.4349, 5621127.6695, 108.2684],
            [364793.5793, 5621220.9659, 108.1232],
            [364868.9891, 5621310.2283, 107.9929],
            [364937.1665, 5621232.2154, 107.9581],
            [364919.0140, 5621153.6880, 107.8130],
            [364906.8750, 5621199.2600, 108.0610],
            [364951.9350, 5621243.4890, 106.9560],
            [364992.5600, 5621229.7440, 106.7330],
            [365003.7740, 5621203.8200, 106.7760],
            [364987.8850, 5621179.5160, 107.8890],
            [364950.1180, 5621148.5770, 107.9120],
        ]
    )

    mode = "local"

    wfs_provider = WFSEdgeProvider()
    local_provider = LocalEdgeProvider()

    # geoid
    geoid = Geoid()

    plt.figure(figsize=(10, 5))
    ax_local = plt.subplot(221, projection="polar")
    ax_wfs = plt.subplot(222, projection="polar")

    ax_edges_local = plt.subplot(223)
    ax_edges_wfs = plt.subplot(224)
    for p in xyz:
        pos = PointSet(xyz=p, epsg=25832, init_local_transformer=False)
        pos.z -= geoid.interpolate(pos)
        local_edge_list = local_provider.get_edges(pos)
        wfs_edge_list = wfs_provider.get_edges(pos)

        local_oaem = oaem_from_edge_list(local_edge_list, pos)
        wfs_oaem = oaem_from_edge_list(wfs_edge_list, pos)

        ax_local.plot(local_oaem.azimuth, np.pi / 2 - local_oaem.elevation)
        ax_local.set_theta_zero_location("N")
        ax_local.set_theta_direction(-1)

        ax_wfs.plot(wfs_oaem.azimuth, np.pi / 2 - wfs_oaem.elevation)
        ax_wfs.set_theta_zero_location("N")
        ax_wfs.set_theta_direction(-1)

        for edge in local_edge_list:
            ax_edges_local.plot(
                [edge.start[0], edge.end[0]], [edge.start[1], edge.end[1]]
            )

        for edge in wfs_edge_list:
            ax_edges_wfs.plot(
                [edge.start[0], edge.end[0]], [edge.start[1], edge.end[1]]
            )

        ax_edges_local.axis("equal")
        ax_edges_wfs.axis("equal")

        plt.pause(5)
        # plt.cla()
        ax_local.clear()
        ax_wfs.clear()
        ax_edges_local.clear()
        ax_edges_wfs.clear()


if __name__ == "__main__":
    main()
