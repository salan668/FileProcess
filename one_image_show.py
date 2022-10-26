"""
All rights reserved. 
Author: Yang SONG (songyangmri@gmail.com)
"""
from PySide2 import QtWidgets
from PySide2.QtWidgets import QMainWindow, QApplication
import pyqtgraph as pg


# class OneView(pg.ImageView):
#     def __init__(self, parent=None, name="ImageView", view=None, imageItem=None, *args):
#         super().__init__(self, parent, name, view, imageItem, *args)
#         self.ui.roiBtn.hide()
#         self.ui.menuBtn.hide()
#         self.ui.histogram.hide()
#         self.show()
#
#
# if __name__ == '__main__':
#     win = QMainWindow()
#     win.resize(500, 500)
#     imv = pg.ImageView()
#     win.setCentralWidget(imv)
#     win.show()
#     win.setWindowTitle('test')
#
#     app = QApplication([])
#     app.exec()


class WdgPlot(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(WdgPlot, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)

        pw = pg.PlotWidget()
        pw.plot([1,2,3,4])
        layout.addWidget(pw)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    w = WdgPlot()
    w.show()
    sys.exit(app.exec_())