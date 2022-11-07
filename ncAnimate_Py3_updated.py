# -*- coding: utf-8 -*-

'''
This script will take the output of the PISM model
(choose the 'extras_' file) and will take the
ice thickness variable and create a gif out of the
images it creates from the time slices.

Script created by: Dr Stewart Jamieson (stewart.jamieson@durham.ac.uk)
Script edited by: Ethan Lee (e.lee5@newcastle.ac.uk)

Edit date: 18/06/2021

Edits made (in line order, not order of being made):
    -   Updated from Python 2 to Python 3
    -   Removed Deprecation Warnings to clean up the console (however
        these 'clipping input' errors I do not know how to fix/remove)
    -   Added user specific options so they do not need to be found 
        within the script
    -   Opens file explorer to allow user to find their nc file easily
    -   Script automatically pulls out the x, y dimentions and number 
        of 'slices' from the .nc file
    -   Script automatically obtains the min/max cell value from the last
        slice of the variable chosen and rounds up to nearest interval
        -   Also automatically generates ticks by creating a list and 
            appends the max value to the end (some manual edits needed)
    -   Creates a new folder with the name dependant on user option 
        (new_dir_name) so images and gifs are stored neatly in wd
        -   Added function where is folder name already exists it will 
            not over wirte dependant on user option (editingSame)
    -   Fixed the xcell and ycell order (was incorrect e.g. x = y and 
        y = x, now x = x and y = y)
    -   Automatically generates variables 
    -   Added model year to the plot
        -   Added the model temperature delta and fraction precip to the plot
        -   Added ability to make gif of images, without using external program
    -   Added extract information to print to the console on status of scrip
    -   Added a little diagnostic funcionality so the .nc file is not closed 
        so you can check parts of the code work
        
Still to be implamented:
    -   Make script work again with linux command line
    -   Automate titles?
    -   Automate the variable creation?
'''
from time import time
start = time()


import os
from  pylab import *
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import scipy.signal as signal
import getopt,sys
import netCDF4
import netCDF4 as nc, numpy
from netCDF4 import Dataset
import time
import pathlib
import imageio
import matplotlib.patches as mpl_patches

## these remove the Deprecation Warnings for a cleaner console
## comment out if want to see the Deprecation Warnings
from warnings import simplefilter 
simplefilter(action='ignore', category=DeprecationWarning)


####################################################
## below are all the options you need to set yourself 
## for the code to run, comments will be at the end 
## of each line so you understand what the line of
## of code does. Some options in the code may need to
## be edited manually, if the output is incorrect
####################################################

Folder = 'C:/Users/b9036459/OneDrive - Newcastle University/PhD/Data/Modelling/output/plots' # directory of where you want your images and gif saved
variable = 'thk' # define the variable you want to be plotted, must have same name as the variable in the .nc file
interval = 26 # this is the interval for the colorbar (i.e. will show elevations at every XX m)
createGif = 'y' # if you want a gid to be created at the end put 'y', if not put 'n'
new_dir_name = 'thk_300m_10_120' # a new folder will be created in your chosen working directory, this will be the folder name
outFile ='thk_300m_10_120_images' # the name you want to be at the start of the image output, without the file extention
outFileGif = 'thk_300m_10_120_gif' # the name you want the output of the generated gif to be, without the file extention
timeStep = 100 # this is the timestepping you used for extracting the extras (write model output every 100 years etc.)
userEndSlice = -1 # if you want all slices set as -1 and it will autmoatically determine the slice limit, if want to manually asign, insert a number > 0
startSlice= 0 # this will always be the same, unless you want to start at a different point in the slices
skipSlice= 1 # the skips between slices e.g. generate image for every 5 slices (5, 10, 15, 20)
overText = 'e.lee5@newcastle.ac.uk' # this will be what gets added to your images (if you want to be contacted)
DeltaT = '-10' # this is the temprature modifier used for the model run you are plotting
xP = '1.25' # this is the precipitation fraction modifier used for the mopdel run you are plotting

## diagnostic vairbales
diagnostic = 'n' # this will stop the nc file being closed, so you can test parts of the code
editingSame = 'y' # if you are editing the same nc file choose 'y' if not choose 'n' - this is so the folder can be overwritten
cleanFiles = False # if set to False = images created will not be deleted. If set to True = images will be deleted after gif creation

####################################################

