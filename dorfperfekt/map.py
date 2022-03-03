from collections import defaultdict
from collections.abc import MutableMapping

from .tile import Terrain, Tile

OFFSETS = set(zip(range(6), [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]))


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
            (ori, npos)
            for ori, opos in OFFSETS
            if self[(npos := (pos[0] + opos[0], pos[1] + opos[1]))] is not None
        }

    def open_positions(self):
        return {
            pos
            for cpos in closed_positions
            for _, pos in self.neighbors(cpos)
            if pos not in (closed_positions := self.tiles.keys())
        }

    def is_valid_position(self, tile, pos, ori):
        for sori, npos in self.neighbors(pos):
            this_terrain = tile[sori - ori]
            this_is_lake = all([t is Terrain.WATER for t in tile])

            that_tile, that_ori = self[npos]
            that_terrain = that_tile[sori + 3 - that_ori]
            that_is_lake = all([t is Terrain.WATER for t in that_tile])

            match = this_terrain is that_terrain
            terrains = (this_terrain, that_terrain)
            water = Terrain.WATER in terrains
            train = Terrain.TRAIN in terrains
            station = Terrain.STATION in terrains
            lake = this_is_lake or that_is_lake

            if water and not (lake or station) and not match:
                return False

            if train and not station and not match:
                return False

        return True

    def valid_open_positions(self, tile):
        return {
            pos
            for pos in self.open_positions()
            for ori in range(6)
            if self.is_valid_position(tile, pos, ori)
        }

    def is_ruined_position(self, pos):
        tile, ori = self[pos]
        for sori, npos in self.neighbors(pos):
            this_terrain = tile[sori - ori]
            this_is_lake = all([t is Terrain.WATER for t in tile])

            that_tile, that_ori = self[npos]
            that_terrain = that_tile[sori + 3 - that_ori]
            that_is_lake = all([t is Terrain.WATER for t in that_tile])

            match = this_terrain is that_terrain
            terrains = (this_terrain, that_terrain)
            grass = Terrain.GRASS in terrains
            station = Terrain.STATION in terrains
            lake = this_is_lake or that_is_lake
            water_match = (grass and (station or lake)) or (station and lake)

            if not match and not water_match:
                return True

        return False
