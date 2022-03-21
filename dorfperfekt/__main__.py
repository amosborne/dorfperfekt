import sys
import time
from copy import deepcopy

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import QObject, QSize, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .display import coords2pos, draw_position_map, draw_terrain_map, pos2coords
from .tile import InvalidTileDefinitionError, string2tile
from .tilemap import TileMap

StyleSheet = """
#BlueProgressBar {
    text-align: center;
    border: 2px solid #2196F3;
    border-radius: 5px;
    background-color: #E0E0E0;
}
#BlueProgressBar::chunk {
    background-color: #2196F3;
    width: 10px; 
    margin: 0.5px;
}
"""


def refresh_canvas(fig, ax, canvas, origin, scale):
    extent = fig.get_window_extent()
    coords = pos2coords(origin)
    w = extent.width * fig.dpi / scale
    h = extent.height * fig.dpi / scale
    ax.set_xlim(-w + coords[0], w + coords[0])
    ax.set_ylim(-h + coords[1], h + coords[1])
    canvas.draw()
    canvas.flush_events()


class Solver(QObject):
    result = Signal(tuple)

    def __init__(self, parent=None, **kwargs):
        super(Solver, self).__init__(parent, **kwargs)

    def interrupt(self):
        self.active = False

    @Slot(tuple)
    def run(self, msg):
        self.active = True
        tilemap, terrains = msg
        scores = tilemap.scores(terrains)
        for i, (pos, tilescores) in enumerate(scores):
            self.result.emit((i, pos, tilescores))
            if not self.active:
                break


class MainWindow(QMainWindow):
    run_solver = Signal(tuple)

    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle("Dorfperfekt[*]")
        self.setMinimumSize(QSize(600, 600))

        self.init_menu_bar()

        vbox = QVBoxLayout()

        self.posfg, self.posax, self.poscv = self.init_plot_canvas(vbox)
        self.terfg, self.terax, self.tercv = self.init_plot_canvas(vbox)
        self.ledit = self.init_control_grid(vbox)
        self.pgbar = self.init_progress_bar(vbox)

        self.poscv.callbacks.connect("button_press_event", self.focus)

        central = QWidget(self)
        central.setLayout(vbox)
        self.setCentralWidget(central)

        self.filename = None
        self.tilemap = TileMap()

        self.thread = QThread()
        self.solver = Solver()
        self.solver.result.connect(self.update)
        self.run_solver.connect(self.solver.run)
        self.solver.moveToThread(self.thread)
        self.thread.start(priority=QThread.Priority.IdlePriority)

        self.pos_scale = 2500
        self.pos_focus = (0, 0)

        self.ter_scale = 10000
        self.ter_focus = (0, 0)

        self.refresh()

    def init_menu_bar(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("File")

        open_action = file_menu.addAction("Open...")
        open_action.triggered.connect(self.open)

        save_action = file_menu.addAction("Save")
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save)

        saveas_action = file_menu.addAction("Save as...")
        saveas_action.triggered.connect(self.saveas)

    def init_plot_canvas(self, parent):
        fig = Figure()
        ax = fig.add_axes([0, 0, 1, 1])
        canvas = FigureCanvas(fig)
        parent.addWidget(canvas)

        return fig, ax, canvas

    def init_control_grid(self, parent):
        hbox = QHBoxLayout()
        grid = QGridLayout()

        tile_string = QLineEdit()
        tile_string.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        grid.addWidget(tile_string, 0, 0)

        solve_button = QPushButton("SOLVE")
        solve_button.clicked.connect(self.solve)
        grid.addWidget(solve_button, 1, 0)

        rotate_cw_button = QPushButton("ROTATE CW")
        rotate_cw_button.clicked.connect(lambda: self.rotate(1))
        grid.addWidget(rotate_cw_button, 0, 1)

        rotate_ccw_button = QPushButton("ROTATE CCW")
        rotate_ccw_button.clicked.connect(lambda: self.rotate(-1))
        grid.addWidget(rotate_ccw_button, 1, 1)

        place_button = QPushButton("PLACE")
        place_button.clicked.connect(self.place)
        grid.addWidget(place_button, 0, 2)

        delete_button = QPushButton("DELETE")
        delete_button.clicked.connect(self.delete)
        grid.addWidget(delete_button, 1, 2)

        hbox.addLayout(grid)
        hbox.addStretch()
        parent.addLayout(hbox)

        return tile_string

    def init_progress_bar(self, parent):
        pgbar = QProgressBar(self, objectName="BlueProgressBar")
        parent.addWidget(pgbar)
        return pgbar

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

        self.solver.interrupt()
        self.thread.quit()
        self.thread.wait()
        event.accept()

    # def resizeEvent(self, event):
    # #     self.draw_position_map()
    # #     self.draw_terrain_map()
    #     print("resizing")
    #     event.accept()

    def refresh(self, modified=False):
        self.scores = dict()
        self.draw_position_map()
        self.draw_terrain_map()
        self.setWindowModified(modified)
        self.ledit.setText("")
        self.pgbar.setValue(0)

    def draw_position_map(self):
        ruined = set(self.tilemap.ruined)
        nonruined = set(self.tilemap) - ruined

        ranked = {pos: score for pos, score in self.scores.items() if score is not None}
        ranked = [pos for pos in sorted(ranked, key=ranked.get)]

        draw_position_map(self.posax, nonruined, ruined, ranked)

        refresh_canvas(
            fig=self.posfg,
            ax=self.posax,
            canvas=self.poscv,
            origin=self.pos_focus,
            scale=self.pos_scale,
        )

    def draw_terrain_map(self):
        tiles = list(self.tilemap.items())
        if self.ter_focus in self.tilemap:
            selected = (self.ter_focus, self.tilemap[self.ter_focus])
        else:
            selected = None

        draw_terrain_map(self.terax, tiles, selected)

        refresh_canvas(
            fig=self.terfg,
            ax=self.terax,
            canvas=self.tercv,
            origin=self.ter_focus,
            scale=self.ter_scale,
        )

    def focus(self, event):
        if event.inaxes is not None:
            self.ter_focus = coords2pos((event.xdata, event.ydata))
            self.draw_terrain_map()

    def delete(self):
        if self.ter_focus in self.tilemap:
            del self.tilemap[self.ter_focus]
            self.refresh(modified=True)

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

    def solve(self):
        try:
            string = self.ledit.text()
            tile = string2tile(string)
        except InvalidTileDefinitionError:
            return

        self.pgbar.setMaximum(len(self.tilemap.open))
        self.scores = {pos: None for pos in self.tilemap.open}
        self.solver.interrupt()
        self.run_solver.emit((self.tilemap, tile.terrains))

    def update(self, msg):
        i, pos, tilescores = msg
        if tilescores:
            self.scores[pos] = min(score for score, _ in tilescores)
        else:
            del self.scores[pos]

        self.pgbar.setValue(i + 1)
        # self.draw_position_map()

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


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(StyleSheet)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
