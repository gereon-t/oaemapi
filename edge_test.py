from app.edge import Edge
from app.edge_provider import LocalEdgeProvider
import matplotlib.pyplot as plt


def main():
    local_provider = LocalEdgeProvider()

    plt.figure(figsize=(10, 5))
    ax_edges_local = plt.subplot(223)

    for index in range(0, 1000, 2):
        edge = Edge(
            start=local_provider.edge_data[index, 0:3],
            end=local_provider.edge_data[index, 3:],
        )
        ax_edges_local.plot([edge.start[0], edge.end[0]], [edge.start[1], edge.end[1]])

    ax_edges_local.axis("equal")
    plt.show()


if __name__ == "__main__":
    main()
