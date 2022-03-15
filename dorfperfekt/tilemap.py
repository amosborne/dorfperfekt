import re
from collections import OrderedDict, defaultdict, namedtuple
from collections.abc import MutableMapping
from functools import cache

from .tile import Tile, validate_terrains, validate_tiles


class InvalidTilePlacementError(ValueError):
    pass


OFFSETS = [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]


@cache
def adjacent_positions(pos):
    return [(pos[0] + off[0], pos[1] + off[1]) for off in OFFSETS]


class TileMap(MutableMapping):
    def __init__(self):
        self.tiles = OrderedDict()
        self.counter = defaultdict(int)
        self.ruined = list()
        self.open = set([(0, 0)])
        self[0, 0] = Tile("g")

    @staticmethod
    def from_file(filepath):
        tilemap = TileMap()
        del tilemap[0, 0]
        pattern = r"^([GFRDWSTC]{6}) (-?\d+) (-?\d+) (-?\d+)$"
        with open(filepath) as file:
            for line in file:
                match = re.match(pattern, line)
                tile = Tile(match[1])
                tile.ori = int(match[2])
                pos = (int(match[3]), int(match[4]))
                tilemap[pos] = tile

        return tilemap

    def write_file(self, filepath):
        with open(filepath, "w") as file:
            fstring = "{} {:d} {:d} {:d}\n"
            for pos, tile in self.tiles.items():
                line = fstring.format(tile.string, tile.ori, *pos)
                file.write(line)

    def __setitem__(self, key, value):
        outer = self.outer_tile(key)
        this_ori = (value.ori - outer.ori) % 6
        is_valid, is_perfect = validate_tiles(value, outer)[this_ori]

        if not (is_valid and key in self.open):
            raise InvalidTilePlacementError

        self.tiles[key] = value
        self.counter[value.copy()] += 1

        adj = adjacent_positions(key)

        if is_perfect.count(False):
            adj = adj[(6 - this_ori) :] + adj[: (6 - this_ori)]
            for adj_pos, perfect in zip(adj, is_perfect):
                if perfect is False:
                    self.ruined.append(key)
                    self.ruined.append(adj_pos)

        self.open.remove(key)
        [self.open.add(pos) for pos in adj if pos not in self]

    def __getitem__(self, key):
        return self.tiles[key]

    def __delitem__(self, key):
        inner = self[key]
        outer = self.outer_tile(key)
        this_ori = (inner.ori - outer.ori) % 6
        _, is_perfect = validate_tiles(inner, outer)[this_ori]

        del self.tiles[key]
        self.counter[inner] -= 1
        if not self.counter[inner]:
            del self.counter[inner]

        adj = adjacent_positions(key)

        if is_perfect.count(False):
            adj = adj[(6 - this_ori) :] + adj[: (6 - this_ori)]
            for adj_pos, perfect in zip(adj, is_perfect):
                if perfect is False:
                    self.ruined.remove(key)
                    self.ruined.remove(adj_pos)

        self.open.add(key)
        for adj_pos in [pos for pos in adj if pos not in self]:
            adj = adjacent_positions(adj_pos)
            found = any([pos in self for pos in adj])
            if not found:
                self.open.discard(adj_pos)

    def __iter__(self):
        return self.tiles.__iter__()

    def __len__(self):
        return len(self.tiles)

    def outer_tile(self, pos):
        terrains = ["o"] * 6
        for ori, adj in enumerate(adjacent_positions(pos)):
            if adj in self:
                tile = self[adj]
                terrains[ori] = tile[(ori - tile.ori + 3) % 6].name[0]

        return Tile("".join(terrains))

    def perfect_alternates(self, pos):
        count = 0
        pre_ruined = len(set(self.ruined))
        for tile, subcount in self.counter.items():
            for ori in range(6):
                try:
                    tile.ori = ori
                    self[pos] = tile
                    post_ruined = len(set(self.ruined))
                    del self[pos]
                    newly_ruined = post_ruined - pre_ruined
                    if not newly_ruined:
                        count += subcount
                        break
                except InvalidTilePlacementError:
                    pass

        return count

    def rate_placement(self, tile, pos):
        pre_ruined = len(set(self.ruined))

        self[pos] = tile

        secondorder_alternates = sum(
            [
                self.perfect_alternates(adj)
                for adj in adjacent_positions(pos)
                if adj in self.open
            ]
        )

        post_ruined = len(set(self.ruined))

        del self[pos]

        newly_ruined = post_ruined - pre_ruined

        alternates = self.perfect_alternates(pos)

        return newly_ruined, alternates, secondorder_alternates

    def suggest_placements(self, string):
        placements = defaultdict(set)
        for pos in self.open:
            for ori in range(6):
                try:
                    tile = Tile(string)
                    tile.ori = ori
                    score = self.rate_placement(tile, pos)
                    placements[score].add((pos, tile))
                except InvalidTilePlacementError:
                    pass

        sorted_placements = [placements[key] for key in sorted(placements)]

        return sorted_placements
