import sys
import time
from collections import defaultdict
from copy import deepcopy

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import QObject, QSize, QThread, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpinBox,
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
    scale = scale * 3 / 4
    ascale = scale * extent.height / extent.width
    ax.set_xlim(coords[0] - scale, coords[0] + scale)
    ax.set_ylim(coords[1] - ascale, coords[1] + ascale)
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
        tilemap, terrains, thresh = msg
        scores = tilemap.scores(terrains, thresh)
        for i, (pos, tilescores) in enumerate(scores):
            self.result.emit((i, pos, tilescores))
            if not self.active:
                break


class MainWindow(QMainWindow):
    run_solver = Signal(tuple)

    def __init__(self):
        QMainWindow.__init__(self)
        self.setMinimumSize(500, 500)

        self.filename = None
        self.tilemap = TileMap()
        self.pos_focus = (0, 0)
        self.ter_focus = (0, 0)

        self.init_menu_bar()
        self.init_window_title()

        # setup top-level layouts
        main_vbox = QVBoxLayout()
        main_hbox = QHBoxLayout()
        side_vbox = QVBoxLayout()
        main_vbox.addLayout(main_hbox)
        main_hbox.addLayout(side_vbox)

        central = QWidget(self)
        central.setLayout(main_vbox)
        self.setCentralWidget(central)

        # setup top-level widgets
        self.possc, self.tersc, self.ledit, self.thresh = self.init_controls(side_vbox)
        self.terfg, self.terax, self.tercv = self.init_plot_canvas(side_vbox)
        self.tercv.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Expanding)
        self.posfg, self.posax, self.poscv = self.init_plot_canvas(main_hbox)
        self.poscv.callbacks.connect("button_press_event", self.focus)
        self.pgbar = self.init_progress_bar(main_vbox)

        # setup solver thread
        self.thread = QThread()
        self.solver = Solver()
        self.solver.result.connect(self.update_scores)
        self.run_solver.connect(self.solver.run)
        self.solver.moveToThread(self.thread)
        self.thread.start(priority=QThread.Priority.IdlePriority)

        # setup resize event timer
        self.rtimer = QTimer()
        self.rtimer.setSingleShot(True)
        self.rtimer.timeout.connect(self.resized)

        # setup progress timer
        self.ptimer = QTimer()
        self.ptimer.timeout.connect(self.update_progress)

    def init_window_title(self):
        filestring = " (" + self.filename + ")" if self.filename is not None else ""
        self.setWindowTitle("Dorfperfekt" + filestring + "[*]")

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
        parent.addWidget(canvas, stretch=1)

        return fig, ax, canvas

    def init_controls(self, parent):
        grid = QGridLayout()

        grid.addWidget(QLabel("Position Map Horizontal Scale :"), 0, 0, 1, 2)
        grid.addWidget(possc := QSpinBox(minimum=10), 0, 2)
        grid.addWidget(QLabel("Terrain Map Horizontal Scale :"), 1, 0, 1, 2)
        grid.addWidget(tersc := QSpinBox(minimum=5), 1, 2)

        grid.addWidget(set_origin := QPushButton("Set Origin"), 2, 0)
        grid.addWidget(rst_origin := QPushButton("Reset Origin"), 2, 1)
        grid.addWidget(refresh := QPushButton("Refresh"), 2, 2)

        grid.addWidget(QLabel("Tile Definition String :"), 3, 0, 1, 2)
        grid.addWidget(ledit := QLineEdit(), 3, 2)
        ledit.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        grid.addWidget(QLabel("Tile Counter Threshold :"), 4, 0, 1, 2)
        grid.addWidget(thresh := QSpinBox(minimum=1), 4, 2)

        grid.addWidget(solve := QPushButton("Solve"), 5, 0, 1, 3)
        grid.addWidget(delete := QPushButton("Delete"), 6, 0)
        grid.addWidget(rotate := QPushButton("Rotate"), 6, 1)
        grid.addWidget(place := QPushButton("Place"), 6, 2)

        possc.valueChanged.connect(self.draw_position_map)
        tersc.valueChanged.connect(self.draw_terrain_map)
        refresh.clicked.connect(self.draw_position_map)
        set_origin.clicked.connect(lambda: self.change_origin(self.ter_focus))
        rst_origin.clicked.connect(lambda: self.change_origin((0, 0)))

        solve.clicked.connect(self.solve)

        parent.addLayout(grid)

        return possc, tersc, ledit, thresh

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

    def resizeEvent(self, event):
        self.rtimer.start(500)
        event.accept()

    def resized(self):
        self.draw_position_map()
        self.draw_terrain_map()

    def reset(self, modified=False):
        self.scores = dict()
        self.resized()
        self.setWindowModified(modified)
        self.ledit.setText("")
        self.pgbar.setValue(0)

    def change_origin(self, origin):
        self.pos_focus = origin
        self.ter_focus = origin
        self.resized()

    def draw_position_map(self):
        ruined = set(self.tilemap.ruined)
        nonruined = set(self.tilemap) - ruined

        ranked = defaultdict(set)
        unranked = set()
        for pos, tilescores in self.scores.items():
            if tilescores is None:
                unranked.add(pos)
            else:
                score = min(score for score, _ in tilescores)
                ranked[score].add(pos)

        ranked = [ranked[score] for score in sorted(ranked)]

        draw_position_map(self.posax, nonruined, ruined, ranked, unranked)

        refresh_canvas(
            fig=self.posfg,
            ax=self.posax,
            canvas=self.poscv,
            origin=self.pos_focus,
            scale=self.possc.value(),
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
            scale=self.tersc.value(),
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
            self.init_window_title()
            self.reset()

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
            self.init_window_title()
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
        self.run_solver.emit((self.tilemap, tile.terrains, self.thresh.value()))
        self.progress = 0
        self.ptimer.start(2000)

    def update_scores(self, msg):
        i, pos, tilescores = msg
        if tilescores:
            self.scores[pos] = tilescores
        else:
            del self.scores[pos]

        self.progress = i + 1

    def update_progress(self):
        self.pgbar.setValue(self.progress)
        if self.progress == self.pgbar.maximum():
            self.ptimer.stop()

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
    main_window.reset()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
