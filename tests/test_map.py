from dorfperfekt.map import Map
from dorfperfekt.tile import Tile


def test_new_map():
    map = Map()
    assert map[0, 0] == (Tile.from_string("g"), 0)
    assert len(map) == 1


def test_water():
    map = Map()
    map[0, 0] = (Tile.from_string("ggggwg"), 1)
    lake = Tile.from_string("w")
    assert map.is_valid_position(lake, pos=(0, 1), ori=0)
    assert map.is_valid_position(lake, pos=(1, -1), ori=0)

    river = Tile.from_string("ggwwgg")
    assert map.is_valid_position(river, pos=(0, 1), ori=0)
    assert map.is_valid_position(river, pos=(1, -1), ori=0)
    assert not map.is_valid_position(river, pos=(1, 0), ori=0)
    assert not map.is_valid_position(river, pos=(0, 1), ori=1)
    assert not map.is_valid_position(river, pos=(1, -1), ori=1)

    map[0, 0] = (Tile.from_string("s"), 0)
    assert map.is_valid_position(river, pos=(0, 1), ori=0)
    assert map.is_valid_position(river, pos=(0, 1), ori=1)


def test_train():
    map = Map()
    map[0, 0] = (Tile.from_string("ggggtg"), 1)

    train = Tile.from_string("ggttgg")
    assert map.is_valid_position(train, pos=(0, 1), ori=0)
    assert map.is_valid_position(train, pos=(1, -1), ori=0)
    assert not map.is_valid_position(train, pos=(1, 0), ori=0)
    assert not map.is_valid_position(train, pos=(0, 1), ori=1)
    assert not map.is_valid_position(train, pos=(1, -1), ori=1)

    map[0, 0] = (Tile.from_string("s"), 0)
    assert map.is_valid_position(train, pos=(0, 1), ori=0)
    assert map.is_valid_position(train, pos=(0, 1), ori=1)


def test_ruined():
    map = Map()
    map[-1, 0] = (Tile.from_string("w"), 0)
    assert not map.is_ruined_position((0, 0))
    assert not map.is_ruined_position((-1, 0))

    map[1, 0] = (Tile.from_string("r"), 0)
    assert map.is_ruined_position((0, 0))
    assert map.is_ruined_position((1, 0))
