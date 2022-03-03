from dorfperfekt.map import Map
from dorfperfekt.tile import Tile


def test_new_map():
    map = Map()
    assert map[0, 0] == (Tile.from_string("g"), 0)
    assert len(map) == 1
    assert len(map.open_positions()) == 6


def test_water():
    map = Map()
    map[0, 0] = (Tile.from_string("ggggwg"), 1)
    lake = Tile.from_string("w")
    assert map.is_valid_placement(lake, pos=(0, 1), ori=0)
    assert map.is_valid_placement(lake, pos=(1, -1), ori=0)

    river = Tile.from_string("ggwwgg")
    assert map.is_valid_placement(river, pos=(0, 1), ori=0)
    assert map.is_valid_placement(river, pos=(1, -1), ori=0)
    assert not map.is_valid_placement(river, pos=(1, 0), ori=0)
    assert not map.is_valid_placement(river, pos=(0, 1), ori=1)
    assert not map.is_valid_placement(river, pos=(1, -1), ori=1)

    map[0, 0] = (Tile.from_string("s"), 0)
    assert map.is_valid_placement(river, pos=(0, 1), ori=0)
    assert map.is_valid_placement(river, pos=(0, 1), ori=1)


def test_train():
    map = Map()
    map[0, 0] = (Tile.from_string("ggggtg"), 1)

    train = Tile.from_string("ggttgg")
    assert map.is_valid_placement(train, pos=(0, 1), ori=0)
    assert map.is_valid_placement(train, pos=(1, -1), ori=0)
    assert not map.is_valid_placement(train, pos=(1, 0), ori=0)
    assert not map.is_valid_placement(train, pos=(0, 1), ori=1)
    assert not map.is_valid_placement(train, pos=(1, -1), ori=1)

    map[0, 0] = (Tile.from_string("s"), 0)
    assert map.is_valid_placement(train, pos=(0, 1), ori=0)
    assert map.is_valid_placement(train, pos=(0, 1), ori=1)


def test_ruined():
    map = Map()
    map[-1, 0] = (Tile.from_string("w"), 0)
    assert not map.is_ruined_position((0, 0))
    assert not map.is_ruined_position((-1, 0))

    map[1, 0] = (Tile.from_string("r"), 0)
    assert map.is_ruined_position((0, 0))
    assert map.is_ruined_position((1, 0))

    assert len(map.open_positions()) == 10


def test_suggest_placement():
    map = Map()
    rate = map.rate_placement(Tile.from_string("r"), (1, 0), 0)
    assert rate == (2, 2, 1, 1, 0, 0)

    rate = map.rate_position(Tile.from_string("r"), (1, 0))
    assert rate == (2, 2, 1, 1, 0, 0)

    npos, ori = map.suggest_placement(Tile.from_string("r"))
    assert npos == (-1, 0)
    assert ori == 0

    one_grass = Tile.from_string("ffgfff")
    npos, ori = map.suggest_placement(one_grass)
    assert npos == (-1, 0)
    assert ori == 4
    map[npos] = (one_grass, ori)

    npos, ori = map.suggest_placement(one_grass)
    assert npos == (0, -1)
    assert ori == 5
    map[npos] = (one_grass, ori)

    ranch_forest = Tile.from_string("ffrrrr")
    npos, ori = map.suggest_placement(ranch_forest)
    assert npos == (-1, -1)
    assert ori == 0
