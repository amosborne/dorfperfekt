from collections import defaultdict

import pytest

from dorfperfekt.tile import string2tile, tile2string
from dorfperfekt.tilemap import InvalidTilePlacementError, TileMap


def test_new_map():
    tilemap = TileMap()
    assert len(tilemap) == 1
    assert tile2string(tilemap[0, 0]) == "GGGGGG"
    assert not len(tilemap.ruined)
    assert len(tilemap.open) == 6
    assert tilemap.counter[tilemap[0, 0].terrains] == 1


def test_counter():
    tilemap = TileMap()
    tilemap[1, 0] = string2tile("ggrrdd")
    tilemap[0, 1] = string2tile("rrddgg")
    terrains = string2tile("dggrrd").terrains
    assert tilemap.counter[terrains] == 2


def test_delete():
    tilemap1 = TileMap()
    tilemap1[1, 0] = string2tile("r")

    tilemap2 = TileMap()
    tilemap2[1, 0] = string2tile("r")
    tilemap2[0, 1] = string2tile("d")
    del tilemap2[0, 1]

    assert tilemap1.tiles == tilemap2.tiles
    assert tilemap1.counter == tilemap2.counter
    assert set(tilemap1.ruined) == set(tilemap2.ruined)
    assert tilemap1.open == tilemap2.open


def test_outer_tile():
    tilemap = TileMap()
    tilemap[1, 0] = string2tile("rgggrr")

    outer = tilemap.outer_tile(pos=(1, -1))
    assert outer == string2tile("orgooo") and outer.ori == 2

    outer = tilemap.outer_tile(pos=(0, 1))
    assert outer == string2tile("oooogg") and outer.ori == 4


def test_ruined():
    tilemap = TileMap()
    tilemap[1, 0] = string2tile("r")
    tilemap[0, 1] = string2tile("f")
    assert set(tilemap.ruined) == {(0, 0), (1, 0), (0, 1)}

    del tilemap[0, 0]
    assert set(tilemap.ruined) == {(1, 0), (0, 1)}

    tilemap[1, 1] = string2tile("gggfrg")
    assert set(tilemap.ruined) == {(1, 0), (0, 1)}


def test_restricted():
    tilemap = TileMap()

    def attempt_placement(tile, pos, invalid=False):
        if invalid:
            with pytest.raises(InvalidTilePlacementError):
                tilemap[pos] = tile
        else:
            tilemap[pos] = tile
            del tilemap[pos]

    attempt_placement(tile=string2tile("wggggg"), pos=(0, 0), invalid=True)
    del tilemap[0, 0]
    tilemap[0, 0] = string2tile("wggggg")

    attempt_placement(tile=string2tile("c"), pos=(1, 0))
    attempt_placement(tile=string2tile("c"), pos=(0, 1))

    attempt_placement(tile=string2tile("wwgggg"), pos=(1, 0), invalid=True)
    attempt_placement(tile=string2tile("gwwggg"), pos=(1, 0), invalid=True)
    attempt_placement(tile=string2tile("ggwwgg"), pos=(1, 0))
    attempt_placement(tile=string2tile("gggwwg"), pos=(1, 0))
    attempt_placement(tile=string2tile("ggggww"), pos=(1, 0), invalid=True)
    attempt_placement(tile=string2tile("wggggw"), pos=(1, 0), invalid=True)

    del tilemap[0, 0]
    tilemap[0, 0] = string2tile("s")

    attempt_placement(tile=string2tile("twgggg"), pos=(1, 0))
    attempt_placement(tile=string2tile("gtwggg"), pos=(1, 0))
    attempt_placement(tile=string2tile("ggtwgg"), pos=(1, 0))
    attempt_placement(tile=string2tile("gggtwg"), pos=(1, 0))
    attempt_placement(tile=string2tile("ggggtw"), pos=(1, 0))
    attempt_placement(tile=string2tile("wggggt"), pos=(1, 0))


def test_score():
    tilemap = TileMap()
    score = tilemap.score_tile(pos=(1, 0), tile=string2tile("r"))
    assert score == (2, 1, -3)

    score = tilemap.score_tile(pos=(1, 0), tile=string2tile("wggggg"))
    assert score == (0, 1, -9)

    with pytest.raises(InvalidTilePlacementError):
        tilemap.score_tile(pos=(1, 0), tile=string2tile("t"))


def test_scores():
    tilemap = TileMap()

    def group_scores(scores):
        grouped_scores = defaultdict(set)
        for pos, tilescores in scores:
            for score, tile in tilescores:
                grouped_scores[score].add((pos, tile))

        return [grouped_scores[score] for score in sorted(grouped_scores)]

    scores = tilemap.scores(string2tile("r").terrains)
    assert ((-1, 0), string2tile("r")) in group_scores(scores)[0]

    scores = tilemap.scores(string2tile("ffgfff").terrains)
    assert ((-1, 0), string2tile("gfffff")) in group_scores(scores)[0]
