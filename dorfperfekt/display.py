import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Polygon

from dorfperfekt.tile import Terrain

CMAP = LinearSegmentedColormap.from_list("gr", ["g", "w", "r"])

angles = np.linspace(start=0, stop=360, num=6, endpoint=False)
angles = np.deg2rad(angles)

DIST = np.cos(np.deg2rad(30))
XVEC = np.array([0, 1])
YVEC = np.array([DIST, np.sin(np.deg2rad(30))])
VERTICES = np.transpose(np.vstack((np.cos(angles), np.sin(angles))))

TERRAIN_COLORS = {
    Terrain.GRASS: "lightgreen",
    Terrain.FOREST: "darkgreen",
    Terrain.RANCH: "gold",
    Terrain.DWELLING: "firebrick",
    Terrain.WATER: "steelblue",
    Terrain.STATION: "slategray",
    Terrain.TRAIN: "tab:brown",
    Terrain.COAST: "aqua",
}


def pos2coords(pos):
    return np.matmul(pos, np.vstack((XVEC, YVEC))) * 2 * DIST


def coords2pos(coords):
    coords = np.array(coords) / (2 * DIST)
    pos = np.linalg.solve(np.vstack((XVEC, YVEC)).T, coords.T).T
    return tuple([int(np.rint(p)) for p in pos])


def format_map(draw_map):
    def wrapper(*args, **kwargs):
        ax = kwargs["ax"] if "ax" in kwargs else args[0]
        ax.clear()
        ax.set_aspect("equal")
        ax.axis("off")
        draw_map(*args, **kwargs)
        ax.autoscale()

    return wrapper


@format_map
def draw_position_map(ax, tilemap, movelist):
    def draw_tile(pos, color, edge):
        coords = pos2coords(pos)
        corners = coords + VERTICES
        patch = Polygon(corners, edgecolor=edge, facecolor=color)
        ax.add_patch(patch)

    for pos in tilemap.tiles:
        color = "lightsteelblue" if pos in tilemap.ruined else "lightslategrey"
        draw_tile(pos, color, "white")

    color = CMAP(np.linspace(0, 1, len(movelist)))
    for idx, move in enumerate(movelist):
        for pos, _ in move:
            draw_tile(pos, color[idx], "black")


@format_map
def draw_terrain_map(ax, placements):
    for idx, (pos, terrains) in enumerate(placements):
        color = None if idx < len(placements) - 1 else "black"
        coords = pos2coords(pos)
        corners = coords + VERTICES
        corners = np.vstack((corners, corners[0]))
        corners = np.flipud(corners)
        for k in range(len(corners) - 1):
            subpatch_corners = [coords, corners[k], corners[k + 1]]
            subpatch = Polygon(
                subpatch_corners,
                edgecolor=color,
                facecolor=TERRAIN_COLORS[terrains[(k + 2) % 6]],
            )
            ax.add_patch(subpatch)
