import cProfile
import filecmp
import os

from dorfperfekt.tile import Tile
from dorfperfekt.tilemap import TileMap


def test_perfect_station():
    filein = "tests/scenarios/perfect_station.txt"
    fileout = "tests/test_perfect_station.txt"
    tilemap = TileMap.from_file(filein)
    placements = tilemap.suggest_placements(string="s")
    assert ((2, -1), Tile("s")) in placements[0]
    tilemap.write_file(fileout)
    assert filecmp.cmp(filein, fileout)
    os.remove(fileout)


def test_invalid_position():
    filein = "tests/scenarios/invalid_position.txt"
    fileout = "tests/test_invalid_position.txt"
    tilemap = TileMap.from_file(filein)
    placements = tilemap.suggest_placements(string="wggwwg")
    assert placements
    tilemap.write_file(fileout)
    assert filecmp.cmp(filein, fileout)
    os.remove(fileout)


def test_demo_game():
    filein = "tests/scenarios/demo_game.txt"
    fileout = "tests/test_demo_game.txt"
    tilemap = TileMap.from_file("tests/scenarios/demo_game.txt")
    tilemap.write_file(fileout)
    assert filecmp.cmp(filein, fileout)
    os.remove(fileout)

    # cProfile.runctx(
    #     "tilemap.suggest_placements(string='d')", globals(), locals()
    # )
