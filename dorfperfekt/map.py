from collections import defaultdict, namedtuple
from collections.abc import MutableMapping

from .tile import Tile

Placement = namedtuple("Placement", "tile ori")


class Map(MutableMapping):
    def __init__(self):
        self.tiles = defaultdict()
        self.tiles[0, 0] = Placement(Tile.from_string("g"), 0)

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
