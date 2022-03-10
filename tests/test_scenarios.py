import filecmp
import os

from dorfperfekt.tile import Tile
from dorfperfekt.tilemap import TileMap


def test_perfect_station():
    filein = "tests/scenarios/perfect_station.txt"
    fileout = "tests/test_perfect_station.txt"
    tilemap = TileMap.from_file(filein)
    placements = tilemap.suggest_placements(Tile.from_string("s"))
    assert (2, -1) in {pos for pos, _ in placements[0]}
    tilemap.write_file(fileout)
    assert filecmp.cmp(filein, fileout)
    os.remove(fileout)


def test_invalid_position():
    tilemap = TileMap.from_file("tests/scenarios/invalid_position.txt")
    placements = tilemap.suggest_placements(Tile.from_string("wggwwg"))
    assert placements
