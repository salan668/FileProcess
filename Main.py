"""
All rights reserved. 
Author: Yang SONG (songyangmri@gmail.com)
"""
import sys
from pathlib import Path
from PySide2.QtWidgets import *

from GUI.VidaConvertForm import VidaConvertForm

if __name__ == '__main__':
    dcm2niix_path = str(Path(__file__).parent / r'Utility\dcm2niix.exe')
    app = QApplication(sys.argv)
    main_frame = VidaConvertForm(dcm2niix_path)
    main_frame.show()
    sys.exit(app.exec_())