"""
All rights reserved. 
Author: Yang SONG (songyangmri@gmail.com)
"""

import os

import shutil
import traceback
from pathlib import Path
import pydicom

from Utility.IO import MakeFolder, CopyFile, MakeEffectFileName, MoveFile

class DicomShareInfo:
    def __init__(self, header=None):
        self.__header = header

    def IsDICOM(self, file_path):
        file_path = str(file_path)
        if file_path.endswith('.exe'):
            return False
        if os.path.isdir(file_path):
            return False
        with open(file_path, 'rb') as file:
            file.seek(128)
            key = file.read(4)
            if key == b'DICM':
                return True
            else:
                return False

    def IsDICOMFolder(self, folder_path):
        for file in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file)
            if not self.IsDICOM(file_path):
                return False
        return True

    def LoadCaseFolder(self, case_folder):
        if isinstance(case_folder, Path):
            case_folder = str(case_folder)

        if not os.path.exists(case_folder):
            print('Check the case folder path: ', case_folder)
            return False

        for root, dir, files in os.walk(case_folder):
            for file in files:
                file_path = os.path.join(root, file)
                if self.IsDICOM(file_path):
                    try:
                        self.__header = pydicom.dcmread(file_path)
                        return True
                    except Exception as e:
                        if hasattr(e, 'message'):
                            print(e.message)
                        else:
                            print(e)
                            print('Load DICOM File failed: ', case_folder)
                            return False

    def GetManufacture(self):
        if self.__header:
            return self.__header.Manufacturer
        else:
            print('Please load the case folder first')

    def GetPatientID(self):
        if self.__header:
            return self.__header.PatientID
        else:
            print('Please load the case folder first')

    def GetPatientName(self):
        if self.__header:
            return self.__header.PatientName
        else:
            print('Please load the case folder first')

    def GetSeriesDescription(self):
        if self.__header:
            return self.__header.SeriesDescription
        else:
            print('Please load the case folder first')

    def GetSeriesNumber(self):
        if self.__header:
            return self.__header.SeriesNumber
        else:
            print('Please load the case folder first')

    def GetInstitution(self):
        if self.__header:
            return self.__header.InstitutionName
        else:
            print('Please load the case folder first')

    def DecompressSiemensDicom(self, data_folder, store_folder,
                               gdcm_path=r"D:\MyCode\Lib\gdcm\GDCMGITBin\bin\Release\gdcmconv.exe"):
        file_list = os.listdir(data_folder)
        file_list.sort()
        for file in file_list:
            file_path = os.path.join(data_folder, file)
            # store_file = os.path.join(store_folder, file+'.IMA')
            store_file = os.path.join(store_folder, file)

            cmd = gdcm_path + " --raw \"{:s}\" \"{:s}\"".format(file_path, store_file)
            os.system(cmd)

    def DecompressDicomDcmtk(self, data_folder, store_folder,
                             # gdcm_path=r"C:\ProgramData\chocolatey\lib\dcmtk\tools\dcmtk-3.6.4-win64-dynamic\bin\dcmdjpeg.exe"):
                             gdcm_path=r"d:\MyCode\Lib\Dcmtk\Release\dcmdjpeg.exe"):
        file_list = os.listdir(data_folder)
        file_list.sort()
        for file in file_list:
            file_path = os.path.join(data_folder, file)
            # store_file = os.path.join(store_folder, file+'.IMA')
            store_file = os.path.join(store_folder, file)

            cmd = gdcm_path + " \"{:s}\" \"{:s}\"".format(file_path, store_file)
            os.system(cmd)


def RemoveNumber(name):
    return ''.join([s for s in name if s not in '0123456789'])

def _CheckBvecContainAllZero(file):
    with open(str(file), 'r') as f:
        for row in f.readlines():
            if any([one != '0' for one in row[:-1].split(' ')]):
                return False
    return True

def _AddFakeBvec(file):
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

def ExtractFile(folder: Path, dicom_info=DicomShareInfo()):
    if folder.is_dir():
        for file in folder.iterdir():
            if file.is_dir():
                for inner_file in ExtractFile(file):
                    yield inner_file
            else:
                if dicom_info.IsDICOM(str(file)):
                    yield file

