#! /usr/bin/env python3
# vim: et sw=4 ts=4 fdm=marker

import sys
import pickle

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class Grid:

    default_path = "/tmp"

    __default_filename = default_path + "/" + "default_grid_16x8"

    def __init__(self, filename = None):

        print("creating grid from file %s" % (filename))

        if filename:
            self.restore(filename)
        else:
            self.__default_init()

    def __default_init(self):

        try:
            self.restore(self.__default_filename)
        except:

            # in a case when the default file doesn't exist, try to create it
            self.__map = {
                " ": "Empty",
                "one": "One bird",
                "two": "Two birds",
                "three": "Three birds",
                "four": "Four birds",
                "five": "Five birds",
            }
            self.__size = (16, 8)
            self.__data = [['' for x in range(self.__size[0])] for y in range(self.__size[1])]

            self.save(self.__default_filename)

    def keys(self):
        return self.__map.keys()

    def name(self, key):
        return self.__map[key]

    def match_key(self, key):
        return [k for k in self.keys() if (key == k[:len(key)])]

    def size(self):   return self.__size[:]
    def width(self):  return self.__size[0]
    def height(self): return self.__size[1]

    def set_size(self, w, h):
        self.__size = (w, h)

    def set_legend_value(self, key, value):
        self.__map[key] = value

    def data(self, x, y):
        return self.__data[y][x]

    def set_data(self, x, y, X):
        self.__data[y][x] = X

    def save(self, filename):
        obj = (self.__size, self.__map, self.__data)
        pickle.dump(obj, open(filename, "wb"))

    def restore(self, filename):
        self.__size, self.__map, self.__data = pickle.load(open(filename, "rb"))

    def export(self, filename):
        '''
        Exports data in a csv file in the following format:

            'Width', 'Height', 'Key 1', 'Key 2', ..., 'Key N'
            <width>, <height>, <# of objects under key 1>, ...
        '''

        keys = self.__map.keys()
        hist = {}

        w, h = self.__size
        for y in range(h):
            for x in range(w):
                k = self.data(x, y)
                if not k:
                    k = ' '

                if k in hist:
                    hist[k] += 1
                else:
                    hist[k] = 1

        with open(filename, "w") as f:

            s = '"Width", "Height"'
            for key in keys:
                s += ', "%s"' % (self.name(key))
            s += "\r\n"

            s += '%s, %s' % (w, h)
            for key in keys:
                if key in hist:
                    s += ', %s' % (hist[key])
                else:
                    s += ', 0'
            s += "\r\n"

            f.write(s)

