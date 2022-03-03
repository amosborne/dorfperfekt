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

    pos, _ = map.suggest_placement(Tile.from_string("s"))
    assert pos == (2, -1)