# def usage():
#     "print short help message"
#     print('Usage: ncAnimate.py [options] infile outfile')
#     print('')
#     print('Animates a variable from a netcdf file')
#     print('')
#     print('infile = input text file e.g. model.nc')
#     print('outfile = output text file e.g. model.mpg')
#     print('-h = this message')
#     print('-v, --variable = plotting variable')
#     print('-s, --start = Start plotting at this slice')
#     print('-e, --end = End plotting at this slice')
#     print('-c, --clean = clean up temporary image files')
#     print('--text = Add this string as text over the plot')
#     print('--skip = Plot variable at every nth slice')

## get options
# try:
#     opts, args = getopt.getopt(sys.argv[1:],'hv:s:e:c',['help','variable=','start=','end=','clean','text=','skip='])
# except getopt.GetoptError:
#         # print usage and exit
#         printError('error')
#         usage()
#         sys.exit(1)

####################################################
## below is three ways in which the file is chosen
## can either be by opening a file explorer window which is default
## by manually assigning the inFile or by using the linux
## command line options
####################################################
 
## when the script is ran it will open a file explorer to select the file
## it will also look for the ts file within the same direcotry as the extras
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.wm_attributes('-topmost',1)
root.withdraw()

inFile = filedialog.askopenfilename(parent = root,
                                    title = "Open the extras NetCDF File",
                                    filetypes = (("NC file",
                                                  "*.nc*"),
                                                  ("all files",
                                                  ".")))

os.chdir(os.path.dirname(inFile))
prefixed = [filename for filename in os.listdir('.') if filename.startswith("ts")]
tsFile = ''.join(prefixed)

## if there is no ts file automatically found within the folder 
## it will then ask for you to automatically choose one
if tsFile == '':
    tsFile = filedialog.askopenfilename(parent = root,
                                        title = "Open the time series NetCDF File",
                                        filetypes = (("NC file",
                                                      "*.nc*"),
                                                     ("all files",
                                                      ".")))

print('This is the extras file selected: '+os.path.basename(inFile)+'\n ')

print('This is the time series file selected: '+os.path.basename(tsFile)+'\n ')



## if that does not work above, manually define the file location in 'inFile'
#inFile = 'C:/Users/b9036459/OneDrive - Newcastle University/PhD/Data/Modelling/parametres/t10_150/150/extra_LH_Spin_10_150_600m.nc'

## if you want to use the script in a linux command line uncommend out these lines
## THIS NEEDS TO BE RECONFIGURED TO WORK
#if len(args) < 3:
#        inFile = args[0]
#        outFile = args[1]
#else:
#        usage()
#        sys.exit(1)

####################################################

# for o,a in opts:
#     if o in ('-h', '--help'):
#         usage()        
#         sys.exit(0)
#     if o in ('-v','--variable'):
#      	variable = a
#     if o in ('-s','--start'):
#      	startSlice = int(a)
#     if o in ('-e','--end'):
#      	endSlice = int(a)
#     if o in ('--skip'):
#      	skipSlice = int(a)
#     if o in ('-c','--clean'):
#      	cleanFiles=True
#     if o in ('--text'):
#      	overText = a

## this generates the hillshade 
def hillshade(data,scale=10.0,azdeg=165.0,altdeg=45.0):
  ''' convert data to hillshade based on matplotlib.colors.LightSource class.
    input:
         data - a 2-d array of data
         scale - scaling value of the data. higher number = lower gradient
         azdeg - where the light comes from: 0 south ; 90 east ; 180 north ;
                      270 west
         altdeg - where the light comes from: 0 horison ; 90 zenith
    output: a 2-d array of normalized hilshade'''
  ## convert alt, az to radians
  az = azdeg*pi/180.0
  alt = altdeg*pi/180.0
  ## gradient in x and y directions
  dx, dy = gradient(data/float(scale))
  slope = 0.5*pi - arctan(hypot(dx, dy))
  aspect = arctan2(dx, dy)
  intensity = sin(alt)*sin(slope) + cos(alt)*cos(slope)*cos(-az - aspect - 0.5*pi)
  intensity = (intensity - intensity.min())/(intensity.max() - intensity.min())
  return intensity

## generates the shade which is used to fully create the hillshade  
def set_shade(a,intensity=None,cmap=cm.gray,scale=10.0,azdeg=165.0,altdeg=45.0):
  if intensity is None:
    ## hilshading the data
    intensity = hillshade(a,scale=10.0,azdeg=165.0,altdeg=45.0)
  else:
    ## or normalize the intensity
    intensity = (intensity - intensity.min())/(intensity.max() - intensity.min())
   ## get rgb of normalized data based on cmap
  rgb = cmap((a-a.min())/float(a.max()-a.min()))[:,:,:3]
  ## form an rgb eqvivalent of intensity
  d = intensity.repeat(3).reshape(rgb.shape)
  ## simulate illumination based on pegtop algorithm.
  rgb = 2*d*rgb+(rgb**2)*(1-2*d)
  return rgb

