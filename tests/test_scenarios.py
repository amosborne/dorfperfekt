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
