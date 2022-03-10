import re
from collections import OrderedDict, defaultdict, namedtuple
from collections.abc import MutableMapping

from .tile import Terrain, Tile

OFFSETS = {0: (1, 0), 1: (0, 1), 2: (-1, 1), 3: (-1, 0), 4: (0, -1), 5: (1, -1)}

RESTRICTED_TERRAINS = {Terrain.WATER, Terrain.TRAIN}
RESTRICTED_EXCEPTIONS = [
    {Terrain.WATER, Terrain.STATION},
    {Terrain.WATER, Terrain.COAST},
    {Terrain.TRAIN, Terrain.STATION},
]
PERFECT_ACCEPTIONS = [
    {Terrain.WATER, Terrain.STATION},
    {Terrain.WATER, Terrain.COAST},
    {Terrain.TRAIN, Terrain.STATION},
    {Terrain.COAST, Terrain.GRASS},
    {Terrain.COAST, Terrain.STATION},
    {Terrain.GRASS, Terrain.STATION},
]

MapTile = namedtuple("MapTile", "tile ori")


class TileMap(MutableMapping):
    def __init__(self):
        self.tilemap = OrderedDict()
        self.openpos = {(0, 0)}
        self.counter = defaultdict(int)
        self.ruined = set()
        self[0, 0] = MapTile(tile=Tile.from_string("g"), ori=0)

    def __getitem__(self, key):
        return self.tilemap[key]

    def __setitem__(self, key, item):
        self.openpos.discard(key)
        self.counter[item.tile] += 1
        self.tilemap[key] = item

        if self.is_ruined_position(key):
            self.ruined.add(key)

        for offset in OFFSETS.values():
            pos = key[0] + offset[0], key[1] + offset[1]
            if pos not in self:
                self.openpos.add(pos)
            elif self.is_ruined_position(pos):
                self.ruined.add(pos)

    def __delitem__(self, key):
        self.counter[self.tilemap[key].tile] -= 1
        self.openpos.add(key)
        del self.tilemap[key]
        self.ruined.discard(key)

        for offset in OFFSETS.values():
            pos = key[0] + offset[0], key[1] + offset[1]

            if pos not in self:
                for offset2 in OFFSETS.values():
                    pos2 = pos[0] + offset2[0], pos[1] + offset2[1]
                    adj_exists = pos2 in self.tilemap
                    if adj_exists:
                        break

                if not adj_exists:
                    self.openpos.remove(pos)

            elif not self.is_ruined_position(pos):
                self.ruined.discard(pos)

    def __iter__(self):
        return self.tilemap.__iter__()

    def __len__(self):
        return len(self.tilemap)

    @staticmethod
    def from_file(filepath):
        tilemap = TileMap()
        pattern = r"^([GFRDWSTC]{6}) (-?\d+) (-?\d+) ([0-6])$"
        with open(filepath) as file:
            for line in file:
                match = re.match(pattern, line)
                tile = Tile.from_string(match[1])
                pos = (int(match[2]), int(match[3]))
                ori = int(match[4])
                tilemap[pos] = MapTile(tile=tile, ori=ori)

        return tilemap

    def write_file(self, filepath):
        with open(filepath, "w") as file:
            fstring = "{} {:d} {:d} {:d}\n"
            for pos, (tile, ori) in self.items():
                line = fstring.format(tile.string, *pos, ori)
                file.write(line)

    def adjacent_terrains(self, pos):
        adj_terrains = [None] * 6
        for ori, offset in OFFSETS.items():
            adj_pos = pos[0] + offset[0], pos[1] + offset[1]
            if adj_pos in self:
                adj_maptile = self[adj_pos]
                adj_terrains[ori] = adj_maptile.tile[ori - adj_maptile.ori + 3]

        return tuple(adj_terrains)

    def is_valid_placement(self, pos, tile, ori):
        adj_terrains = self.adjacent_terrains(pos)
        pos_terrains = tuple([tile[k - ori] for k in range(6)])
        for terrains in zip(adj_terrains, pos_terrains):
            if None in terrains:
                continue

            matching = terrains[0] is terrains[1]
            restricted = not RESTRICTED_TERRAINS.isdisjoint(set(terrains))
            excepted = set(terrains) in RESTRICTED_EXCEPTIONS

            if restricted and not (matching or excepted):
                return False

        return True

    def is_ruined_position(self, pos):
        adj_terrains = self.adjacent_terrains(pos)
        tile, ori = self[pos]
        pos_terrains = tuple([tile[k - ori] for k in range(6)])
        for terrains in zip(adj_terrains, pos_terrains):
            if None in terrains:
                continue

            matching = terrains[0] is terrains[1]
            accepted = set(terrains) in PERFECT_ACCEPTIONS

            if not (matching or accepted):
                return True

        return False

    def count_alternates(self, pos):
        count = 0
        for tile in self.counter:
            for ori in range(6):
                if not self.is_valid_placement(pos, tile, ori):
                    continue

                self[pos] = MapTile(tile, ori)

                if pos not in self.ruined:
                    count += self.counter[tile]
                    del self[pos]
                    break

                del self[pos]

        return count

    def rate_placement(self, pos, tile, ori):
        # A placement's rating is a tuple where lower numbers are better.
        #  1. (+) Number of tiles newly ruined by the placement (includes self).
        #  2. (+) Sum of all perfect alternate tiles for open adjacencies.

        if not self.is_valid_placement(pos, tile, ori):
            return None

        ruined_prior = len(self.ruined)

        self[pos] = MapTile(tile, ori)

        ruined_after = len(self.ruined)

        adj_alternates = 0
        for offset in OFFSETS.values():
            adj = pos[0] + offset[0], pos[1] + offset[1]
            if adj in self.openpos:
                adj_alternates += self.count_alternates(adj)

        del self[pos]

        newly_ruined = ruined_after - ruined_prior

        return newly_ruined, adj_alternates

    def rate_position(self, pos, tile):
        rates = defaultdict(set)
        for ori in range(6):
            rate = self.rate_placement(pos, tile, ori)
            if rate is not None:
                rates[rate].add(ori)

        if not rates:
            return None

        scores = sorted(rates)
        (newly_ruined, adj_alternates) = scores[0]
        alternates = self.count_alternates(pos)

        return (newly_ruined, alternates, adj_alternates), rates[scores[0]]

    def suggest_placements(self, tile):
        rates = defaultdict(set)
        for pos in self.openpos:
            rate = self.rate_position(pos, tile)
            if rate is not None:
                score, oris = rate
                rates[score] |= {(pos, ori) for ori in oris}

        return [rates[score] for score in sorted(rates)]