class GridSetupDialog(QDialog):

    def __init__(self, parent=None, saved = None):

        super(GridSetupDialog, self).__init__(parent)

        labelGridWidth = QLabel("Grid Width")
        labelGridHeight = QLabel("Grid Height")
        self.gridWidth = QLineEdit()
        self.gridHeight = QLineEdit()

        self.sl = [] # shortcuts
        self.dl = [] # descriptions
        for i in range(10):
            sl = QLineEdit()
            sl.setFixedWidth(100)
            self.sl.append(sl)

            self.dl.append(QLineEdit())

        self.sl[0].setStyleSheet("color: grey;")
        self.dl[0].setStyleSheet("color: grey;")

        self.saveButton = QPushButton("Save")
        self.loadButton = QPushButton("Load")

        self.saveButton.clicked.connect(self.save)
        self.loadButton.clicked.connect(self.load)

        self.buttonOk = QPushButton("OK")
        self.buttonCancel = QPushButton("Cancel")

        self.buttonOk.clicked.connect(lambda: self.done(1))
        self.buttonCancel.clicked.connect(lambda: self.done(0))

        L = QGridLayout()
        L.addWidget(labelGridWidth,     0, 0)
        L.addWidget(self.gridWidth,     0, 1)
        L.addWidget(labelGridHeight,    1, 0)
        L.addWidget(self.gridHeight,    1, 1)

        for i in range(10):
            L.addWidget(self.sl[i], 2 + i, 0)
            L.addWidget(self.dl[i], 2 + i, 1)

        L.addWidget(self.saveButton, 13, 0)
        L.addWidget(self.loadButton, 13, 1)

        L.addWidget(self.buttonOk,     14, 0)
        L.addWidget(self.buttonCancel, 14, 1)
        self.setLayout(L)

        print("saved = %s" %(saved))

        if saved:

            try:
                self.load(saved)
            except:
                self.fill(Grid())

    def grid(self):

        grid = Grid()

        for i in range(10):
            short = self.sl[i].text()
            full = self.dl[i].text()

            # replace <space> with a real space character
            if i == 0:
                short = ' '

            if not full or not short:
                break

            grid.set_legend_value(short, full)

        grid.set_size(int(self.gridWidth.text()), int(self.gridHeight.text()))

        return grid

    def save(self):

        filename, _ = QFileDialog.getSaveFileName(self, "Create/Update File", Grid.default_path)

        if not filename:
            return

        self.grid().save(filename)

    def fill(self, grid):
        self.gridWidth.setText(str(grid.width()))
        self.gridHeight.setText(str(grid.height()))

        i = 0
        for k in grid.keys():
            self.sl[i].setText(k)
            self.dl[i].setText(grid.name(k))
            i += 1

        # some special conditions: the first key is always <space>
        self.sl[0].setText("<Space>")
        self.sl[0].setReadOnly(True)
        self.dl[0].setReadOnly(True)

    def load(self, filename = None):

        if not filename:
            filename, _ = QFileDialog.getOpenFileName(self, "Open File", Grid.default_path)

        if not filename:
            return

        grid = Grid(filename)
        self.fill(grid)

    def gimme_grid(self):
        return self.grid()