## this takes the nc file and opens it for the data to be read from it
ncfile = nc.Dataset(inFile, 'r')
tsfile = nc.Dataset(tsFile, 'r')

## this will extract the x and y dimentions of the nc file
## this is used for the plot dimentions
#print(ncfile.dimensions) # uncommend is you want to see the dimensions of the .nc file
dimension = str(ncfile.dimensions)
theDimension = dimension.split()
x1 = theDimension[27]
y1 = theDimension[36]
y = int(''.join(filter(str.isdigit, y1)))
x = int(''.join(filter(str.isdigit, x1)))

## similar to above, unless there is a user generated end slice number
## this will automatically extract the number of slices from the nc file
if userEndSlice >= 0:
    endSlice = userEndSlice
else:
    autoSlice1 = theDimension[9]
    autoSlice = int(''.join(filter(str.isdigit, autoSlice1)))
    endSlice = autoSlice
    print('There are '+str(autoSlice)+' slices\n')

#print(ncfile.variables) 

#ion()
#fig_hndl = figure()

## make an empty list into which we'll append the filenames of the PNGs 
## that compose each frame.
files=[]

## this is for the sea mask. If you location has coastlines, you may want
## uncomment the seamask further down in the script
#sl=numpy.ones([329,329])

## this is the dimentions of the .nc file which will also be used for the plot 
xcellmin=0
xcellmax=x
ycellmin=0
ycellmax=y

## this are the different variables which can be used 
## if your vairable is not found in this list, you can add it
## yourself using the same format as the ones below
####################################################

## these functions to round up and down the max and min value 
def roundup(num, to):
    return num if num % to == 0 else num + to - num % to 

def rounddown(num, to):
    return num // to*to

## this allows varibales to be chosen to matter what is chosen
## without having to manually create if's
##### WIP - Works, just sometimes nees manual edit for titletext ####
def Variable(userInterval, userVariable):
    global vmn, vmx, colour, titletext, barTicks, barTickLabels
    interval = userInterval
    var = ncfile.variables[userVariable][(endSlice-1):]
    vmn = rounddown(var.data.min(), interval)
    #vmn = 0 # uncommand if you want the minimum to be 0
    vmx = roundup(var.data.max(), interval)
    ticks = np.arange(int(vmn), int(vmx), interval).tolist()
    ticks.append(int(vmx))
    colour = matplotlib.cm.Blues_r
    titleStart = ncfile.variables[userVariable]
    units = str(titleStart)
    units = units.split('units: ')
    units = units[1]
    units = units.split('\n')
    units = units[0]
    title = str(titleStart)
    title = title.split('standard_name: ')
    if len(title) == 1:
        title = str(titleStart)
        title = title.split('long_name: ')
        title = title[1]
        title = title.split('\n')
        title = title[0]
    else:
        title = title[1]
        title = title.split('\n')
        title = title[0]
        title = title.replace('_', ' ')
        title = title.title()
    titletext = title+' ('+units+')'
    #titletext = 'Ice Velocity (m year-1)' ## if the title is not what you want, uncomment this as put what you want
    barTicks = np.array(ticks)
    barTickLabels = ticks

Variable(interval, variable)

def steadyState():
    global vol, area
    vol = tsfile.variables['ice_volume'][-1:]
    area = tsfile.variables['ice_area_glacierized'][-1:]
    vol = float(vol)
    vol = "{:.2f}".format(vol)
    vol = str(vol)
    vol = (int(''.join(filter(str.isdigit, vol)))/100)
    vol = vol / 1e9
    vol = "{:.2f}".format(vol)
    area = float(area)
    area = "{:.2f}".format(area)
    area = str(area)
    area = (int(''.join(filter(str.isdigit, area)))/100)
    area = area / 1e6
    area = "{:.2f}".format(area)
    
steadyState()

####################################################
## Keeping these incase anything goes wrong with the above function.
## If you need to use the below 'if's comment out the function above
## and uncommend the 'if' you want to use below
####################################################

