import pydicom
import os
import numpy
import matplotlib.pyplot as plt
import glob

SCCImagepath="//svstoroprd01/VA_Transfer/DICOM/standard/"
#SCCImagepath="//sccvis2/va_data$/filedata/DICOM/"
SCCTBIImagepath="//sccsrv1/dept/RTClinic/TBI PROGRAM/Imaging Data/"
#SCCTBIImagepath="//sccsrv1/Lap/"

print("Welcome to the 2nd CT concatenation program programed at SCC\n")
print("Enter in the patient number that you would like to concatenatate, the last 8 folders are listed below.\n")

all_subdirs=[]
for x in range(0, 8):
    all_subdirs.append(sorted(glob.glob(os.path.join(SCCImagepath, '*/')), key=os.path.getmtime)[-x])


for x in range(0, 8):
	fullname=all_subdirs[x]
	shortname=fullname.split("\\")
	if ('delete' in shortname[1])==False:
		print(shortname[1])


var = input("\nPlease enter the patient's ID number: ")
print ("You entered: "+ var) 

OriginalPath=SCCImagepath+var+"/"
print("Path of folder is " +OriginalPath)
pathout=SCCImagepath+var+"-Concantenated/"
pathoutTBI=SCCTBIImagepath+var+"-Concantenated/"

#print("Output path 1 is " +pathout)
#print("Output path 2 is " +pathoutTBI)

xshift = input("Enter in the laterial shift needed (cm): ")
xshift_value=int(float (xshift)*10)
print ("You entered: "+ str(xshift_value) +" mm") 


if os.path.exists(OriginalPath):
	if not os.path.exists(pathout):
		os.makedirs(pathout)
	if not os.path.exists(pathoutTBI):
		os.makedirs(pathoutTBI)
	num_files = len([f for f in os.listdir(OriginalPath)if os.path.isfile(os.path.join(OriginalPath, f))])
	print("That folder has "+str(num_files)+" total files")
else:
    print("Paitent folder "+var+" dose not exist!")
    exit()


for root, dirs, filenames in os.walk(OriginalPath):
    for f in filenames:
        filepath=OriginalPath+f
        plan=pydicom.read_file(filepath)
        if ("scout" in plan.SeriesDescription):
        	num_files=num_files-1
        	print("Scout file ("+f+") removed from folder, new total for folder is "+str(num_files)+" files")
        	os.remove(filepath) 


coronal_plane=[]
coronal_grid = numpy.zeros((num_files, 4, 512))
i=0
fcount=0
head_count=0
feet_count=0
hfound=0


for root, dirs, filenames in os.walk(OriginalPath):
    for f in filenames:
        filepath=OriginalPath+f
        plan=pydicom.read_file(filepath)
        if (("head" in plan.StudyDescription) or ("HTG" in plan.StudyDescription) or ("Head" in plan.StudyDescription) or ("HEAD" in plan.StudyDescription) or (plan.StudyDescription=="TBI")):
                SeriesInstanceUID=plan.SeriesInstanceUID
                StudyInstanceUID=plan.StudyInstanceUID
                FrameOfReferenceUID=plan.FrameOfReferenceUID
                StudyID=plan.StudyID
                SOPInstanceUID_base=".".join(plan.SOPInstanceUID.split(".")[:-1])
                StudyTime=plan.StudyTime
                SeriesTime=plan.SeriesTime
                SeriesNumber=plan.SeriesNumber
                hfound=1
                break
    break

if hfound==1: 
    print("Images are TBI scans")
else:
    print("Images are not TBI scans")
    exit()

# Find the Series number for head scans
for root, dirs, filenames in os.walk(OriginalPath):
    for f in filenames:
        filepath=OriginalPath+f
        plan=pydicom.read_file(filepath)
        if (("head" in plan.StudyDescription) or ("Head" in plan.StudyDescription) or ("HTG" in plan.StudyDescription) or ("HEAD" in plan.StudyDescription) or (plan.StudyDescription=="TBI")):
        	fcount=fcount+1
        	head_count=head_count+1
        	if (plan.SliceLocation<0.0):
        	    print("Negative head image found at slice position :  " + str(plan.SliceLocation))

        elif (("feet" in plan.StudyDescription) or ("Feet" in plan.StudyDescription) or ("FOOT" in plan.StudyDescription)  or ("Foot" in plan.StudyDescription) or ("FEET" in plan.StudyDescription) or ("Ft" in plan.StudyDescription) or ("FTG" in plan.StudyDescription)):
        	feet_count=feet_count+1
        	fcount=fcount+1
        	plan.SeriesInstanceUID=SeriesInstanceUID
        	plan.StudyInstanceUID=StudyInstanceUID
        	plan.FrameOfReferenceUID=FrameOfReferenceUID
        	plan.StudyID=StudyID
        	plan.StudyTime=StudyTime
        	plan.SeriesTime=SeriesTime
        	plan.SeriesNumber=SeriesNumber
        	if (plan.SliceLocation<0.0):
        		print("Negative foot image found at slice position :  " + str(plan.SliceLocation))
        	plan.SliceLocation=-1*plan.SliceLocation
        	plan.ImagePositionPatient[2]=plan.SliceLocation
        	plan.ImagePositionPatient[0]=plan.ImagePositionPatient[0]+xshift_value
        	#print(plan.ImagePositionPatient)
        	plan.InstanceNumber=num_files-plan.InstanceNumber+1
        	a=plan.pixel_array
        	a=a[:,::-1]
        	plan.PixelData=a.tostring()
        	plan.SOPInstanceUID=SOPInstanceUID_base+"."+str(plan.InstanceNumber)       	
        
        vv=plan.pixel_array*plan.RescaleSlope + plan.RescaleIntercept
        filepathout=pathout+"CT."+plan.SOPInstanceUID
        plan.save_as(filepathout)
        z_index=plan.InstanceNumber-1
        coronal_grid[z_index,1,:]=vv[256]
        coronal_grid[z_index,2,:]=vv[200]
        coronal_grid[z_index,3,:]=vv[300]

print("Number of head images processed: "+str(head_count))
print("Number of feet images processed: "+str(feet_count))

# Copy files to TBI folder
import shutil
#shutil.copy2(pathout,pathoutTBI)

from distutils.dir_util import copy_tree

copy_tree(pathout, pathoutTBI)
a=coronal_grid[:,1,:]
b=coronal_grid[:,2,:]
c=coronal_grid[:,3,:]

plt.figure()
#plt.imshow(b)
#plt.imshow(a,b,c)
imgplot = plt.imshow(c)
plt.show()
exit()