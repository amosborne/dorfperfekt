from dorfperfekt.tile import Terrain, Tile


def test_to_string():
    tile = Tile(
        [
            Terrain.GRASS,
            Terrain.FOREST,
            Terrain.RANCH,
            Terrain.DWELLING,
            Terrain.WATER,
            Terrain.TRAIN,
        ]
    )
    assert tile.string == "GFRDWT"
    assert tile[1] is tile[7] is Terrain.FOREST
    assert len(tile) == 6


def test_from_string():
    tile = Tile.from_string("gfrrrr")
    assert tile.string == "GFRRRR"


def test_from_letter():
    tile = Tile.from_string("w")
    assert tile.string == "WWWWWW"


def test_equality():
    tile1 = Tile.from_string("gfrrrr")
    tile2 = Tile.from_string("frrrrg")
    assert tile1 == tile2
