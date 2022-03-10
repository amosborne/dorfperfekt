from dorfperfekt.tile import Terrain, Tile
from dorfperfekt.tilemap import MapTile, TileMap


def test_new_map():
    tilemap = TileMap()
    assert tilemap[0, 0].tile.string == "GGGGGG"
    assert tilemap[0, 0].ori == 0
    assert len(tilemap.ruined) == 0
    assert len(tilemap) == 1
    assert {(1, 0), (0, -1)} < tilemap.openpos
    assert tilemap.counter[Tile.from_string("g")] == 1


def test_counter():
    tilemap = TileMap()
    tilemap[1, 0] = MapTile(tile=Tile.from_string("ggrrdd"), ori=0)
    tilemap[0, 1] = MapTile(tile=Tile.from_string("rrddgg"), ori=1)
    assert tilemap.counter[Tile.from_string("dggrrd")] == 2


def test_adjacent_terrains():
    tilemap = TileMap()
    tilemap[1, 0] = MapTile(tile=Tile.from_string("rrrggg"), ori=2)

    adj_terrains = tilemap.adjacent_terrains((1, -1))
    assert adj_terrains == (None, Terrain.RANCH, Terrain.GRASS, None, None, None)

    adj_terrains = tilemap.adjacent_terrains((0, 1))
    assert adj_terrains == (None, None, None, None, Terrain.GRASS, Terrain.RANCH)


def test_water():
    tilemap = TileMap()
    tilemap[0, 0] = MapTile(tile=Tile.from_string("ggggwg"), ori=1)

    lake = Tile.from_string("c")
    assert tilemap.is_valid_placement(pos=(0, 1), tile=lake, ori=0)
    assert tilemap.is_valid_placement(pos=(1, -1), tile=lake, ori=0)

    river = Tile.from_string("ggwwgg")
    assert tilemap.is_valid_placement(pos=(0, 1), tile=river, ori=0)
    assert tilemap.is_valid_placement(pos=(1, -1), tile=river, ori=0)
    assert not tilemap.is_valid_placement(pos=(1, 0), tile=river, ori=0)
    assert not tilemap.is_valid_placement(pos=(0, 1), tile=river, ori=1)
    assert not tilemap.is_valid_placement(pos=(1, -1), tile=river, ori=1)

    tilemap[0, 0] = MapTile(tile=Tile.from_string("s"), ori=0)
    assert tilemap.is_valid_placement(pos=(0, 1), tile=river, ori=0)
    assert tilemap.is_valid_placement(pos=(0, 1), tile=river, ori=1)


def test_train():
    tilemap = TileMap()
    tilemap[0, 0] = MapTile(tile=Tile.from_string("ggggtg"), ori=1)

    train = Tile.from_string("ggttgg")
    assert tilemap.is_valid_placement(pos=(0, 1), tile=train, ori=0)
    assert tilemap.is_valid_placement(pos=(1, -1), tile=train, ori=0)
    assert not tilemap.is_valid_placement(pos=(1, 0), tile=train, ori=0)
    assert not tilemap.is_valid_placement(pos=(0, 1), tile=train, ori=1)
    assert not tilemap.is_valid_placement(pos=(1, -1), tile=train, ori=1)

    tilemap[0, 0] = MapTile(tile=Tile.from_string("s"), ori=0)
    assert tilemap.is_valid_placement(pos=(0, 1), tile=train, ori=0)
    assert tilemap.is_valid_placement(pos=(0, 1), tile=train, ori=1)


def test_ruined():
    tilemap = TileMap()
    tilemap[-1, 0] = MapTile(tile=Tile.from_string("c"), ori=0)
    assert not tilemap.is_ruined_position(pos=(0, 0))
    assert not tilemap.is_ruined_position(pos=(-1, 0))

    tilemap[1, 0] = MapTile(tile=Tile.from_string("r"), ori=0)
    assert tilemap.is_ruined_position(pos=(0, 0))
    assert tilemap.is_ruined_position(pos=(1, 0))

    assert len(tilemap.openpos) == 10
    assert len(tilemap.ruined) == 2


def test_delete():
    tilemap1 = TileMap()
    tilemap1[1, 0] = MapTile(tile=Tile.from_string("r"), ori=0)

    tilemap2 = TileMap()
    tilemap2[1, 0] = MapTile(tile=Tile.from_string("r"), ori=0)
    tilemap2[0, 1] = MapTile(tile=Tile.from_string("d"), ori=0)
    del tilemap2[0, 1]

    tilemap1.counter[Tile.from_string("d")] = 0

    assert tilemap1.tilemap == tilemap2.tilemap
    assert tilemap1.openpos == tilemap2.openpos
    assert tilemap1.counter == tilemap2.counter
    assert tilemap1.ruined == tilemap2.ruined


def test_suggest_placement():
    tilemap = TileMap()
    rate = tilemap.rate_placement(pos=(1, 0), tile=Tile.from_string("r"), ori=0)
    assert rate == (2, 6)

    score, ori = tilemap.rate_position(pos=(1, 0), tile=Tile.from_string("r"))
    assert score == (2, 2, 6)
    assert ori == {0, 1, 2, 3, 4, 5}

    placements = tilemap.suggest_placements(tile=Tile.from_string("r"))
    assert ((-1, 0), 0) in placements[0]

    one_grass = Tile.from_string("ffgfff")
    placements = tilemap.suggest_placements(tile=one_grass)
    pos, ori = (-1, 0), 4
    assert (pos, ori) in placements[0]
    tilemap[pos] = MapTile(tile=one_grass, ori=ori)

    placements = tilemap.suggest_placements(tile=one_grass)
    pos, ori = (0, -1), 5
    assert (pos, ori) in placements[0]
    tilemap[pos] = MapTile(tile=one_grass, ori=ori)

    ranch_forest = Tile.from_string("ffrrrr")
    placements = tilemap.suggest_placements(tile=ranch_forest)
    pos, ori = (-1, -1), 0
    assert (pos, ori) in placements[0]