# if (variable == 'usurf'):
#     interval = 500 # this is the interval spacing you would want for the color bar
#     var = ncfile.variables['usurf'][(endSlice-1):]
#     max_u = var.data.max()
#     min_u = var.data.min()
#     min = 0 # this will need to be manually assigned if color bars minimum messing it up
#     max = roundup(max_u, interval)
#     vmn=min
#     vmx=max
#     ticks = np.arange(int(min), int(max), interval).tolist()
#     ticks.append(int(max))
#     colour=matplotlib.cm.Blues_r
#     titletext='Ice Surface (m)'
#     barTicks=np.array(ticks)
#     barTickLabels=ticks
# if (variable == 'erate'):
#     vmn=0
#     vmx=0.0008
#     colour=matplotlib.cm.jet
#     titletext='Erosion Potential'
#     barTicks=np.array([0,0.0008])
#     barTickLabels=['0','Maximum']
# if (variable == 'btemp'):
#     vmn=-5
#     vmx=0
#     colour=matplotlib.cm.hot
#     titletext='Basal Ice Temperature (deg. C)'
#     barTicks=np.array([0,-1,-2,-3,-4,-5])
#     barTickLabels=['0','-1','-2','-3','-4','< -5']
# if (variable == 'thk'):
#     interval = 50
#     var = ncfile.variables['thk'][(endSlice-1):]
#     vmn=rounddown(var.data.min(), interval)
#     vmx=roundup(var.data.max(), interval)
#     ticks = np.arange(int(vmn), int(vmx), interval).tolist()
#     ticks.append(int(vmx))
#     colour=matplotlib.cm.Blues_r
#     titletext='Ice Thickness (m)'
#     barTicks=np.array(ticks)
#     barTickLabels=ticks
# if (variable == 'velbase_mag'):
#     interval = 100
#     var = ncfile.variables['velbase_mag'][(endSlice-1):]
#     min = rounddowmn(var.data.min(), interval)
#     max = roundup(var.data.max(), interval)
#     vmn=0
#     vmx=max # need to change the max dependant on the modelled glacial ice thickness
#     ticks = np.arange(0, int(max), interval).tolist()
#     ticks.append(int(max))
#     colour=matplotlib.cm.Blues_r
#     titletext='Ice Velocity (m year-1)'
#     barTicks=np.array(ticks)
#     barTickLabels=ticks
    
####################################################

os.chdir(Folder)

## this creates a new folder in your chosen working directory chosen at
## the start of the script (Folder) and then sets it as the new working 
## directory this will be where the images and gif will be saved
## this is set up as a def and if loop as, if the folder already exists
## you may not want to overwrite what you have created as you could have
## forgot to change the new_dir_name
## if you want to spe
def createfolder(dirname, destpath):
            full_path = os.path.join(dirname, destpath)
            if os.path.exists(full_path):
                    print('\nFolder already exists, please delete folder, or rename your new_dir_name at top of the script')
                    sys.exit()
            else:
                new_dir = pathlib.Path(Folder, new_dir_name)
                new_dir.mkdir(parents=True, exist_ok=True)

## if you have selected that you are editing the same .nc file and variable
## this will check so, if you are not it will say the folder already exisits
## if it does indeed exist
if editingSame == 'n':
    createfolder(Folder, new_dir_name)
else:
    new_dir = pathlib.Path(Folder, new_dir_name)
    new_dir.mkdir(parents=True, exist_ok=True)
    
os.chdir(new_dir_name)

handles = [mpl_patches.Rectangle((0, 0), 0, 0)] * 3

labels = []
labels.append(str(DeltaT)+'°C, xP '+str(xP))
labels.append('Area = '+area+' km$^2$')
labels.append('Volume = '+vol+' km$^3$')