def OneCaseConvertDicomFolder(source_case, dest_case, check=None, convert_name=('SeriesNumber', 'SeriesDescription')):
    """
    check: To make sure the source case is one person.
    """
    if isinstance(convert_name, str):
        convert_name = [convert_name]

    descript = {}
    dest_case = MakeFolder(dest_case)
    patient_check = None

    for file in ExtractFile(source_case):
        if file.name == 'DICOMDIR':
            continue

        head = pydicom.dcmread(str(file))

        if check is not None:
            if patient_check is None:
                patient_check = head.__getattr__(check)
            else:
                assert (patient_check == head.__getattr__(check))

        for one in convert_name:
            if not hasattr(head, one):
                raise ValueError('Dicom Header of {} has no {}'.format(file, one))

        folder_name = ''
        for one in convert_name:
            if one == 'SeriesNumber':
                folder_name += '{:04d}'.format(int(head.__getattr__(one)))
            else:
                folder_name += str(head.__getattr__(one))
            folder_name += '_'
        folder_name = folder_name[:-1]

        folder_name = MakeEffectFileName(folder_name)
        dest_series_fold = MakeFolder(dest_case / folder_name)
        CopyFile(file, dest_series_fold / file.name)

        if 'SeriesDescription' in convert_name:
            series_descript = str(head.__getattr__('SeriesDescription'))
            series_number = str(head.__getattr__('SeriesNumber'))

            if series_descript not in descript.keys():
                descript[series_descript] = []
            if hasattr(head, 'AcquisitionTime'):
                series_acqtime = str(head.__getattr__('AcquisitionTime'))
                value = (series_number, float(series_acqtime))
                if value not in descript[series_descript]:
                    descript[series_descript].append(value)
    return descript


def SortDicom(source_case, dest_case, convert_name=('SeriesNumber', 'SeriesDescription')):
    if isinstance(convert_name, str):
        convert_name = [convert_name]

    for file in ExtractFile(source_case):
        if file.name == 'DICOMDIR':
            continue
        head = pydicom.dcmread(str(file))

        for one in convert_name:
            if not hasattr(head, one):
                raise ValueError('Dicom Header of {} has no {}'.format(file, one))

        folder_name = ''
        for one in convert_name:
            if one == 'SeriesNumber':
                folder_name += '{:04d}'.format(int(head.__getattr__(one)))
            else:
                folder_name += str(head.__getattr__(one))
            folder_name += '_'
        folder_name = folder_name[:-1]

        folder_name = MakeEffectFileName(folder_name)
        dest_series_fold = MakeFolder(dest_case / folder_name)
        CopyFile(file, dest_series_fold / file.name)

def Dcm2Nii(dicom_folder, dest_folder, dcm2niix_path):
    temp_folder = MakeFolder(dest_folder / 'temp')

    cmd_output_folder = " -o \"{}\"".format(str(temp_folder))
    config_text = " -f %3s_%d -m y -v 0 -z n"
    cmd = dcm2niix_path + cmd_output_folder + config_text + " \"{}\"".format(str(dicom_folder))
    os.system(cmd)

    for file in temp_folder.iterdir():
        if (not file in dest_folder.iterdir()) and (not file.name.endswith('json')):
            MoveFile(file, dest_folder / file.name, file)

            # 处理b值为0的情况：
            if file.name.endswith('bvec') and _CheckBvecContainAllZero(dest_folder / file.name):
                print('Add {} fake b vectors'.format(str(file.name)))
                _AddFakeBvec(dest_folder / file.name)

    shutil.rmtree(str(temp_folder))

def ConvertOneCase(source_case: Path, dcm2niix_path, convert_name=('SeriesNumber', 'SeriesDescription')):
    dest_case = Path()
    try:
        dest_case = source_case.parent / 'Convert_{}'.format(source_case.name)
        SortDicom(source_case, dest_case, convert_name)
    except Exception as e:
        print(traceback.format_exc())
        shutil.rmtree(dest_case)

    for one_series in dest_case.iterdir():
        if one_series.is_dir():
            Dcm2Nii(one_series, dest_case, dcm2niix_path)

def MultiCasesConvertDicomRoot(source_root: Path, dcm2niix_path, convert_name=('SeriesNumber', 'SeriesDescription')):
    for one_case in source_root.glob('*'):
        if one_case.is_dir():
            ConvertOneCase(one_case, dcm2niix_path, convert_name)


if __name__ == '__main__':
    OneCaseConvertDicomFolder(Path(r'C:\Users\Suns\Desktop\Convert_01410000\7'),
                              Path(r'C:\Users\Suns\Desktop\Convert_01410000'))
