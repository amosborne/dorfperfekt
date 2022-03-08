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

from dorfperfekt.display import coords2pos, draw_position_map, draw_terrain_map
from dorfperfekt.map import Map
from dorfperfekt.tile import Tile


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
        self.map = Map()
        self.refresh()

    def refresh(self, modified=False):
        self.movelist = []
        self.focus_pos = None
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
            self.map = Map.from_file(filename)
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
            self.map.write_file(self.filename)
            self.setWindowModified(False)

    def saveas(self):
        filename = QFileDialog.getSaveFileName(self)[0]
        if filename:
            self.map.write_file(filename)
            self.filename = filename
            self.setWindowModified(False)

    def draw_position_map(self):
        draw_position_map(self.position_map_ax, self.map, self.movelist)
        self.position_map_canvas.draw()
        self.position_map_canvas.flush_events()

    def draw_terrain_map(self):
        if self.focus_pos is None:
            placements = []
        else:
            nearby = {pos for _, pos in self.map.neighbors(self.focus_pos)}
            for _ in range(3):
                nearby |= {
                    pos for npos in nearby for _, pos in self.map.neighbors(npos)
                }

            placements = [(npos, *self.map[npos]) for npos in nearby]

            if self.new_tile_focus:
                placements.append((self.focus_pos, self.tile, self.ori))
            else:
                placements.append((self.focus_pos, *self.map[self.focus_pos]))

        draw_terrain_map(self.terrain_map_ax, placements)
        self.terrain_map_canvas.draw()
        self.terrain_map_canvas.flush_events()

    def solve(self):
        try:
            self.tile = Tile.from_string(self.tile_string.text())
        except (AssertionError, KeyError):
            return  # bad tile string-- do nothing

        self.movelist = self.map.suggest_placements(self.tile)
        self.focus_pos = None
        self.draw_position_map()
        self.draw_terrain_map()

    def focus(self, event):
        if event.inaxes is not None:
            moves = [(mpos, ori) for mset in self.movelist for mpos, ori in mset]
            pos = coords2pos((event.xdata, event.ydata))
            self.new_tile_focus = pos in list(zip(*moves))[0] if moves else False
            self.focus_pos = pos if pos in self.map or self.new_tile_focus else None

            if self.new_tile_focus:
                idx = list(zip(*moves))[0].index(pos)
                self.ori = list(zip(*moves))[1][idx]

        else:
            self.focus_pos = None

        self.draw_terrain_map()

    def place(self):
        if self.focus_pos is not None and self.new_tile_focus:
            self.map[self.focus_pos] = (self.tile, self.ori)
            self.refresh(modified=True)

    def rotate(self, direc):
        if self.focus_pos is not None and self.new_tile_focus:
            self.ori += direc
            while not self.map.is_valid_placement(self.tile, self.focus_pos, self.ori):
                self.ori += direc

            self.draw_terrain_map()

    def delete(self):
        if self.focus_pos is not None and not self.new_tile_focus:
            del self.map[self.focus_pos]
            self.refresh(modified=True)


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
