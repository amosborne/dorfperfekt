import sys

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .display import coords2pos, draw_position_map, draw_terrain_map

# from .tile import Tile
from .tilemap import TileMap


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle("Dorfperfekt[*]")
        self.setMinimumSize(QSize(600, 600))

        central = QWidget(self)
        self.setCentralWidget(central)

        vbox = QVBoxLayout()
        central.setLayout(vbox)

        fig = Figure()
        self.position_map_ax = fig.add_subplot(1, 1, 1)
        self.position_map_canvas = FigureCanvas(fig)
        self.position_map_canvas.callbacks.connect("button_press_event", self.focus)
        vbox.addWidget(self.position_map_canvas, stretch=2)

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
        rotate_cw_button.clicked.connect(lambda: self.rotate(1))
        grid.addWidget(rotate_cw_button, 0, 1)

        rotate_ccw_button = QPushButton("Rotate CCW")
        rotate_ccw_button.clicked.connect(lambda: self.rotate(-1))
        grid.addWidget(rotate_ccw_button, 1, 1)

        place_button = QPushButton("Place")
        place_button.clicked.connect(self.place)
        grid.addWidget(place_button, 0, 2)

        delete_button = QPushButton("Delete")
        delete_button.clicked.connect(self.delete)
        grid.addWidget(delete_button, 1, 2)

        menu = self.menuBar()
        file_menu = menu.addMenu("File")

        open_action = file_menu.addAction("Open...")
        open_action.triggered.connect(self.open)

        save_action = file_menu.addAction("Save")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save)

        saveas_action = file_menu.addAction("Save as...")
        saveas_action.triggered.connect(self.saveas)

        self.filename = None
        self.tilemap = TileMap()
        self.refresh()

    def refresh(self, modified=False):
        self.movelist = []
        self.move = None
        self.select = None
        self.draw_position_map()
        self.draw_terrain_map()
        self.tile_string.setText("")
        self.setWindowModified(modified)

    def open(self):
        if self.isWindowModified():
            ret = QMessageBox.warning(
                self,
                "Dorfperfekt -- Warning",
                "Current file is not saved!",
                QMessageBox.Ok | QMessageBox.Cancel,
            )
            if ret is QMessageBox.Cancel:
                return

        filename = QFileDialog.getOpenFileName(self)[0]
        if filename:
            self.tilemap = TileMap.from_file(filename)
            self.filename = filename
            self.refresh()

    def closeEvent(self, event):
        if self.isWindowModified():
            ret = QMessageBox.warning(
                self,
                "Dorfperfekt -- Warning",
                "Current file is not saved!",
                QMessageBox.Ok | QMessageBox.Cancel,
            )
            if ret is QMessageBox.Cancel:
                event.ignore()
                return

        event.accept()

    def save(self):
        if not self.isWindowModified():
            return
        elif self.filename is None:
            self.saveas()
        else:
            self.tilemap.write_file(self.filename)
            self.setWindowModified(False)

    def saveas(self):
        filename = QFileDialog.getSaveFileName(self)[0]
        if filename:
            self.tilemap.write_file(filename)
            self.filename = filename
            self.setWindowModified(False)

    def draw_position_map(self):
        draw_position_map(self.position_map_ax, self.tilemap, self.movelist)
        self.position_map_canvas.draw()
        self.position_map_canvas.flush_events()

    def draw_terrain_map(self, focus=None):
        if focus is None:
            draw_terrain_map(self.terrain_map_ax, [])

        else:
            placements = self.tilemap.items()
            placements.append(focus)
            draw_terrain_map(self.terrain_map_ax, [])

        self.terrain_map_canvas.draw()
        self.terrain_map_canvas.flush_events()

    def solve(self):
        string = self.tile_string.text()
        self.movelist = self.tilemap.suggest_placements(string)
        self.draw_position_map()
        self.draw_terrain_map()

    def focus(self, event):
        if event.inaxes is not None:
            pos = coords2pos((event.xdata, event.ydata))
            moves_pos, moves_tile = zip(*set().union(*self.movelist))

            if pos in self.tilemap:
                self.select = (pos, self.tilemap[pos])
                self.draw_terrain_map(focus=self.select)
            elif pos in moves_pos:
                self.move = (pos, moves_tile[moves_pos.index(pos)])
                self.draw_terrain_map(focus=self.move)

        else:
            self.draw_terrain_map()

    def place(self):
        if self.move is not None:
            self.tilemap[self.move[0]] = self.move[1]
            self.refresh(modified=True)

    def rotate(self, direc):
        if self.move is not None:
            moves = set().union(*self.movelist)
            moves = {move for move in moves if move == self.move}
            ori = self.move[1].ori
            while True:
                ori += direc % 6
                for move in moves:
                    if move[1].ori == ori:
                        self.move = move
                        self.draw_terrain_map(focus=self.move)
                        return

    def delete(self):
        if self.select is not None:
            del self.tilemap[self.select[0]]
            self.refresh(modified=True)


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
