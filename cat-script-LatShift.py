import pydicom
import os
import numpy
import matplotlib.pyplot as plt
import glob
import string
import sys
import tornado 
from pathlib import Path

print("Welcome to the 2nd CT concatenation program programed at SCC\n")

SCCImagepath=os.path.abspath(r"//svstoroprd01/VA_Transfer/DICOM/standard/")
SCCTBIImagepath=os.path.abspath(r"\\svstoroprd01\VA_Transfer\DICOM\NonStandard")

debug = (input("\nAre You testing this code (Y/N)")).lower()

if ('y' in debug):
    if len(sys.argv) > 2:
        SCCImagepath=sys.argv[-2]
        SCCTBIImagepath = sys.argv[-1]
    else:
        SCCImagepath = input("Source location: ")
        SCCTBIImagepath = input("Save Location:")


print("Enter in the patient number that you would like to concatenatate, the last 8 folders are listed below.\n")

all_subdirs = [ f.path for f in os.scandir(SCCImagepath) if f.is_dir() ]

for subdir in all_subdirs:
	fullname=subdir
	dir, shortname = os.path.split(subdir)
	if ('delete' in shortname)==False:
		print(shortname)

while True:
    var = (input("\nPlease enter the patient's ID number: ")).strip()
    print ("You entered: "+ var) 
    if (input ("Is this correct (y/n)")).lower() == 'y' :
        break

OriginalPath=str(Path(os.path.join(SCCImagepath, var)).resolve())
print("Path of folder is " +OriginalPath)
pathout=OriginalPath+ "-Concantenated/"
pathoutTBI=os.path.join(SCCTBIImagepath, var+"-Concantenated/")

print("Output path 1 is " +pathout)
print("Output path 2 is " +pathoutTBI)




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

while True:
    xshift = input("Enter in the laterial shift needed (cm): ")
    xshift_value=int(float (xshift)*10)
    print ("You entered: "+ str(xshift_value) +" mm") 
    if (input ("Is this correct (y/n)")).lower() == 'y' :
        break

for root, dirs, filenames in os.walk(OriginalPath):
    for f in filenames:
        filepath=os.path.join(OriginalPath,f)
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
        filepath=os.path.join(OriginalPath,f)
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
        filepath=os.path.join(OriginalPath,f)
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
        filepathout=os.path.join(pathout,"CT."+plan.SOPInstanceUID)
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

print("TBI Images Saved")
var = input("Would you like to plot (old/new)")

if "old" in var.lower():
    a=coronal_grid[:,1,:]
    b=coronal_grid[:,2,:]
    c=coronal_grid[:,3,:]
    fig, axs = plt.subplots(3)
    fig.suptitle('Array')
    axs[0].imshow(b)
    axs[1].imshow(a)
    axs[2].imshow(c)
    #plt.figure()
    #plt.imshow(b)
    #plt.imshow(a,b,c)
    #imgplot = plt.imshow(c)
    plt.show()


elif "new" in var.lower():
    def make_mesh(image, threshold=-300, step_size=1):
        print "Transposing surface"
        p = image.transpose(2,1,0)
        
        print "Calculating surface"
        verts, faces, norm, val = measure.marching_cubes(p, threshold, step_size=step_size, allow_degenerate=True) 
        return verts, faces

    def plotly_3d(verts, faces):
        x,y,z = zip(*verts) 
        
        print "Drawing"
        
        # Make the colormap single color since the axes are positional not intensity. 
    #    colormap=['rgb(255,105,180)','rgb(255,255,51)','rgb(0,191,255)']
        colormap=['rgb(236, 236, 212)','rgb(236, 236, 212)']
        
        fig = FF.create_trisurf(x=x,
                            y=y, 
                            z=z, 
                            plot_edges=False,
                            colormap=colormap,
                            simplices=faces,
                            backgroundcolor='rgb(64, 64, 64)',
                            title="Interactive Visualization")
        iplot(fig)

    def plt_3d(verts, faces):
        print "Drawing"
        x,y,z = zip(*verts) 
        fig = plt.figure(figsize=(10, 10))
        ax = fig.add_subplot(111, projection='3d')

        # Fancy indexing: `verts[faces]` to generate a collection of triangles
        mesh = Poly3DCollection(verts[faces], linewidths=0.05, alpha=1)
        face_color = [1, 1, 0.9]
        mesh.set_facecolor(face_color)
        ax.add_collection3d(mesh)

        ax.set_xlim(0, max(x))
        ax.set_ylim(0, max(y))
        ax.set_zlim(0, max(z))
        ax.set_axis_bgcolor((0.7, 0.7, 0.7))
        plt.show()
    v, f = make_mesh(SCCTBIImagepath, 350)
    plt_3d(v, f)

sys.exit()



