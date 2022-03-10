from collections.abc import Sequence
from enum import Enum

Terrain = Enum("Terrain", "GRASS FOREST RANCH DWELLING WATER STATION TRAIN COAST")


class Tile(Sequence):
    def __init__(self, terrain):
        assert len(terrain) == 6
        self.terrain = terrain

        self.string = "".join([terrain.name[0] for terrain in self.terrain])

        hashstring = self.string
        for idx in range(6):
            newstring = self.string[idx:] + self.string[:idx]
            if newstring < hashstring:
                hashstring = newstring

        self.hash = hash(hashstring)

    @staticmethod
    def from_string(string):
        string = string.upper()
        string = string * 6 if len(string) == 1 else string
        terrain = {t.name[0]: t for t in Terrain}
        return Tile([terrain[s] for s in string])

    def __repr__(self):
        return self.string

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __getitem__(self, key):
        return self.terrain[key % 6]

    def __iter__(self):
        return self.terrain.__iter__()

    def __len__(self):
        return 6

    def __hash__(self):
        return self.hash
