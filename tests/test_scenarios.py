# import cProfile
import filecmp
import os
from collections import defaultdict

from dorfperfekt.tile import string2tile
from dorfperfekt.tilemap import TileMap


def group_scores(scores):
    grouped_scores = defaultdict(set)
    for score, pos, tile in scores:
        grouped_scores[score].add((pos, tile))

    return [grouped_scores[score] for score in sorted(grouped_scores)]


def test_perfect_station():
    filein = "tests/scenarios/perfect_station.txt"
    fileout = "tests/test_perfect_station.txt"
    tilemap = TileMap.from_file(filein)

    scores = tilemap.scores(string2tile("s").terrains)
    assert ((2, -1), string2tile("s")) in group_scores(scores)[0]

    tilemap.write_file(fileout)
    assert filecmp.cmp(filein, fileout)
    os.remove(fileout)


def test_invalid_position():
    filein = "tests/scenarios/invalid_position.txt"
    fileout = "tests/test_invalid_position.txt"
    tilemap = TileMap.from_file(filein)

    scores = tilemap.scores(string2tile("wggwwg").terrains)
    assert len(group_scores(scores))

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

    # cProfile.runctx("tilemap.suggest_placements(string='d')", globals(), locals())

    # print(validate_tiles.cache_info())
