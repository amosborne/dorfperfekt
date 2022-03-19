from collections import namedtuple

from aenum import OrderedEnum, unique
from cachetools.func import lfu_cache


class InvalidTileDefinitionError(ValueError):
    pass


@unique
class Terrain(OrderedEnum):
    GRASS = "G"
    FOREST = "F"
    RANCH = "R"
    DWELLING = "D"
    WATER = "W"
    STATION = "S"
    TRAIN = "T"
    COAST = "C"
    OPEN = "O"


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

Tile = namedtuple("Tile", "terrains ori")


def string2tile(string):
    string = string.upper()
    string = string * 6 if len(string) == 1 else string

    try:
        terrains = tuple(Terrain(t) for t in string)
        return terrains2tile(terrains)
    except ValueError:
        raise InvalidTileDefinitionError


def terrains2tile(terrains):
    if len(terrains) != 6:
        raise InvalidTileDefinitionError

    final_terrains, final_ori = terrains, 0

    for rot_ori in range(1, 6):
        rot_terrains = tuple((*terrains[rot_ori:], *terrains[:rot_ori]))

        if rot_terrains < final_terrains:
            final_terrains, final_ori = rot_terrains, rot_ori

    return Tile(final_terrains, final_ori)


def tile2string(tile):
    string = "".join([t.value for t in tile.terrains])
    return string[-tile.ori :] + string[: -tile.ori]


class SettifyCacheArguments:
    def __init__(self, func):
        self.func = func

    def __call__(self, arg1, arg2):
        return self.func(frozenset((arg1, arg2)))

    def cache_info(self):
        return self.func.cache_info()


@SettifyCacheArguments
@lfu_cache(maxsize=64)
def validate_terrains(terrains):
    if Terrain.OPEN in terrains:
        return True, None

    matching = len(terrains) == 1
    restricted = not terrains.isdisjoint(RESTRICTED_TERRAINS)
    excepted = terrains in RESTRICTED_EXCEPTIONS

    accepted = terrains in PERFECT_ACCEPTIONS
    is_invalid = restricted and not (matching or excepted)
    is_perfect = matching or accepted

    return not is_invalid, is_perfect


@SettifyCacheArguments
@lfu_cache(maxsize=262144)
def validate_tiles(tiles):
    if len(tiles) == 1:
        return True, (True,) * 6

    else:
        is_perfect = [None] * 6
        inner, outer = tuple(tiles)
        for ori in range(6):
            inner_terrain = inner.terrains[(ori - inner.ori) % 6]
            outer_terrain = outer.terrains[(ori - outer.ori) % 6]
            is_valid, is_perfect[ori] = validate_terrains(inner_terrain, outer_terrain)

            if not is_valid:
                return False, None

        return True, tuple(is_perfect)
