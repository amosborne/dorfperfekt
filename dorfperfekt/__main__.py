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
        ax = fig.add_subplot(1, 1, 1)
        ax.set_aspect("equal")
        ax.axis("off")
        canvas = FigureCanvas(fig)
        # canvas.callbacks.connect("button_press_event", on_click)
        vbox.addWidget(canvas)

        fig = Figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.set_aspect("equal")
        ax.axis("off")
        canvas = FigureCanvas(fig)
        vbox.addWidget(canvas)

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
        grid.addWidget(place_button, 0, 2)

        delete_button = QPushButton("Delete")
        grid.addWidget(delete_button, 1, 2)

        self.map = Map()

    def solve(self):
        try:
            tile = Tile.from_string(self.tile_string.text())
        except (AssertionError, KeyError):
            return  # bad tile string-- do nothing

        placements = self.map.suggest_placements(tile)
        pos, ori = placements.pop()
        print(tile, pos, ori)
        self.map[pos] = (tile, ori)


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
