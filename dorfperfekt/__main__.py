import sys

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from dorfperfekt.display import draw_position_map, draw_terrain_map, hex_coordinates
from dorfperfekt.map import Map
from dorfperfekt.tile import Tile

# def on_click(event):
#     if event.inaxes is not None:
#         print(event.xdata, event.ydata)
#     else:
#         print("Clicked ouside axes bounds but inside plot window")


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle("Dorfperfekt")
        self.setMinimumSize(QSize(600, 600))

        central = QWidget(self)
        self.setCentralWidget(central)

        vbox = QVBoxLayout()
        central.setLayout(vbox)

        fig = Figure()
        self.position_map_ax = fig.add_subplot(1, 1, 1)
        self.position_map_canvas = FigureCanvas(fig)
        vbox.addWidget(self.position_map_canvas, stretch=2)
        # canvas.callbacks.connect("button_press_event", on_click)

        fig = Figure()
        self.terrain_map_ax = fig.add_subplot(1, 1, 1)
        self.terrain_map_canvas = FigureCanvas(fig)
        vbox.addWidget(self.terrain_map_canvas, stretch=1)

        hbox = QHBoxLayout()
        vbox.addLayout(hbox)

        grid = QGridLayout()
        hbox.addLayout(grid)
        hbox.addStretch()

        self.tile_string = QLineEdit()
        self.tile_string.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        grid.addWidget(self.tile_string, 0, 0)

        solve_button = QPushButton("SOLVE")
        solve_button.clicked.connect(self.solve)
        grid.addWidget(solve_button, 1, 0)

        rotate_cw_button = QPushButton("Rotate CW")
        grid.addWidget(rotate_cw_button, 0, 1)

        rotate_ccw_button = QPushButton("Rotate CCW")
        grid.addWidget(rotate_ccw_button, 1, 1)

        place_button = QPushButton("Place")
        place_button.clicked.connect(self.place)
        grid.addWidget(place_button, 0, 2)

        delete_button = QPushButton("Delete")
        grid.addWidget(delete_button, 1, 2)

        self.map = Map()

        draw_position_map(self.position_map_ax, self.map)
        self.position_map_canvas.draw()
        self.position_map_canvas.flush_events()

        draw_terrain_map(self.terrain_map_ax, self.map)
        self.terrain_map_canvas.draw()
        self.terrain_map_canvas.flush_events()

    def solve(self):
        try:
            tile = Tile.from_string(self.tile_string.text())
        except (AssertionError, KeyError):
            return  # bad tile string-- do nothing

        movelist = self.map.suggest_placements(tile)
        move = movelist[0].pop()
        movelist[0].add(move)
        self.to_place = (tile, *move)
        print(self.to_place)

        draw_position_map(self.position_map_ax, self.map, movelist)
        self.position_map_canvas.draw()
        self.position_map_canvas.flush_events()

    def place(self):
        tile, pos, ori = self.to_place
        self.map[pos] = (tile, ori)

        draw_position_map(self.position_map_ax, self.map)
        self.position_map_canvas.draw()
        self.position_map_canvas.flush_events()


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
