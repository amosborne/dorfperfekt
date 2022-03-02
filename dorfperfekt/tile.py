from collections.abc import Sequence
from enum import Enum

Terrain = Enum("Terrain", "GRASS FOREST RANCH DWELLING WATER STATION TRAIN")


class Tile(Sequence):
    length = 6

    def __init__(self, terrain):
        assert len(terrain) == Tile.length
        self.terrain = terrain

    @staticmethod
    def from_string(string):
        string = string.upper()
        string = string * Tile.length if len(string) == 1 else string
        terrain = {t.name[0]: t for t in Terrain}
        return Tile([terrain[s] for s in string])

    def to_string(self):
        return "".join([terrain.name[0] for terrain in self.terrain])

    def __repr__(self):
        return self.to_string()

    def __eq__(self, other):
        return self.to_string() in other.to_string() * 2

    def __getitem__(self, key):
        return self.terrain[key]

    def __len__(self):
        return Tile.length
