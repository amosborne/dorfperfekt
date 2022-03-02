from collections import defaultdict
from collections.abc import MutableMapping

from .tile import Terrain, Tile

ORI_OFFSET = {0: (1, 0), 1: (0, 1), 2: (-1, 1), 3: (-1, 0), 4: (0, -1), 5: (1, -1)}


class Map(MutableMapping):
    def __init__(self):
        self.tiles = defaultdict(lambda: None)
        self.tiles[0, 0] = (Tile.from_string("g"), 0)

    def __getitem__(self, key):
        return self.tiles[key]

    def __setitem__(self, key, item):
        self.tiles[key] = item

    def __delitem__(self, key):
        del self.tiles[key]

    def __iter__(self):
        return self.tiles.__iter__()

    def __len__(self):
        return len(self.tiles)

    def neighbors(self, pos):
        return {
            ori: (pos[0] + opos[0], pos[1] + opos[1])
            for ori, opos in ORI_OFFSET.items()
        }

    def open_positions(self):
        closed_positions = self.tiles.keys()
        return {
            pos
            for cpos in closed_positions
            for pos in self.neighbors(cpos).values()
            if pos not in closed_positions
        }

    def is_valid_position(self, tile, pos, ori):
        for nori, npos in self.neighbors(pos).items():
            if self[npos] is None:
                continue
            else:
                that_tile, that_ori = self[npos]
                that_terrain = that_tile[nori + 3 - that_ori]

            this_terrain = tile[nori - ori]
            this_is_lake = all([t is Terrain.WATER for t in tile])
            that_is_lake = all([t is Terrain.WATER for t in that_tile])
            terrains = (this_terrain, that_terrain)

            if (
                Terrain.WATER in terrains
                and Terrain.STATION not in terrains
                and not (this_is_lake or that_is_lake)
                and not this_terrain is that_terrain
            ):
                return False

            if (
                Terrain.TRAIN in terrains
                and Terrain.STATION not in terrains
                and not this_terrain is that_terrain
            ):
                return False

        return True

    def valid_open_positions(self, tile):
        return {
            pos
            for pos in self.open_positions()
            for ori in range(6)
            if self.is_valid_position(tile, pos, ori)
        }
