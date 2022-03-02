from dorfperfekt.map import Map
from dorfperfekt.tile import Tile


def test_new_map():
    map = Map()
    assert map[0, 0].tile == Tile.from_string("g")
    assert len(map) == 1
