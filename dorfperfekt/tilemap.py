import re
from collections import Counter, OrderedDict
from collections.abc import MutableMapping
from math import inf
from multiprocessing import Pool, cpu_count

from cachetools.func import lru_cache

from .tile import Terrain, Tile, string2tile, terrains2tile, tile2string, validate_tiles


class InvalidTilePlacementError(ValueError):
    pass


OFFSETS = [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]

# FUTURE IDEAS:
#   1. self.ruined = set()
#   3. self.solve(terrains, thresh1=1, thresh2=1)


@lru_cache(maxsize=64)
def adjacent_positions(pos):
    return [(pos[0] + off[0], pos[1] + off[1]) for off in OFFSETS]


class TileMap(MutableMapping):
    def __init__(self):
        self.tiles = OrderedDict()
        self.counter = Counter()
        self.ruined = list()
        self.open = set([(0, 0)])
        self[0, 0] = string2tile("g")

    @staticmethod
    def from_file(filepath):
        tilemap = TileMap()
        del tilemap[0, 0]
        pattern = r"^([GFRDWSTC]{6}) (-?\d+) (-?\d+)$"
        with open(filepath) as file:
            for line in file:
                match = re.match(pattern, line)
                tile = string2tile(match[1])
                pos = (int(match[2]), int(match[3]))
                tilemap[pos] = tile

        return tilemap

    def write_file(self, filepath):
        with open(filepath, "w") as file:
            fstring = "{} {:d} {:d}\n"
            for pos, tile in self.tiles.items():
                line = fstring.format(tile2string(tile), *pos)
                file.write(line)

    def __setitem__(self, pos, tile):
        outer = self.outer_tile(pos)
        valid, perfect = validate_tiles(tile, outer)

        if not (valid and pos in self.open):
            raise InvalidTilePlacementError

        self.tiles[pos] = tile
        self.open.remove(pos)
        self.counter[tile.terrains] += 1

        adj = adjacent_positions(pos)

        for adj_pos, adj_perfect in zip(adj, perfect):
            if adj_perfect is False:
                self.ruined.extend([pos, adj_pos])

            if adj_pos not in self:
                self.open.add(adj_pos)

    def __getitem__(self, pos):
        return self.tiles[pos]

    def __delitem__(self, pos):
        inner = self[pos]
        outer = self.outer_tile(pos)
        _, perfect = validate_tiles(inner, outer)

        del self.tiles[pos]
        self.open.add(pos)

        count = self.counter[inner.terrains]
        if count == 1:
            del self.counter[inner.terrains]
        else:
            self.counter[inner.terrains] = count - 1

        adj = adjacent_positions(pos)

        for adj_pos, adj_perfect in zip(adj, perfect):
            if adj_perfect is False:
                self.ruined.remove(pos)
                self.ruined.remove(adj_pos)

            if adj_pos not in self:
                adj_adj = adjacent_positions(adj_pos)
                found = any([pos in self for pos in adj_adj])
                if not found:
                    self.open.discard(adj_pos)

    def __iter__(self):
        return self.tiles.__iter__()

    def __len__(self):
        return len(self.tiles)

    def outer_tile(self, pos):
        terrains = [Terrain.OPEN] * 6
        for ori, adj in enumerate(adjacent_positions(pos)):
            if adj in self:
                tile = self[adj]
                terrains[ori] = tile.terrains[(ori - tile.ori + 3) % 6]

        return terrains2tile(tuple(terrains))

    def perfect_alternates(self, pos, thresh=1):
        count = 0
        pre_ruined = len(set(self.ruined))
        for terrains, subcount in self.counter.items():
            if subcount < thresh:
                continue

            for ori in range(6):
                try:
                    self[pos] = Tile(terrains, ori)
                    post_ruined = len(set(self.ruined))
                    del self[pos]
                    newly_ruined = post_ruined - pre_ruined
                    if not newly_ruined:
                        count += subcount
                        break
                except InvalidTilePlacementError:
                    pass

        return count

    def score_tile(self, pos, tile, thresh=1):
        pre_ruined = len(set(self.ruined))

        self[pos] = tile

        open_adj = [adj for adj in adjacent_positions(pos) if adj in self.open]
        secondorder_alternates = (
            min([self.perfect_alternates(adj, thresh) for adj in open_adj])
            if open_adj
            else inf
        )

        post_ruined = len(set(self.ruined))

        del self[pos]

        newly_ruined = post_ruined - pre_ruined

        alternates = self.perfect_alternates(pos, thresh)

        return newly_ruined, alternates, -secondorder_alternates

    def score_pos(self, args):
        pos, terrains, thresh = args
        scores = set()
        for ori in range(6):
            try:
                tile = Tile(terrains, ori)
                score = self.score_tile(pos, tile, thresh)
                scores.add((score, tile))
            except InvalidTilePlacementError:
                pass

        return pos, scores

    def scores(self, terrains, thresh=1):
        args = ((pos, terrains, thresh) for pos in self.open)
        with Pool(cpu_count() // 2) as pool:
            for score in pool.imap_unordered(self.score_pos, args):
                yield score
