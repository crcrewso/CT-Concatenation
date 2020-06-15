import os
import sys
import DisplayCT
import matplotlib.pyplot as plt
import numpy as np 





# set path and load files 
path = sys.argv[-1]

import vtkplotter
volume = vtkplotter.load(path, threshold=-500)
vtkplotter.show(volume, axes=True)



patient_dicom = DisplayCT.load_scan(path)
patient_pixels = DisplayCT.get_pixels_hu(patient_dicom)
#sanity check
plt.imshow(patient_pixels[326], cmap=plt.cm.bone)