from dorfperfekt.tile import Terrain, Tile, terrains2string
from dorfperfekt.tilemap import TileMap


def test_new_map():
    tilemap = TileMap()
    assert terrains2string(tilemap.tiles[0, 0].terrains) == "GGGGGG"


def test_counter():
    tilemap = TileMap()
    tilemap.place(pos=(1, 0), tile=Tile.from_string("ggrrdd"), ori=0)
    tilemap.place(pos=(0, 1), tile=Tile.from_string("rrddgg"), ori=1)
    assert tilemap.counter[Tile.from_string("dggrrd")] == 2


def test_adjacent_terrains():
    tilemap = TileMap()
    tilemap.place(pos=(1, 0), tile=Tile.from_string("rrrggg"), ori=2)

    adj_terrains = tilemap.adj_terrains(pos=(1, -1))
    assert adj_terrains == (None, Terrain.RANCH, Terrain.GRASS, None, None, None)

    adj_terrains = tilemap.adj_terrains(pos=(0, 1))
    assert adj_terrains == (None, None, None, None, Terrain.GRASS, Terrain.RANCH)


def test_water():
    tilemap = TileMap()
    tilemap.remove(pos=(0, 0))
    tilemap.place(pos=(0, 0), tile=Tile.from_string("ggggwg"), ori=1)

    lake = Tile.from_string("c")
    assert tilemap.is_valid_placement(pos=(0, 1), tile=lake, ori=0)
    assert tilemap.is_valid_placement(pos=(1, -1), tile=lake, ori=0)

    river = Tile.from_string("ggwwgg")
    assert tilemap.is_valid_placement(pos=(0, 1), tile=river, ori=0)
    assert tilemap.is_valid_placement(pos=(1, -1), tile=river, ori=0)
    assert not tilemap.is_valid_placement(pos=(1, 0), tile=river, ori=0)
    assert not tilemap.is_valid_placement(pos=(0, 1), tile=river, ori=1)
    assert not tilemap.is_valid_placement(pos=(1, -1), tile=river, ori=1)

    tilemap.remove(pos=(0, 0))
    tilemap.place(pos=(0, 0), tile=Tile.from_string("s"), ori=1)
    assert tilemap.is_valid_placement(pos=(0, 1), tile=river, ori=0)
    assert tilemap.is_valid_placement(pos=(0, 1), tile=river, ori=1)


def test_train():
    tilemap = TileMap()
    tilemap.remove(pos=(0, 0))
    tilemap.place(pos=(0, 0), tile=Tile.from_string("ggggtg"), ori=1)

    train = Tile.from_string("ggttgg")
    assert tilemap.is_valid_placement(pos=(0, 1), tile=train, ori=0)
    assert tilemap.is_valid_placement(pos=(1, -1), tile=train, ori=0)
    assert not tilemap.is_valid_placement(pos=(1, 0), tile=train, ori=0)
    assert not tilemap.is_valid_placement(pos=(0, 1), tile=train, ori=1)
    assert not tilemap.is_valid_placement(pos=(1, -1), tile=train, ori=1)

    tilemap.remove(pos=(0, 0))
    tilemap.place(pos=(0, 0), tile=Tile.from_string("s"), ori=1)
    assert tilemap.is_valid_placement(pos=(0, 1), tile=train, ori=0)
    assert tilemap.is_valid_placement(pos=(0, 1), tile=train, ori=1)


def test_ruined():
    tilemap = TileMap()
    ruined, adj_ruined = tilemap.is_ruined_by_placement(
        pos=(-1, 0), tile=Tile.from_string("c"), ori=0
    )
    assert not ruined and not any(adj_ruined)

    ruined, adj_ruined = tilemap.is_ruined_by_placement(
        pos=(1, 0), tile=Tile.from_string("r"), ori=0
    )
    assert ruined and adj_ruined[3] and adj_ruined.count(True) == 1

    tilemap.place(pos=(1, 0), tile=Tile.from_string("r"), ori=0)
    assert len(set(tilemap.ruined)) == 2


def test_delete():
    tilemap1 = TileMap()
    tilemap1.place(pos=(1, 0), tile=Tile.from_string("r"), ori=0)

    tilemap2 = TileMap()
    tilemap2.place(pos=(1, 0), tile=Tile.from_string("r"), ori=0)
    tilemap2.place(pos=(0, 1), tile=Tile.from_string("d"), ori=0)
    tilemap2.remove(pos=(0, 1))

    assert tilemap1.tiles == tilemap2.tiles
    assert tilemap1.counter == tilemap2.counter
    assert set(tilemap1.ruined) == set(tilemap2.ruined)


def test_suggest_placement():
    tilemap = TileMap()
    rate = tilemap.rate_placement(pos=(1, 0), tile=Tile.from_string("r"), ori=0)
    assert rate == (2, 3)

    score, oris = tilemap.rate_position(pos=(1, 0), tile=Tile.from_string("r"))
    assert score == (2, 1, 3)
    assert oris == {0, 1, 2, 3, 4, 5}

    placements = tilemap.suggest_placements(tile=Tile.from_string("r"))
    assert ((-1, 0), 0) in placements[0]

    one_grass = Tile.from_string("ffgfff")
    placements = tilemap.suggest_placements(tile=one_grass)
    pos, ori = (-1, 0), 4
    assert (pos, ori) in placements[0]
    tilemap.place(pos, one_grass, ori)

    placements = tilemap.suggest_placements(tile=one_grass)
    pos, ori = (0, -1), 5
    assert (pos, ori) in placements[0]
    tilemap.place(pos, one_grass, ori)

    ranch_forest = Tile.from_string("ffrrrr")
    placements = tilemap.suggest_placements(tile=ranch_forest)
    pos, ori = (-1, -1), 0
    assert (pos, ori) in placements[0]
