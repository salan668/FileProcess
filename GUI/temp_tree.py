"""
All rights reserved. 
Author: Yang SONG (songyangmri@gmail.com)
"""
import os
import sys
import shutil
from pathlib import Path
from PySide2 import QtCore
from PySide2.QtWidgets import *

from GUI.VidaConvert import Ui_VidaConvert


class VidaConvertForm(QWidget):
    def __init__(self, dcm2niix_path):
        super().__init__()
        self.ui = Ui_VidaConvert()
        self.ui.setupUi(self)

        # self.model = QDirModel()
        # self.ui.treeView.setModel(self.model)
        self.model = QFileSystemModel()
        self.model.setRootPath(str(self.file_path))

        self.file_path = Path()

        # for ind in range(1, 4):
        #     self.ui.treeView.hideColumn(ind)

        self.ui.buttonConvert.clicked.connect(self.Convert)
        self.ui.treeView.clicked.connect(self.TreeViewClick)

    @QtCore.Slot(QtCore.QModelIndex)
    def TreeViewClick(self, index):
        indexItem = self.model.index(index.row(), 0, index.parent())
        self.file_path = Path(self.model.filePath(indexItem))

    def Convert(self):
        print(self.file_path)
        current_file = self.file_path
        self.model = QFileSystemModel()
        self.model.setRootPath(str(self.file_path))
        self.ui.treeView.setModel(self.model)
        # self.ui.treeView.setRootIndex(self.model.index(QtCore.QDir.currentPath()))
        # self.ui.treeView.setRootPath(QtCore.QDir.currentPath())

        # selectionmode = QAbstractItemView.SelectionMode(1)
        # self.ui.treeView.setSelectionMode(selectionmode)
        # self._origrootindex = self.ui.treeView.rootIndex()
        # print(self._origrootindex)



if __name__ == '__main__':
    dcm2niix_path = str(Path(__file__).parent.parent / r'Utility\dcm2niix.exe')
    app = QApplication(sys.argv)
    main_frame = VidaConvertForm(dcm2niix_path)
    main_frame.show()
    sys.exit(app.exec_())