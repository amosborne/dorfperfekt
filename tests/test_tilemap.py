from dorfperfekt.tile import Terrain, Tile
from dorfperfekt.tilemap import TileMap, InvalidTilePlacementError
import pytest


def test_new_map():
    tilemap = TileMap()
    assert tilemap[0, 0] == Tile("g")
    assert len(tilemap.open) == 6


def test_counter():
    tilemap = TileMap()
    tilemap[1, 0] = Tile("ggrrdd")
    tilemap[0, 1] = Tile("rrddgg")
    assert tilemap.counter[Tile("dggrrd")] == 2


def test_delete():
    tilemap1 = TileMap()
    tilemap1[1, 0] = Tile("r")

    tilemap2 = TileMap()
    tilemap2[1, 0] = Tile("r")
    tilemap2[0, 1] = Tile("d")
    del tilemap2[0, 1]

    assert tilemap1.tiles == tilemap2.tiles
    assert tilemap1.counter == tilemap2.counter
    assert set(tilemap1.ruined) == set(tilemap2.ruined)
    assert set(tilemap1.open) == set(tilemap2.open)


def test_outer_tile():
    tilemap = TileMap()
    tilemap[1, 0] = Tile("rgggrr")

    outer = tilemap.outer_tile(pos=(1, -1))
    assert outer == Tile("orgooo") and outer.ori == 2

    outer = tilemap.outer_tile(pos=(0, 1))
    assert outer == Tile("oooogg") and outer.ori == 4


def test_ruined():
    tilemap = TileMap()
    tilemap[1, 0] = Tile("r")
    tilemap[0, 1] = Tile("f")
    assert set(tilemap.ruined) == {(0, 0), (1, 0), (0, 1)}

    del tilemap[0, 0]
    assert set(tilemap.ruined) == {(1, 0), (0, 1)}

    tilemap[1, 1] = Tile("gggfrg")
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

    attempt_placement(tile=Tile("wggggg"), pos=(0, 0), invalid=True)
    del tilemap[0, 0]
    tilemap[0, 0] = Tile("wggggg")

    attempt_placement(tile=Tile("c"), pos=(1, 0))
    attempt_placement(tile=Tile("c"), pos=(0, 1))

    attempt_placement(tile=Tile("wwgggg"), pos=(1, 0), invalid=True)
    attempt_placement(tile=Tile("gwwggg"), pos=(1, 0), invalid=True)
    attempt_placement(tile=Tile("ggwwgg"), pos=(1, 0))
    attempt_placement(tile=Tile("gggwwg"), pos=(1, 0))
    attempt_placement(tile=Tile("ggggww"), pos=(1, 0), invalid=True)
    attempt_placement(tile=Tile("wggggw"), pos=(1, 0), invalid=True)

    del tilemap[0, 0]
    tilemap[0, 0] = Tile("s")

    attempt_placement(tile=Tile("twgggg"), pos=(1, 0))
    attempt_placement(tile=Tile("gtwggg"), pos=(1, 0))
    attempt_placement(tile=Tile("ggtwgg"), pos=(1, 0))
    attempt_placement(tile=Tile("gggtwg"), pos=(1, 0))
    attempt_placement(tile=Tile("ggggtw"), pos=(1, 0))
    attempt_placement(tile=Tile("wggggt"), pos=(1, 0))


def test_restricted2():
    tilemap = TileMap()
    tilemap[1, 0] = Tile("wggggg")
    tilemap[2, -1] = Tile("g")


def test_rate_placement():
    tilemap = TileMap()
    score = tilemap.rate_placement(tile=Tile("r"), pos=(1, 0))
    assert score == (2, 1, 3)

    score = tilemap.rate_placement(tile=Tile("wggggg"), pos=(1, 0))
    assert score == (0, 1, 9)

    with pytest.raises(InvalidTilePlacementError):
        tilemap.rate_placement(tile=Tile("t"), pos=(1, 0))


def test_suggest_placements():
    tilemap = TileMap()
    placements = tilemap.suggest_placements(string="r")
    assert ((-1, 0), Tile("r")) in placements[0]

    placements = tilemap.suggest_placements(string="ffgfff")
    assert ((-1, 0), Tile("gfffff")) in placements[0]
    tilemap[-1, 0] = Tile("gfffff")

    placements = tilemap.suggest_placements(string="ffgfff")
    assert ((0, -1), Tile("fgffff")) in placements[0]
    tilemap[0, -1] = Tile("fgffff")

    placements = tilemap.suggest_placements(string="ffrrrr")
    assert ((-1, -1), Tile("ffrrrr")) in placements[0]
