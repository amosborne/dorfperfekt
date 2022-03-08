from dorfperfekt.map import Map
from dorfperfekt.tile import Tile


def test_perfect_station():
    map = Map.from_file("tests/scenarios/perfect_station.txt")
    placements = map.suggest_placements(Tile.from_string("s"))
    assert (2, -1) in {pos for pos, _ in placements[0]}


def test_invalid_position():
    map = Map.from_file("tests/scenarios/invalid_position.txt")
    placements = map.suggest_placements(Tile.from_string("wggwwg"))
    assert placements
