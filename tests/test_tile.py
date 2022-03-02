from dorfperfekt.tile import Terrain, Tile


def test_to_string():
    tile = Tile(
        [
            Terrain.GRASS,
            Terrain.FOREST,
            Terrain.RANCH,
            Terrain.RANCH,
            Terrain.RANCH,
            Terrain.RANCH,
        ]
    )
    assert tile.to_string() == "GFRRRR"
    assert tile[1] is Terrain.FOREST
    assert tile[7] is Terrain.FOREST
    assert len(tile) == 6


def test_from_string():
    tile = Tile.from_string("gfrrrr")
    assert tile.to_string() == "GFRRRR"


def test_from_letter():
    tile = Tile.from_string("w")
    assert tile.to_string() == "WWWWWW"


def test_equality():
    tile1 = Tile.from_string("gfrrrr")
    tile2 = Tile.from_string("frrrrg")
    assert tile1 == tile2
