from dorfperfekt.map import Map
from dorfperfekt.tile import Tile


def test_perfect_station():
    map = Map()
    map[1, 0] = (Tile.from_string("gggggg"), 0)
    map[2, 0] = (Tile.from_string("ggggtg"), 0)
    map[1, -1] = (Tile.from_string("gggggg"), 0)
    map[3, -1] = (Tile.from_string("gggwgg"), 0)
    map[2, -2] = (Tile.from_string("gwgggg"), 0)
    map[3, -2] = (Tile.from_string("gggggg"), 0)

    placements = map.suggest_placements(Tile.from_string("s"))
    assert (2, -1) in {pos for pos, _ in placements}


def test_invalid_position():
    map = Map()
    map[1, 0] = (Tile.from_string("rrdggr"), 0)
    map[-1, 0] = (Tile.from_string("ggffgg"), 0)
    map[1, -1] = (Tile.from_string("gggddg"), 0)
    map[0, -1] = (Tile.from_string("dggrrr"), 0)
    map[-1, -1] = (Tile.from_string("rggfff"), 0)
    map[2, -2] = (Tile.from_string("ffggff"), 0)
    map[-1, 1] = (Tile.from_string("rrrdgg"), 0)
    map[1, 1] = (Tile.from_string("ccrgrc"), 0)
    map[0, 2] = (Tile.from_string("rgrrgr"), 0)
    map[0, 3] = (Tile.from_string("cggccc"), 0)

    placements = map.suggest_placements(Tile.from_string("wggwwg"))
    assert placements
