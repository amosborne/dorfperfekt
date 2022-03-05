import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Polygon

cmap = LinearSegmentedColormap.from_list("gr", ["g", "w", "r"])


def hex_coordinates(pos):
    dist = np.cos(np.deg2rad(30))
    xvec = np.array([0, 1]) * pos[0]
    yvec = np.array([dist, np.sin(np.deg2rad(30))]) * pos[1]
    origin = (xvec + yvec) * 2 * dist

    angles = np.linspace(start=0, stop=360, num=6, endpoint=False)
    angles = np.deg2rad(angles)
    vertices = np.transpose(np.vstack((np.cos(angles), np.sin(angles))))

    return origin, vertices + origin


def draw_position_map(ax, tilemap, movelist=[]):
    ax.clear()
    ax.set_aspect("equal")
    ax.axis("off")

    for pos in tilemap:
        _, vertices = hex_coordinates(pos)
        color = "yellow" if tilemap.is_ruined_position(pos) else "blue"
        patch = Polygon(vertices, edgecolor="black", facecolor=color)
        ax.add_patch(patch)

    cidx = np.linspace(0, 1, len(movelist))
    for idx, move in enumerate(movelist):
        color = cmap(cidx[idx])
        for pos, _ in move:
            _, vertices = hex_coordinates(pos)
            patch = Polygon(vertices, edgecolor="black", facecolor=color)
            ax.add_patch(patch)

    ax.autoscale()


def draw_terrain_map(ax, map):
    ax.clear()
    ax.set_aspect("equal")
    ax.axis("off")
