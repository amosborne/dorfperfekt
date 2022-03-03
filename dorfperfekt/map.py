from collections import defaultdict
from collections.abc import MutableMapping

from .tile import Terrain, Tile

OFFSETS = set(zip(range(6), [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]))


class Map(MutableMapping):
    def __init__(self):
        self.tiles = {(0, 0): (Tile.from_string("g"), 0)}

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

    def neighbors(self, pos, existing=True):
        npos = lambda opos: (pos[0] + opos[0], pos[1] + opos[1])
        neighbors = {(ori, npos(opos)) for ori, opos in OFFSETS}
        real_neighbors = {(ori, npos) for ori, npos in neighbors if npos in self}
        open_neighbors = neighbors - real_neighbors
        return real_neighbors if existing else open_neighbors

    def open_positions(self):
        return {pos for cpos in self for _, pos in self.neighbors(cpos, existing=False)}

    def is_valid_placement(self, tile, pos, ori):
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

            if water and not (lake or station or match):
                return False

            if train and not (station or match):
                return False

        return True

    def valid_open_positions(self, tile):
        return {
            pos
            for pos in self.open_positions()
            for ori in range(6)
            if self.is_valid_placement(tile, pos, ori)
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
            water = Terrain.WATER in terrains
            train = Terrain.TRAIN in terrains
            station = Terrain.STATION in terrains
            lake = this_is_lake or that_is_lake
            water_match = (grass and (station or lake)) or (station and water)
            train_match = station and train
            perfect = match or water_match or train_match

            if not perfect:
                return True

        return False

    def rate_placement(self, tile, pos, ori):
        # A placement's rating is a tuple -- lower numbers are better.
        #  1. (+) Number of tiles newly ruined by the placement (includes self).
        #  2. (-) Number of perfect connections to train or water.
        #  3. (+) Number of new open positions for future placements.

        pre_ruined = sum(map(self.is_ruined_position, self))
        pre_open = len(self.open_positions())

        self[pos] = (tile, ori)

        post_ruined = sum(map(self.is_ruined_position, self))
        post_open = len(self.open_positions())

        del self[pos]

        tiles_newly_ruined = post_ruined - pre_ruined
        new_open_positions = post_open - pre_open

        perfect_wts_conns = 0
        for sori, npos in self.neighbors(pos):
            this_terrain = tile[sori - ori]
            this_is_lake = all([t is Terrain.WATER for t in tile])

            that_tile, that_ori = self[npos]
            that_terrain = that_tile[sori + 3 - that_ori]
            that_is_lake = all([t is Terrain.WATER for t in that_tile])

            match = this_terrain is that_terrain
            terrains = (this_terrain, that_terrain)
            grass = Terrain.GRASS in terrains
            water = Terrain.WATER in terrains
            train = Terrain.TRAIN in terrains
            station = Terrain.STATION in terrains
            lake = this_is_lake or that_is_lake
            water_match = (grass and (station or lake)) or (station and water)
            train_match = station and train
            perfect = match or water_match or train_match

            if perfect and (train or water or station):
                perfect_wts_conns += 1

        return (tiles_newly_ruined, -perfect_wts_conns, new_open_positions)

    def rate_position(self, tile, pos):
        rates = defaultdict(set)
        for ori in range(6):
            rates[self.rate_placement(tile, pos, ori)].add((pos, ori))

        scores = sorted(rates)
        return scores[0], rates[scores[0]]

    def suggest_placements(self, tile):
        rates = defaultdict(set)
        for pos in self.valid_open_positions(tile):
            score, placements = self.rate_position(tile, pos)
            rates[score] |= placements

        scores = sorted(rates)
        return rates[scores[0]]
