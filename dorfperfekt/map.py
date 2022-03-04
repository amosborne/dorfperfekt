from collections import defaultdict
from collections.abc import MutableMapping

from .tile import Terrain, Tile

OFFSETS = set(zip(range(6), [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]))

RESTRICTED_TERRAINS = {Terrain.WATER, Terrain.TRAIN}
RESTRICTED_EXCEPTIONS = {
    frozenset({Terrain.WATER, Terrain.STATION}),
    frozenset({Terrain.WATER, Terrain.COAST}),
    frozenset({Terrain.TRAIN, Terrain.STATION}),
}
PERFECT_ADDITIONS = {
    frozenset({Terrain.WATER, Terrain.STATION}),
    frozenset({Terrain.WATER, Terrain.COAST}),
    frozenset({Terrain.TRAIN, Terrain.STATION}),
    frozenset({Terrain.COAST, Terrain.GRASS}),
    frozenset({Terrain.COAST, Terrain.STATION}),
    frozenset({Terrain.GRASS, Terrain.STATION}),
}


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
            that_tile, that_ori = self[npos]
            that_terrain = that_tile[sori + 3 - that_ori]
            terrains = {this_terrain, that_terrain}

            matching = this_terrain is that_terrain
            restricted = not RESTRICTED_TERRAINS.isdisjoint(terrains)
            excepted = terrains in RESTRICTED_EXCEPTIONS

            if restricted and not (matching or excepted):
                return False

        return True

    def is_ruined_position(self, pos):
        tile, ori = self[pos]
        for sori, npos in self.neighbors(pos):
            this_terrain = tile[sori - ori]
            that_tile, that_ori = self[npos]
            that_terrain = that_tile[sori + 3 - that_ori]
            terrains = {this_terrain, that_terrain}

            matching = this_terrain is that_terrain
            accepted = terrains in PERFECT_ADDITIONS

            if not (matching or accepted):
                return True

        return False

    def rate_placement(self, tile, pos, ori):
        # A placement's rating is a tuple -- lower numbers are better.
        #  1. (+) Number of tiles newly ruined by the placement (includes self).
        #  2. (-) Number of perfect restricted connections (train or water).
        #  3. (+) Number of new open positions for future placements.

        if not self.is_valid_placement(tile, pos, ori):
            return None

        pre_ruined = sum(map(self.is_ruined_position, self))
        pre_open = len(self.open_positions())

        self[pos] = (tile, ori)

        post_ruined = sum(map(self.is_ruined_position, self))
        post_open = len(self.open_positions())

        del self[pos]

        tiles_newly_ruined = post_ruined - pre_ruined
        new_open_positions = post_open - pre_open

        perfect_restricted_conns = 0
        for sori, npos in self.neighbors(pos):
            this_terrain = tile[sori - ori]
            that_tile, that_ori = self[npos]
            that_terrain = that_tile[sori + 3 - that_ori]
            terrains = {this_terrain, that_terrain}

            restricted = not RESTRICTED_TERRAINS.isdisjoint(terrains)
            matching = this_terrain is that_terrain
            accepted = terrains in PERFECT_ADDITIONS

            if restricted and (matching or accepted):
                perfect_restricted_conns += len(
                    RESTRICTED_TERRAINS.intersection(terrains)
                )

        return (tiles_newly_ruined, -perfect_restricted_conns, new_open_positions)

    def rate_position(self, tile, pos):
        rates = defaultdict(set)
        for ori in range(6):
            rate = self.rate_placement(tile, pos, ori)
            if rate is not None:
                rates[rate].add((pos, ori))

        if not rates:
            return None

        scores = sorted(rates)
        return scores[0], rates[scores[0]]

    def suggest_placements(self, tile):
        rates = defaultdict(set)
        for pos in self.open_positions():
            rate = self.rate_position(tile, pos)
            if rate is not None:
                score, placements = rate
                rates[score] |= placements

        scores = sorted(rates)
        return rates[scores[0]]
