import re
from collections import OrderedDict, defaultdict, namedtuple

from .tile import Terrain, Tile, terrains2string

OFFSETS = [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]

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


MapTile = namedtuple("MapTile", "adj terrains")


def new_maptile(pos, tile, ori):
    adj = [(pos[0] + off[0], pos[1] + off[1]) for off in OFFSETS]
    terrains = tuple([tile[k - ori] for k in range(6)])
    return MapTile(adj, terrains)


class TileMap:
    def __init__(self):
        self.tiles = OrderedDict()
        self.counter = defaultdict(int)
        self.ruined = list()
        self.place(pos=(0, 0), tile=Tile.from_string("G"), ori=0)

    @staticmethod
    def from_file(filepath):
        tilemap = TileMap()
        tilemap.remove(pos=(0, 0))
        pattern = r"^([GFRDWSTC]{6}) (-?\d+) (-?\d+)$"
        with open(filepath) as file:
            for line in file:
                match = re.match(pattern, line)
                tile = Tile.from_string(match[1])
                pos = (int(match[2]), int(match[3]))
                tilemap.place(pos, tile, 0)

        return tilemap

    def write_file(self, filepath):
        with open(filepath, "w") as file:
            fstring = "{} {:d} {:d}\n"
            for pos, maptile in self.tiles.items():
                string = terrains2string(maptile.terrains)
                line = fstring.format(string, *pos)
                file.write(line)

    def place(self, pos, tile, ori):
        assert self.is_valid_placement(pos, tile, ori)
        maptile = new_maptile(pos, tile, ori)
        self.tiles[pos] = maptile
        self.counter[tile] += 1

        ruined, adj_ruined = self.is_ruined_by_placement(pos, tile, ori)
        if ruined:
            self.ruined.append(pos)
        for adj_pos, adj_ruin in zip(maptile.adj, adj_ruined):
            if adj_ruin:
                self.ruined.append(adj_pos)

        return maptile

    def remove(self, pos):
        maptile = self.tiles.pop(pos)
        string = terrains2string(maptile.terrains)
        tile = Tile.from_string(string)
        self.counter[tile] -= 1
        if not self.counter[tile]:
            del self.counter[tile]

        ruined, adj_ruined = self.is_ruined_by_placement(pos, tile, 0)
        if ruined:
            self.ruined.remove(pos)
        for adj_pos, adj_ruin in zip(maptile.adj, adj_ruined):
            if adj_ruin:
                self.ruined.remove(adj_pos)

    def adj_terrains(self, pos):
        adj_terrains = [None] * 6
        adj = [(pos[0] + off[0], pos[1] + off[1]) for off in OFFSETS]
        for ori, adj_pos in enumerate(adj):
            if adj_pos in self.tiles:
                adj_maptile = self.tiles[adj_pos]
                adj_terrains[ori] = adj_maptile.terrains[(ori + 3) % 6]

        return tuple(adj_terrains)

    def is_valid_placement(self, pos, tile, ori):
        if pos in self.tiles:
            return False

        maptile = new_maptile(pos, tile, ori)
        for terrains in zip(self.adj_terrains(pos), maptile.terrains):
            if None in terrains:
                continue

            matching = terrains[0] is terrains[1]
            restricted = not RESTRICTED_TERRAINS.isdisjoint(set(terrains))
            excepted = set(terrains) in RESTRICTED_EXCEPTIONS

            if restricted and not (matching or excepted):
                return False

        return True

    def is_ruined_by_placement(self, pos, tile, ori):
        is_ruined = False
        is_adj_ruined = [False] * 6
        maptile = new_maptile(pos, tile, ori)
        terrain_pairs = zip(self.adj_terrains(pos), maptile.terrains)
        for ori, terrains in enumerate(terrain_pairs):
            if None in terrains:
                continue

            matching = terrains[0] is terrains[1]
            accepted = set(terrains) in PERFECT_ACCEPTIONS

            if not (matching or accepted):
                is_ruined = True
                is_adj_ruined[ori] = True

        return is_ruined, is_adj_ruined

    def count_alternates(self, pos):
        count = 0
        for tile in self.counter:
            for ori in range(6):
                if not self.is_valid_placement(pos, tile, ori):
                    continue

                if not self.is_ruined_by_placement(pos, tile, ori)[0]:
                    count += self.counter[tile]
                    break

        return count

    def rate_placement(self, pos, tile, ori):
        # A placement's rating is a tuple where lower numbers are better.
        #  1. (+) Number of tiles newly ruined by the placement (includes self).
        #  2. (+) Sum of all perfect alternate tiles for open adjacencies.

        if not self.is_valid_placement(pos, tile, ori):
            return None

        ruined, adj_ruined = self.is_ruined_by_placement(pos, tile, ori)
        newly_ruined = ruined + adj_ruined.count(True)

        maptile = self.place(pos, tile, ori)

        adj_alternates = 0
        for adj_pos in maptile.adj:
            adj_alternates += self.count_alternates(adj_pos)

        self.remove(pos)

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
        openpos = set()
        for maptile in self.tiles.values():
            for adj in maptile.adj:
                if adj not in self.tiles:
                    openpos.add(adj)

        rates = defaultdict(set)
        for pos in openpos:
            rate = self.rate_position(pos, tile)
            if rate is not None:
                score, oris = rate
                rates[score] |= {(pos, ori) for ori in oris}

        return [rates[score] for score in sorted(rates)]
