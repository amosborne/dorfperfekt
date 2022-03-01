from PySide6 import QtWidgets
import sys
import matplotlib
from matplotlib.animation import TimedAnimation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

def on_click(event):
    if event.inaxes is not None:
        print(event.xdata, event.ydata)
    else:
        print('Clicked ouside axes bounds but inside plot window')

if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    wid = QtWidgets.QWidget()
    wid.resize(250, 150)
    grid = QtWidgets.QGridLayout(wid)
    fig = Figure()
    ax = fig.add_subplot(1,1,1)
    ax.plot([0,1],[0,1])
    ax.set_aspect("equal")
    ax.axis("off")
    canvas = FigureCanvas(fig)
    canvas.callbacks.connect('button_press_event', on_click)
    grid.addWidget(canvas, 0, 0)
    wid.show()
    sys.exit(app.exec())
