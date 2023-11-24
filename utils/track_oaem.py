import argparse
import numpy as np
from trajectopy_core.trajectory import Trajectory
from app.oaem import compute_oaem
from app.geoid import Geoid
from app.edge_provider import LocalEdgeProvider
from app.config import EDGE_EPSG

# import matplotlib.pyplot as plt
from tqdm import tqdm

geoid = Geoid()
edge_provider = LocalEdgeProvider(data_path="data/bonn_lod2", lod=2)


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--input", help="Path to trajectory file", required=True)
    argparser.add_argument("--output", required=False, help="Path to output file", default="./oaems.csv")
    args = argparser.parse_args()

    traj = Trajectory.from_file(args.input)
    traj.pos.to_epsg(EDGE_EPSG)

    oaems = []

    # plt.figure(figsize=(10, 5))
    # ax = plt.subplot(111, projection="polar")

    last_pos = None
    for pos_xyz in tqdm(traj.pos.xyz):
        rounded_pos = np.round(pos_xyz, 1)
        if last_pos is None or not np.allclose(rounded_pos, last_pos):
            oaem = compute_oaem(
                geoid=geoid,
                edge_provider=edge_provider,
                pos_x=pos_xyz[0],
                pos_y=pos_xyz[1],
                pos_z=pos_xyz[2],
                epsg=traj.pos.epsg,
            )
            last_pos = rounded_pos

            mean_shadowing = np.mean(oaem.elevation / (np.pi / 2))

            oaems.append(np.r_[rounded_pos, mean_shadowing, oaem.elevation])

        # ax.plot(oaem.azimuth, np.pi / 2 - oaem.elevation)
        # ax.set_theta_zero_location("N")
        # ax.set_theta_direction(-1)
        # ax.set_title(f"Mean shadowing: {mean_shadowing * 100:.2f} %")

        # plt.pause(0.1)
        # ax.clear()

    np.savetxt(args.output, np.array(oaems), delimiter=",", fmt="%.4f")


if __name__ == "__main__":
    main()
