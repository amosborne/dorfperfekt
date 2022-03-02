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


def test_from_string():
    tile = Tile.from_string("gfrrrr")
    assert tile.to_string() == "GFRRRR"


def test_equality():
    tile1 = Tile.from_string("gfrrrr")
    tile2 = Tile.from_string("frrrrg")
    assert tile1 == tile2
