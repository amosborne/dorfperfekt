from enum import Enum

Terrain = Enum("Terrain", "GRASS FOREST RANCH DWELLING WATER STATION TRAIN")


class Tile:
    def __init__(self, terrain):
        self.terrain = terrain

    @staticmethod
    def from_string(string):
        string = string.upper()
        string = string * 6 if len(string) == 1 else string
        terrain = {t.name[0]: t for t in Terrain}
        return Tile([terrain[s] for s in string])

    def to_string(self):
        return "".join([terrain.name[0] for terrain in self.terrain])

    def __eq__(self, other):
        return self.to_string() in other.to_string() * 2
