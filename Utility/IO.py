"""
All rights reserved. 
Author: Yang SONG (songyangmri@gmail.com)
"""

import os
import shutil
from pathlib import Path

import numpy as np
import nibabel as nb

def CopyFile(source_path, dest_path, is_replace=True):
    source_path = str(source_path)
    dest_path = str(dest_path)
    if not os.path.exists(source_path):
        print('File does not exist: ', source_path)
        return None
    if not (os.path.exists(dest_path) and (not is_replace)):
        shutil.copyfile(source_path, dest_path)


def MakeFolder(folder_path):
    try:
        if isinstance(folder_path, str):
            folder_path = Path(folder_path)
        if not folder_path.exists():
            print('Making {}'.format(folder_path.name))
            folder_path.mkdir()
    except FileNotFoundError:
        folder_path = str(folder_path)
        os.makedirs(folder_path)
        folder_path = Path(folder_path)
    return folder_path

def MoveFile(source_path, dest_path, is_replace):
    source_path = str(source_path)
    dest_path = str(dest_path)
    if not os.path.exists(source_path):
        print('File does not exist: ', source_path)
        return None
    if (not os.path.exists(dest_path)) or is_replace:
        shutil.move(source_path, dest_path)

def MakeEffectFileName(raw_name):
    un_effect_name_list = ['*', '.', '\"', '/', '\\', ':', ';', '|', ',', '<', '>', '&', '*', '?']
    for one in un_effect_name_list:
        if one in raw_name:
            raw_name = raw_name.replace(one, '_')

    return raw_name

def SplitFileSuffix(file_path: Path):
    str_path = str(file_path)
    if str_path.endswith('nii.gz'):
        suffext = 'nii.gz'
        name = str_path[:-len('.nii.gz')]
    else:
        name, suffext = os.path.splitext(str_path)

    return name, suffext

def LoadDwiNii(data_path, bval_path = None, bvec_path = None):
    name = SplitFileSuffix(data_path)[0]
    if bval_path is None:
        bval_path = name + '.bval'
    if bvec_path is None:
        bvec_path = name + '.bvec'

    data_4d = nb.load(data_path)
    data_list = nb.funcs.four_to_three(data_4d)

    with open(bval_path, 'r') as f:
        bval_list = f.readline()[:-1]
        bval_list = list(map(int, bval_list.split(' ')))

    bvec_array = []
    with open(bvec_path, 'r') as f:
        bvec_array.append(f.readline()[:-1].split(' '))
        bvec_array.append(f.readline()[:-1].split(' '))
        bvec_array.append(f.readline()[:-1].split(' '))
    bvec_array = np.asarray(bvec_array, dtype=float)

    assert(len(data_list) == len(bval_list))
    assert (len(data_list) == bvec_array.shape[1])

    return data_list, bval_list, bvec_array
