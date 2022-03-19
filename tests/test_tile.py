import pytest

from dorfperfekt.tile import (
    InvalidTileDefinitionError,
    Terrain,
    string2tile,
    tile2string,
    validate_terrains,
    validate_tiles,
)


def test_tile():
    tile = string2tile("frdwtg")
    assert tile2string(tile) == "FRDWTG"
    assert tile2string(tile._replace(ori=0)) == "DWTGFR"
    assert tile2string(tile._replace(ori=-1)) == "WTGFRD"
    assert tile.ori == 2
    assert tile.terrains[0] is Terrain.DWELLING
    assert tile.terrains[2] is Terrain.TRAIN
    assert tile.terrains[(7 - tile.ori) % 6] is Terrain.RANCH


def test_from_letter():
    tile = string2tile("w")
    assert tile2string(tile) == "WWWWWW"


def test_equality():
    tile1 = string2tile("gfrrrr")
    tile2 = string2tile("frrrrg")
    assert tile1.terrains == tile2.terrains


def test_assertions():
    with pytest.raises(InvalidTileDefinitionError):
        string2tile("gr")

    with pytest.raises(InvalidTileDefinitionError):
        string2tile("k")


def test_validate_terrains():
    assert validate_terrains(Terrain.GRASS, Terrain.GRASS) == (True, True)
    assert validate_terrains(Terrain.GRASS, Terrain.COAST) == (True, True)
    assert validate_terrains(Terrain.GRASS, Terrain.WATER) == (False, False)
    assert validate_terrains(Terrain.WATER, Terrain.WATER) == (True, True)
    assert validate_terrains(Terrain.GRASS, Terrain.RANCH) == (True, False)
    assert validate_terrains(Terrain.WATER, Terrain.OPEN) == (True, None)


def test_validate_tiles():
    valid, perfect = validate_tiles(string2tile("dwwggr"), string2tile("cwrogd"))
    assert not valid and perfect is None

    valid, perfect = validate_tiles(string2tile("dwwggr"), string2tile("dcwrog"))
    assert valid and perfect == (True, True, True, False, None, False)