for t in range(startSlice,endSlice,skipSlice):
    ## get the data for this timeslice for the main variable, will need to add
    ## if you are using varibales different to these
    plotarray = numpy.array(ncfile.variables[variable][t,ycellmin:ycellmax,xcellmin:xcellmax])
    usurfarray = numpy.array(ncfile.variables['usurf'][t,ycellmin:ycellmax,xcellmin:xcellmax])
    thkarray = numpy.array(ncfile.variables['thk'][t,ycellmin:ycellmax,xcellmin:xcellmax])
    topoarray= numpy.array(ncfile.variables['topg'][0,ycellmin:ycellmax,xcellmin:xcellmax])
    
    ## removes any value below 0.1
        # change if you want to remove another values
    plotarray[plotarray < 0.1] = np.nan # if you need to remove 0 values
    
    ## Mask main array variable, upper surface variable  and sea level variable
    masked_array = numpy.ma.array(plotarray, mask=(thkarray <= 0))
    mask_usurf = numpy.ma.array (numpy.array(ncfile.variables['usurf'][t,ycellmin:ycellmax,xcellmin:xcellmax]), mask=(thkarray <= 0))
    #sea_mask=numpy.ma.array (numpy.array(sl[xcellmin:xcellmax,ycellmin:ycellmax]), mask=(topoarray > 0))
    
    ## Hillshade things
    rgb = set_shade(topoarray,cmap=cm.gray)
    rgb1 = set_shade(mask_usurf,cmap=cm.gray)

    ## Start plotting things
    fig = plt.figure(figsize=(8,8))
    ion()
    ax = fig.add_subplot(111)
    
    ## switch off x,y ticks on image
    ax.yaxis.set_ticks([])
    ax.xaxis.set_ticks([])
    
    ## draw the frame
    suptitle(titletext, fontsize=25, y=0.94, x=0.52)
    cmap = matplotlib.cm.gray
        
    ## plot hillshaded bed topography
    cax=ax.imshow(rgb, norm=matplotlib.colors.Normalize(vmin=0, vmax=0.008, clip = False),alpha=.7,origin='lower')
    
    ## plot sea mask 
    #cmap=matplotlib.cm.jet_r
    #cax=ax.imshow(sea_mask,vmin=0,vmax=1,alpha=.4,origin='lower',cmap=cmap)
    
    ## plot the main variable
    cmap = colour
    cax=ax.imshow(masked_array, vmin=vmn, vmax=vmx, alpha=1, origin='lower', cmap=cmap)
    if (variable=='erate'):
        ctr=contour(masked_array, [0], hold='on', colors = 'w', linestyles=['dotted'],linewidth=[0.5])
        if (variable=='thk'):
            ctr=ax.contour(masked_array, [100 ,150 ,200 ,250 ,300 ,350], colors = 'k', linestyles='solid', alpha=0)
      
    ## plot the colour bar
    cb=fig.colorbar(cax, spacing='proportional', fraction=0.1, aspect=10, orientation='vertical', shrink=0.8, ticks=barTicks)
    cb.ax.set_yticklabels(barTickLabels)
    cb.ax.tick_params(labelsize=12) 
    
    ## add text into the plot
    Time = t*timeStep + 100
    timeT = []
    timeT.append(str(Time)+' years')
    ax.text(0, -5, overText,fontsize=10)
    #ax.text(0, 0, str(Time)+' years', fontsize = 16)
    legend1 = ax.legend(handles, labels, loc='upper left', edgecolor="black",frameon=True, fancybox=False, fontsize=14, framealpha=0.5, handlelength=0, handletextpad=0, borderpad=0.2, borderaxespad = 0, labelspacing=0)
    legend2 = ax.legend(handles, timeT, loc='lower left', edgecolor="black",frameon=True, fancybox=False, fontsize=16, framealpha=0.4, handlelength=0, handletextpad=0, borderpad=0.2, borderaxespad = 0, labelspacing=0)
    ax.add_artist(legend1)
    ax.add_artist(legend2)
    #ax.text(52,1, str(DeltaT)+'°C, xP '+str(xP), fontsize = 20)
    
    ## draws the plot
    draw()
    
    #Plot the hillshade of the ice surface
    #Note: knackers up colouring of variable plot and also the clarity of the sea and topography
    ##cmap = matplotlib.cm.gray
    ##ax.imshow(rgb1, alpha=.8,origin='lower') 

    ## form a filename
    fname = outFile+'_%03d.png'%(t+1)
    
    ## save the frame with the file name
    savefig(fname)
    
    ## append the filename to the list
    files.append(fname)
    fig.clf()
    
    ## closes the created figure
    #time.sleep(2)
    close(fig)
    print('Time: ',t+1)

## this section will take the images made above and turn them into a gif animation 

plt.imshow(thkarray)

def gifCreation():
    png_dir = os.getcwd() # this should be where the images are saved
    images = []
    for file_name in sorted(os.listdir(png_dir)):
        if file_name.endswith('.png'):
            file_path = os.path.join(png_dir, file_name)
            images.append(imageio.imread(file_path))
    imageio.mimsave(outFileGif+'.gif', images, fps=3) # Gif will be saved in working directory

if createGif == 'y':
    gifCreation()
    print ('\nGif created')
else:
    pass

if (cleanFiles == True):
    for fname in files: os.remove(fname)
else:
    pass

if (cleanFiles == True):
    print('\nImages deleted')
else:
    print('\nImages kept')

print('\nScript Complete in ')

if diagnostic == 'n':
    ncfile.close()
else:
    pass

## this moves the working directory up one level incase you want to delete the file created without exiting the script
os.chdir("..")

end = time.time()
print(str(round((end - start),2))+' seconds')