class GridWidget(QLabel):

    __special_keys = (
             Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down,
             Qt.Key_H, Qt.Key_L, Qt.Key_K, Qt.Key_J
        )

    __shortcut_keys = "0123456789qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM"

    def __init__(self, parent):
        super(GridWidget, self).__init__()

        self.parent = parent

        self.__shortcut_timer = QTimer()
        self.__shortcut_timer.setSingleShot(True)
        self.__shortcut_timer.timeout.connect(self.__timer_shot)

        self.__shortcut_reset()

        self.grid = None

    def set_grid(self, grid):

        self.grid = grid

        w, h = self.grid.size()
        self.current = (0, 0)
        self.update()

    def keyPressSpecial(self, key):

        if key == Qt.Key_Left or key == Qt.Key_H:
            self.move_left()
        elif key == Qt.Key_Right or key == Qt.Key_L:
            self.move_right()
        elif key == Qt.Key_Up or key == Qt.Key_K:
            self.move_up()
        elif key == Qt.Key_Down or key == Qt.Key_J:
            self.move_down()

    def __timer_shot(self):
        self.__shortcut_reset()

    def __shortcut_reset(self):
        self.__shortcut = ""
        self.__shortcut_timer.stop()
        self.parent.setStatusMessage(self.__shortcut)

    def keyPressShortcut(self, key):

        self.__shortcut += chr(key | 0x20)
        print(self.__shortcut)
        self.parent.setStatusMessage(self.__shortcut)

        matched = self.grid.match_key(self.__shortcut)
        if len(matched) == 1:
            self.setLabel(matched[0])
            self.__shortcut_reset()
        elif len(matched) > 1:
            self.__shortcut_timer.start(1000)
        else:
            self.__shortcut_reset()

    def keyPress(self, key):

        if not self.grid:
            return

        # move operations
        if key in GridWidget.__special_keys:
            self.keyPressSpecial(key)
        elif key == Qt.Key_Space:
            self.setLabel(" ")
        elif key > 0 and key < 255 and (chr(key) in GridWidget.__shortcut_keys):
            self.keyPressShortcut(key)

    def move(self, offset):
        dx, dy = offset
        x, y = self.current
        w, h = self.grid.size()

        x = (x + dx + w) % w
        y = (y + dy + h) % h

        self.current = x, y
        self.update()

    def move_left(self): self.move((-1, 0))
    def move_right(self): self.move((1, 0))
    def move_up(self): self.move((0, -1))
    def move_down(self): self.move((0, 1))

    def setLabel(self, X = ''):
        x, y = self.current
        self.grid.set_data(x, y, X)

        self.move_right()
        if self.current[0] == 0:
            self.move_down()

    def drawGrid(self, painter):

        if not self.grid:
            return

        w, h = self.grid.size()

        dX = self.width() // w
        dY = self.height() // h

        painter.setBrush(QColor(255, 0, 0, 20))
        for y in range(h):
            for x in range(w):
                try:
                    X = self.grid.data(x, y)

                    if X:
                        rect = QRect(x*dX, y*dY, dX, dY)
                        painter.drawRect(rect)

                        painter.save()
                        painter.setPen(QColor(0, 255, 0, 100))
                        painter.drawText(rect, Qt.AlignCenter, "%s" % X)
                        painter.restore()
                except:
                    print ("bad parameters", self.current, x, y)

        for y in range(h):
            for x in range(w):

                rect = QRect(x*dX, y*dY, dX, dY)
                painter.drawPolyline(QPolygon(rect))

        x, y = self.current
        painter.setBrush(QColor(0, 255, 0, 5))
        pen = QPen(QColor(0, 255, 0, 100))
        pen.setWidth(5)
        painter.setPen(pen)
        rect = QRect(x*dX, y*dY, dX, dY)
        painter.drawRect(rect)

    def paintEvent(self, e):
        QLabel.paintEvent(self, e)

        painter = QPainter(self)
        self.drawGrid(painter)

    def save(self, filename):

        if not filename.endswith('.grid'):
            filename += '.grid'

        self.grid.save(filename)

    def open(self, filename):

        if not filename.endswith('.grid'):
            filename += '.grid'

        self.set_grid(Grid())

        try:
            self.grid.restore(filename)
        except:
            pass

    def export(self, filename):

        if not filename.endswith('.csv'):
            filename += '.csv'

        self.grid.export(filename)

