"""
All rights reserved. 
Author: Yang SONG (songyangmri@gmail.com)
"""
import os
import sys
import math
import shutil

import nibabel
import numpy as np
import nibabel as nb
import pydicom

from pathlib import Path
from PySide2 import QtCore
from PySide2.QtWidgets import *

from Utility import *
from GUI.VidaConvert import Ui_VidaConvert


class VidaConvertForm(QWidget):
    def __init__(self, dcm2niix_path):
        super().__init__()
        self.ui = Ui_VidaConvert()
        self.ui.setupUi(self)

        # self.model = QDirModel()
        self.model = QFileSystemModel()
        self.model.setRootPath('/')
        self.model.setReadOnly(False)

        self.ui.treeView.setModel(self.model)
        self.ui.treeView.setSortingEnabled(True)

        self.file_path = Path()
        self.store_folder = ''
        self.dcm2niix_path = dcm2niix_path

        for ind in range(1, 4):
            self.ui.treeView.hideColumn(ind)

        self.ui.buttonConvert.clicked.connect(self.Convert)
        self.ui.button4DDce.clicked.connect(self.MergeDceFolders)
        self.ui.buttonGenerateTvalFile.clicked.connect(self.GenerateDceTime)
        self.ui.buttonAslMergeSingleTI.clicked.connect(self.MergeAslSingleTI)
        self.ui.treeView.clicked.connect(self.TreeViewClick)

    @QtCore.Slot(QtCore.QModelIndex)
    # @QtCore.pyqtSlot(QtCore.QModelIndex)
    def TreeViewClick(self, index):
        indexItem = self.model.index(index.row(), 0, index.parent())
        self.file_path = Path(self.model.filePath(indexItem))

    def _CheckBvecContainAllZero(self, file):
        with open(str(file), 'r') as f:
            for row in f.readlines():
                if any([one != '0' for one in row[:-1].split(' ')]):
                    return False
        return True

    def _AddFakeBvec(self, file):
        b_count = -1
        b_rows = 0
        with open(str(file), 'r') as f:
            for row in f.readlines():
                temp_b_count = len(row[:-1].split(' '))
                if b_count == -1:
                    b_count = temp_b_count
                else:
                    assert(b_count == temp_b_count)

                b_rows += 1
        assert(b_rows == 3)
        assert(b_count > 0)

        with open(str(file), 'w') as f:
            f.write(' '.join(['0' for _ in range(b_count)]) + '\n')
            f.write(' '.join(['0' for _ in range(b_count)]) + '\n')
            f.write(' '.join(['1' for _ in range(b_count)]) + '\n')

    def Dcm2Nii(self, dicom_folder, dest_folder):
        temp_folder = MakeFolder(dest_folder / 'temp')

        cmd_output_folder = " -o \"{}\"".format(str(temp_folder))
        config_text = " -f %3s_%d -m y -v 0 -z n"
        cmd = self.dcm2niix_path + cmd_output_folder + config_text + " \"{}\"".format(str(dicom_folder))
        os.system(cmd)

        for file in temp_folder.iterdir():
            if (not file in dest_folder.iterdir()) and (not file.name.endswith('json')):
                MoveFile(file, dest_folder / file.name, file)

                # 处理b值为0的情况：
                if file.name.endswith('bvec') and self._CheckBvecContainAllZero(dest_folder / file.name):
                    print('Add {} fake b vectors'.format(str(file.name)))
                    self._AddFakeBvec(dest_folder / file.name)

        shutil.rmtree(str(temp_folder))

    def _IsNumber(self, input_data):
        result = False
        try:
            float(input_data)
            result = True
        except ValueError:
            pass

        if result:
            temp = float(input_data)
            if np.isnan(temp):
                return False
            if np.isinf(temp):
                return False

        if not result:
            try:
                import unicodedata
                unicodedata.numeric(input_data)
                result = True
            except (TypeError, ValueError):
                pass

        return result

    def IsValidNumber(self, input_data):
        return self._IsNumber(input_data) and not math.isnan(float(input_data))

    def _RemoveNumber(self, name):
        parts = name.split('_')
        return '_'.join(s for s in parts if not self.IsValidNumber(s))

    def Convert(self):
        message = QMessageBox()

        if self.ui.checkDescription.isChecked():
            convert_name = ('SeriesNumber', 'SeriesDescription')
        else:
            convert_name='SeriesNumber'

        try:
            if self.ui.checkMultiCases.isChecked():
                MultiCasesConvertDicomRoot(self.file_path, self.dcm2niix_path, convert_name)
            else:
                ConvertOneCase(self.file_path, self.dcm2niix_path, convert_name)
        except Exception as e:
            message.about(self, '', e)




        message.about(self, '', 'Convert Done')

    def Convert4DDce(self, folder_paths, root):
        series, times, nums = [], [], []
        for one in folder_paths:
            one_file = one / list(one.glob('*'))[0]
            header = pydicom.dcmread(str(one_file))

            series.append(header.__getattr__('SeriesDescription'))
            nums.append(header.__getattr__('SeriesNumber'))
            times.append(header.__getattr__('AcquisitionTime'))

        times = [24 * 60 * float(one[:2]) + 60 * float(one[2:4]) + float(one[4:]) for one in times]
        datas, sort_times = [], []
        affine = None
        for ind in np.argsort(times):
            curr_time, curr_nums, curr_series = times[ind], nums[ind], series[ind]
            data_file_candidate = list(root.glob('*{}*{}*nii*'.format(curr_nums, curr_series)))
            if len(data_file_candidate) != 1:
                continue
            else:
                data = nb.load(str(data_file_candidate[0])).get_fdata()
                affine = nb.load(str(data_file_candidate[0])).affine
                datas.append(data)
                sort_times.append(times[ind])

        if affine is None:
            QMessageBox(self, '', 'Select at least one folders')
            return

        shape_list = [one.shape for one in datas]
        if shape_list.count(shape_list[0]) == len(shape_list):
            data_4d = np.asarray(datas).transpose((1, 2, 3, 0))
            affine_4d = affine
            image = nibabel.Nifti1Image(data_4d, affine_4d)
            nibabel.save(image, str(root / '{}_4d.nii.gz'.format(series[0])))

            delta_times = (np.array(sort_times) - sort_times[0]).tolist()
            with open(str(root / '{}_4d.tval'.format(series[0])), 'w') as f:
                f.write(",".join(format(x, ".2f") for x in delta_times))
        else:
            QMessageBox(self, '', 'The shape of frames is not same to each other, may chose wrong folders.')
            return

    def MergeDceFolders(self):
        message = QMessageBox()
        file_dialog = QFileDialog(self, 'Select DCE Folders', str(self.file_path.parent / '{}_{}'.format('Convert', self.file_path.name)),
                                  )
        file_dialog.setFileMode(QFileDialog.DirectoryOnly)
        file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        file_view = file_dialog.findChild(QListView, 'listView')

        # to make it possible to select multiple directories:
        if file_view:
            file_view.setSelectionMode(QAbstractItemView.MultiSelection)
        f_tree_view = file_dialog.findChild(QTreeView)
        if f_tree_view:
            f_tree_view.setSelectionMode(QAbstractItemView.MultiSelection)

        if file_dialog.exec():
            paths = file_dialog.selectedFiles()
            paths = [Path(one) for one in paths]
            print(paths)

            if paths[0].parent != paths[-1].parent:
                paths.pop(0)

            print('Merge DCE to 4D files')
            self.Convert4DDce(paths, paths[0].parent)
            message.about(self, '', 'Convert Done')

    def GenerateDceTime(self):
        dlg = QFileDialog(self, 'Select DCE Folders', str(self.file_path.parent / '{}_{}'.format('Convert', self.file_path.name)))
        dlg.setFileMode(QFileDialog.DirectoryOnly)
        dlg.setOption(QFileDialog.ShowDirsOnly)

        if dlg.exec_():
            folder = Path(dlg.selectedFiles()[0])
            times = []
            try:
                for one in folder.iterdir():
                    header = pydicom.read_file(str(one))
                    curr_time = str(header.__getattr__('AcquisitionTime'))
                    if curr_time not in times:
                        times.append(curr_time)

                times = [24 * 60 * float(one[:2]) + 60 * float(one[2:4]) + float(one[4:]) for one in times]
                delta_times = (np.array(times) - times[0]).tolist()
                with open(str(folder.parent / '{}_4d.tval'.format(folder.name)), 'w') as f:
                    f.write(",".join(format(x, ".2f") for x in delta_times))
                QMessageBox().about(self, '', 'Generate Acquisition Time Done.')
            except Exception as e:
                QMessageBox().about(self, '', e.__str__())

    def MergeAslSingleTI(self):
        message = QMessageBox()
        file_dialog = QFileDialog(self, 'Select ASL Single Folders',
                                  str(self.file_path.parent / '{}_{}'.format('Convert', self.file_path.name)),
                                  )
        file_dialog.setFileMode(QFileDialog.DirectoryOnly)
        file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        file_view = file_dialog.findChild(QListView, 'listView')

        # to make it possible to select multiple directories:
        if file_view:
            file_view.setSelectionMode(QAbstractItemView.MultiSelection)
        f_tree_view = file_dialog.findChild(QTreeView)
        if f_tree_view:
            f_tree_view.setSelectionMode(QAbstractItemView.MultiSelection)

        if file_dialog.exec():
            paths = file_dialog.selectedFiles()
            paths = [Path(one) for one in paths]
            print(paths)

            if paths[0].parent != paths[-1].parent:
                paths.pop(0)

            print('Merge Asl to 4D files')
            series, times, nums = [], [], []
            for one in paths:
                one_file = one / list(one.glob('*'))[0]
                header = pydicom.dcmread(str(one_file))

                series.append(header.__getattr__('SeriesDescription'))
                nums.append(header.__getattr__('SeriesNumber'))
                times.append(header.__getattr__('AcquisitionTime'))

            times = [24 * 60 * float(one[:2]) + 60 * float(one[2:4]) + float(one[4:]) for one in times]
            datas, sort_times = [], []
            affine = None
            for ind in np.argsort(times):
                curr_time, curr_nums, curr_series = times[ind], nums[ind], series[ind]
                data_file_candidate = list(paths[0].parent.glob('*{}*{}*nii*'.format(curr_nums, curr_series)))
                if len(data_file_candidate) != 1:
                    continue
                else:
                    data = nb.load(str(data_file_candidate[0])).get_fdata()
                    affine = nb.load(str(data_file_candidate[0])).affine
                    datas.append(data)
                    sort_times.append(times[ind])
                    print('Time: {}, Data Shape: {}'.format(times[ind], data.shape))

            if affine is None:
                message.about(self, '', 'Select at least one folders')
                return

            shape_list = [one.shape for one in datas]
            if shape_list.count(shape_list[0]) == len(shape_list):
                data_4d = np.concatenate(datas, axis=-1)
                affine_4d = affine
                print('Final data4d shape: {}'.format(data_4d.shape))
                image = nibabel.Nifti1Image(data_4d, affine_4d)
                nibabel.save(image, str(paths[0].parent / '{}_4d.nii.gz'.format(series[0])))

                delta_times = (np.array(sort_times) - sort_times[0]).tolist()
                with open(str(paths[0].parent / '{}_4d.aval'.format(series[0])), 'w') as f:
                    f.write(",".join(format(x, ".2f") for x in delta_times))
            else:
                message.about(self, '', 'The shape of frames is not same to each other, may chose wrong folders.')
                return

            message.about(self, '', 'Convert Done')




if __name__ == '__main__':
    dcm2niix_path = str(Path(__file__).parent.parent / r'Utility\dcm2niix.exe')
    app = QApplication(sys.argv)
    main_frame = VidaConvertForm(dcm2niix_path)
    main_frame.show()
    sys.exit(app.exec_())

