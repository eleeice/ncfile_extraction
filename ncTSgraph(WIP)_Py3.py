# -*- coding: utf-8 -*-
"""
This script will take a NetCDF (.nc) TS file and extract the statistics
from it and produce a line plot, along with the steady state value.

Script created by: Ethan Lee (e.lee5@newcastle.ac.uk)

Creation date: 23/06/2021
Last edit date: 28/04/2022

Edits made (order of being made):
    - Script created to a stage of working (v0.1)
    - Commented script to give context and removed not needed modules (v1)
    - Trimmed script, made more automated (v1.2)
    
v1.2
"""
from time import time
start = time()

import os
from  pylab import *
import netCDF4 as nc, numpy
import pathlib
from matplotlib.offsetbox import AnchoredText
from matplotlib import pyplot as plt
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

Folder = 'C:/Users/b9036459/OneDrive - Newcastle University/PhD/Data/Modelling/output/plots'
os.chdir(Folder) # set working directory
variable = 'ice_volume' # define the variable you want to be plotted, must have same name as the variable in the .nc file
#variable = 'ice_area_glacierized'
plotTitle = 'Ice Volume'
#plotTitle = 'Ice Area'
yAxisTitle = 'Volume (km$^3$)' # if you want superscripting put them inbetween $ e.g. m$^2$
#yAxisTitle = 'Area (km$^2$)'
DeltaT = '-10'
xP = '1.00'
Res = '120m'

diagnostic = 'n' # this will stop the .nc file being closed, so you can test parts of the code

####################################################

## this will import the .nc file you want to use by opening file explorer
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.wm_attributes('-topmost',1)
root.withdraw()

inFile = filedialog.askopenfilename(parent = root,
                                    title = "Open NetCDF File",
                                    filetypes = (("NC file",
                                                  "*.nc*"),
                                                  ("all files",
                                                  ".")))
print('\nThe file selected is: '+os.path.basename(inFile)+'\n ')

## opens the .nc file to be read 
ncfile = nc.Dataset(inFile, 'r')
#print(ncfile.variables.keys())

## extracts the variable which was chosen by the user
var = ncfile.variables[variable][:]

####################################################
## the functions below aid the user to not have to manually change things
## however, some manual editions may be needed if not looking at
## area and volume. The yare easily added to the functions. Follow the
## same format as the previous elifs
####################################################
    
## function determines which divide number needed to convert m to km
def ifloop(userVariable):
    global e
    if 'area' in userVariable:
        e = 1e6
    elif 'volume' in userVariable:
        e = 1e9
    else:
        e = ''

## same as above but determines if it requires the conversion
## e.g. if not in volume or area, will not need conversion
def steadyResult(userVariable):
    global result2, var2
    varresult = ncfile.variables[variable][-1:]
    ifloop(userVariable)
    #e = ''
    if e == '':
        result2 = varresult
        result2 = float(result2)
        result2 = "{:.2f}".format(result2)
        result2 = str(result2)
        result2 = (int(''.join(filter(str.isdigit, result2)))/100)
        var2 = var
    else:
        result2 = varresult / e
        result2 = float(result2)
        result2 = "{:.2f}".format(result2)
        result2 = str(result2)
        result2 = (int(''.join(filter(str.isdigit, result2)))/100)
        var2 = var / e

## determines the units for the 'steady state'
def unit(userVariable):
    global units
    if 'glacierized' in variable:
        units = 'km$^2$'
    elif 'volume' in variable:
        units = 'km$^3$'
    else:
        units = ''

####################################################

## these run the functions
steadyResult(variable)
unit(variable)

## creates a tabel so the 'steady state' value can be added to the plot
handles = [mpl_patches.Rectangle((0, 0), 1, 1, fc="white", ec="white", lw=0, alpha=0)] * 2
labels = []
labels.append(str(DeltaT)+'°C, xP '+str(xP))
labels.append('Steady state is: '+str(result2)+' '+units)

## drawing the plot
fig = plt.figure(figsize=(10,5)) ## makes the plot bigger
plt.plot(var2, linewidth = 3, color = 'black') ## plots the line chart
plt.title(plotTitle, fontsize=14) ## added the title
plt.xlabel('Model Time (yrs)', fontsize=14) ## labels the x-axis; will always be the same
plt.ylabel(yAxisTitle, fontsize=14) ## labels the y-axis using the users define label
plt.legend(handles, labels, loc='lower right', fontsize='large', fancybox=True, framealpha=0, handlelength=0, handletextpad=0, borderpad=0, borderaxespad = 0.2) ## adds the steady state in a legend so it can be easily seen
plt.show() ## plots it all together

## saving the plot
#fname = variable+'_'+Res+'_'+DeltaT+'_'+xP+'.png'
#fig.savefig(fname)


if diagnostic == 'n':
    ncfile.close()
else:
    pass

os.chdir("..")

end = time.time()
print('Script ran in '+str(round((end - start),2))+' seconds')
