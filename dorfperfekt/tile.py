from collections.abc import Sequence
from enum import Enum
from functools import cache

Terrain = Enum("Terrain", "GRASS FOREST RANCH DWELLING WATER STATION TRAIN COAST OPEN")

TERRAINS = {terrain.name[0]: terrain for terrain in Terrain}

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


class Tile(Sequence):
    # A Tile is a sequence of six terrains. Every Tile has a default
    # orientation, as determined by the alphabetical ordering of its
    # definition string.
    #
    # Each index of a Tile is a terrain. The index is counted against
    # the default orientation. The Tile also stores the true orientation
    # as a separate field, which can be added to the index.

    def __init__(self, string):
        string = string.upper()
        string = string * 6 if len(string) == 1 else string
        assert len(string) == 6

        self.string = string
        self.ori = 0
        for ori in range(6):
            newstring = string[ori:] + string[:ori]
            if newstring < self.string:
                self.string = newstring
                self.ori = ori

        self.hash = hash(self.string)
        self.terrain = [TERRAINS[letter] for letter in self.string]

    def copy(self):
        return Tile(self.string)

    def __repr__(self):
        return self.string

    def __eq__(self, other):
        return self.hash == hash(other)

    def __getitem__(self, key):
        return self.terrain[key % 6]

    def __iter__(self):
        return self.terrain.__iter__()

    def __len__(self):
        return 6

    def __hash__(self):
        return self.hash


@cache
def validate_terrains(terrains):
    # Compare two terrains and return a tuple (is_valid, is_perfect).

    if Terrain.OPEN in terrains:
        return True, None

    matching = len(terrains) == 1
    restricted = not terrains.isdisjoint(RESTRICTED_TERRAINS)
    excepted = terrains in RESTRICTED_EXCEPTIONS

    accepted = terrains in PERFECT_ACCEPTIONS
    is_invalid = restricted and not (matching or excepted)
    is_perfect = matching or accepted

    return not is_invalid, is_perfect


@cache
def validate_tiles(inner, outer):
    # Compare two tiles (inner versus outer) and return a list.
    # Each element corresponds to the relative orientation of the tiles.
    # Each element is a tuple (is_valid, is_perfect) where is_perfect
    # is a tuple of the validate_terrains() is_perfect result at each side.
    #
    # The is_perfect tuple will contain None if the outer tile is open.

    ret = [None] * 6
    for ori in range(6):
        tile_is_valid = True
        is_perfect = [None] * 6
        for idx in range(6):
            terrains = frozenset((inner[idx - ori], outer[idx]))
            is_valid, is_perfect[idx] = validate_terrains(terrains)
            tile_is_valid &= is_valid

        ret[ori] = (tile_is_valid, tuple(is_perfect))

    return ret
