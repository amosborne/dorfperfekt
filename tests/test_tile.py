import pytest

from dorfperfekt.tile import Terrain, Tile, validate_terrains, validate_tiles


def test_tile():
    tile = Tile("gfrdwt")
    assert tile.string == "DWTGFR"
    assert tile.ori == 3
    assert tile[1 + tile.ori] == tile[7 + tile.ori] == Terrain.FOREST
    assert tile[0] == Terrain.DWELLING
    assert tile[2] == Terrain.TRAIN


def test_from_letter():
    tile = Tile("w")
    assert tile.string == "WWWWWW"


def test_equality():
    tile1 = Tile("gfrrrr")
    tile2 = Tile("frrrrg")
    assert tile1 == tile2


def test_assertions():
    with pytest.raises(AssertionError):
        Tile("gr")


def test_validate_terrains():
    grass_to_grass = frozenset((Terrain.GRASS, Terrain.GRASS))
    assert (True, True) == validate_terrains(grass_to_grass)

    grass_to_coast = frozenset((Terrain.GRASS, Terrain.COAST))
    assert (True, True) == validate_terrains(grass_to_coast)

    grass_to_water = frozenset((Terrain.GRASS, Terrain.WATER))
    assert (False, False) == validate_terrains(grass_to_water)

    water_to_water = frozenset((Terrain.WATER, Terrain.WATER))
    assert (True, True) == validate_terrains(water_to_water)

    grass_to_ranch = frozenset((Terrain.GRASS, Terrain.RANCH))
    assert (True, False) == validate_terrains(grass_to_ranch)


def test_validate_tiles():
    ret = validate_tiles(inner=Tile("dwwggr"), outer=Tile("cwrogd"))
    assert ret[0] == (False, (False, True, False, None, True, False))
    assert ret[1] == (False, (False, False, False, None, True, False))

    inner = Tile("gfcggg")
    outer = Tile("ggggfg")
    ret = validate_tiles(inner, outer)
    this_ori = (inner.ori - outer.ori) % 6
    best_ori = (inner.ori - outer.ori + 3) % 6
    assert ret[this_ori] == (True, (False, True, True, False, True, True))
    assert ret[best_ori] == (True, (True, True, True, True, True, True))

    inner.ori = outer.ori + best_ori
    ret = validate_tiles(inner, outer)
    this_ori = (inner.ori - outer.ori) % 6
    assert ret[this_ori] == (True, (True, True, True, True, True, True))