class ImageMarker(QMainWindow):

    __name = "Image Marker"

    __last_grid = "/tmp/last_grid"

    def __init__(self):
        super(ImageMarker, self).__init__()
        self.setWindowTitle(self.__name)

        self.statusBar = QStatusBar()
        self.createCentralWidget()
        self.createActions()
        self.createToolBar()
        self.createMenus()
        self.setStatusBar(self.statusBar)

        # debug
        self.open("birds.jpg")
        self.action_zoom_fit.setEnabled(True)
        self.action_zoom_fit.setChecked(True)
        self.zoomFit()

    def keyPressEvent(self, e):

        if e.key() == Qt.Key_Escape:
            self.close()

        self.gridWidget.keyPress(e.key())

    def setStatusMessage(self, status):
        self.statusBar.showMessage(status)

    def createCentralWidget(self):
        """
        Our base widget is a QLabel-based object,
        we will pass all keypress events to it
        """

        self.gridWidget = GridWidget(self)
        self.gridWidget.setBackgroundRole(QPalette.Base)
        self.gridWidget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.gridWidget.setScaledContents(True)

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.gridWidget)
        self.setCentralWidget(self.scrollArea)

    def createActions(self):
        self.action_open = QAction("&Open...", self, shortcut="Ctrl+O", triggered=self.open)
        self.action_save = QAction("&Save...", self, shortcut="Ctrl+S", triggered=self.save)
        self.action_save_as = QAction("Save &As...", self, shortcut="Ctrl+Shift+S", triggered=self.save_as)
        self.action_export = QAction("&Export...", self, shortcut="Ctrl+E", triggered=self.export)
        self.action_exit = QAction("E&xit",    self, shortcut="Ctrl+Q", triggered=self.close)

        self.action_setup_grid    = QAction("Setup Grid", self, enabled=True, triggered=self.setupGrid)

        self.action_zoom_in  = QAction("Zoom &In", self, shortcut="Ctrl++", enabled=False, triggered=self.zoomIn)
        self.action_zoom_out = QAction("Zoom &Out", self, shortcut="Ctrl+-", enabled=False, triggered=self.zoomOut)
        self.action_zoom_11 = QAction("Zoom 1:1", self, enabled=False, triggered=self.zoom11)
        self.action_zoom_fit = QAction("Zoom to fit", self, enabled=False, checkable=True, triggered=self.zoomFit)

    def createToolBar(self):
        self.toolbar = self.addToolBar("Foo")

        self.toolbar.addAction(self.action_zoom_in)
        self.toolbar.addAction(self.action_zoom_out)
        self.toolbar.addAction(self.action_zoom_11)
        self.toolbar.addAction(self.action_zoom_fit)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.action_setup_grid)

    def createMenus(self):
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.action_open)
        self.fileMenu.addAction(self.action_save)
        self.fileMenu.addAction(self.action_save_as)
        self.fileMenu.addAction(self.action_export)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.action_exit)

        self.editMenu = QMenu("&Edit", self)
        self.editMenu.addAction(self.action_setup_grid)

        self.viewMenu = QMenu("&View", self)
        self.viewMenu.addAction(self.action_zoom_in)
        self.viewMenu.addAction(self.action_zoom_out)
        self.viewMenu.addAction(self.action_zoom_11)
        self.viewMenu.addAction(self.action_zoom_fit)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.editMenu)
        self.menuBar().addMenu(self.viewMenu)

    def open(self, fileName = None):

        if not fileName:
            fileName, _ = QFileDialog.getOpenFileName(self, "Open File", QDir.currentPath())

        if not fileName:
            return

        image = QImage(fileName)
        if image.isNull():
            QMessageBox.information(self, self.__name, "Can't open %s" % fileName)
            return

        self.gridWidget.setPixmap(QPixmap.fromImage(image))
        self.scaleFactor = 1.0

        self.action_zoom_fit.setEnabled(True)
        self.updateActions()

        if not self.action_zoom_fit.isChecked():
            self.gridWidget.adjustSize()

        self.update()

        self.fileName = fileName

        self.gridWidget.open(fileName)

    def updateActions(self):
        self.action_zoom_in.setEnabled(not self.action_zoom_fit.isChecked())
        self.action_zoom_out.setEnabled(not self.action_zoom_fit.isChecked())
        self.action_zoom_11.setEnabled(not self.action_zoom_fit.isChecked())

    def save(self):
        self.gridWidget.save(self.fileName)

    def save_as(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save File", Grid.default_path) # XXX: the last path

        if not filename:
            return

        self.gridWidget.save(filename)

    def export(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Export CSV", Grid.default_path) # XXX: the last path

        if not filename:
            return

        self.gridWidget.export(filename)

    def scaleImage(self, factor):
        self.scaleFactor *= factor
        self.gridWidget.resize(self.scaleFactor * self.gridWidget.pixmap().size())
        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value() + ((factor - 1) * scrollBar.pageStep()/2)))

    def zoomIn(self):
        self.scaleImage(1.25)

    def zoomOut(self):
        self.scaleImage(0.8)

    def zoom11(self):
        self.gridWidget.adjustSize()
        self.scaleFactor = 1.0

    def zoomFit(self):
        fit = self.action_zoom_fit.isChecked()
        self.scrollArea.setWidgetResizable(fit)
        self.updateActions()

    def setupGrid(self):

        dialog = GridSetupDialog(self, saved = self.__last_grid)
        if not dialog.exec_():
            return

        grid = dialog.gimme_grid()
        if grid:
            self.gridWidget.set_grid(grid)
            grid.save(self.__last_grid)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    x = ImageMarker()
    x.showMaximized()
    sys.exit(app.exec_())
