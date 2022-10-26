"""
All rights reserved. 
Author: Yang SONG (songyangmri@gmail.com), Cai-xia Fu (caixia.fu@siemens-healthineers.com)
"""
from pathlib import Path
import numpy as np
import nibabel as nb

from Utility.IO import LoadDwiNii

class PesudoMRE(object):
    def __init__(self):
        self.alpha = -12740.0
        self.beta = 14.0
        self.low_b = 200
        self.high_b = 1500

    def Run(self, dwi_file, bvalue_file: Path = None, store_folder: Path=None):
        images, bvalus, _ = LoadDwiNii(dwi_file, bvalue_file)
        low_index = bvalus.index(self.low_b)
        high_index = bvalus.index(self.high_b)
        if low_index == -1 or high_index == -1:
            return None

        image_low, image_high = images[low_index], images[high_index]
        data_low = image_low.get_fdata()
        data_high = image_high.get_fdata()

        sADC = np.log(np.divide(data_low, data_high)) / (self.high_b - self.low_b)
        np.nan_to_num(sADC, nan=0.)

        u_dwi = self.alpha * sADC + self.beta
        u_dwi[u_dwi > 32] = 30
        u_dwi[u_dwi < -30] = 0

        sADC *= 1e6
        sADC = np.clip(sADC, a_min=0, a_max=3000)

        sADC_image = nb.Nifti1Image(sADC, image_high.affine)
        u_dwi_image = nb.Nifti1Image(u_dwi, image_high.affine)

        if store_folder is not None:
            nb.save(sADC_image, str(store_folder / 'sADC.nii.gz'))
            nb.save(u_dwi_image, str(store_folder / 'uDWI.nii.gz'))



if __name__ == '__main__':
    mre = PesudoMRE()
    mre.Run(r'C:\Users\Suns\Desktop\BAO_CHENG_002115931\003_resolve_diff_tra_spair-DKI_TRACEW.nii', store_folder=Path(r'C:\Users\Suns\Desktop\BAO_CHENG_002115931'))
