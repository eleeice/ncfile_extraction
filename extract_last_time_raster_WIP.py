# -*- coding: utf-8 -*-

'''
This script will take a NetCDF (.nc) extras file and extract a singular
slice from the variable you want to look at. 

Script created by: Ethan Lee (e.lee5@newcastle.ac.uk)

Creation date: 23/06/2021
Last edit date: 07/11/2022

Edits made (order of being made):
    - Script created to a stage of working (v0.1)
    - Commented script to give context and removed not needed modules (v1)
    - Trimmed script, made more automation (v1.2)
    
v1.2

'''
## imported libraries, may need to install if not already
import os
import numpy as np
from osgeo import gdal, osr
import matplotlib.pyplot as plt
import netCDF4 as nc, numpy

##############################################################################

## list of variables from PISM
# 'time', 'time_bounds', 'mapping', 'pism_config', 'run_stats', 'timestamp', 
# 'x', 'y', 'bmelt', 'climatic_mass_balance', 'effective_air_temp', 
# 'effective_precipitation', 'ice_mass', 'ice_surface_temp', 'mask', 
# 'surface_accumulation_flux', 'surface_accumulation_rate', 
# 'surface_melt_flux', 'surface_melt_rate', 'surface_runoff_flux', 
# 'surface_runoff_rate', 'tempicethk', 'temppabase', 'tendency_of_ice_amount', 
# 'tendency_of_ice_amount_due_to_basal_mass_flux', 
# 'tendency_of_ice_amount_due_to_conservation_error', 
# 'tendency_of_ice_amount_due_to_discharge', 
# 'tendency_of_ice_amount_due_to_flow', 
# 'tendency_of_ice_amount_due_to_surface_mass_flux', 'thk', 'tillwat', 'topg', 
# 'usurf', 'ubar', 'vbar', 'velbase_mag', 'velsurf_mag'

## user inputs
variable = 'thk' # the variable you want to use, uncommand lines 64-65 to view variables
endSlice = 38 # the 'slice' or date you want. Number dependant on your NetCDF
rasterName = variable+'_10_5_100_600.tif' # name of the raster, needs .tif at the end

##############################################################################

## Opens up a file browser that allows you to easily find the file you want
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.wm_attributes('-topmost',1)
root.withdraw()

inFile = filedialog.askopenfilename(parent = root,
                                    title = "Open the NetCDF File",
                                    filetypes = (("NC file",
                                                  "*.nc*"),
                                                  ("all files",
                                                  ".")))
## makes the file location the working directory
os.chdir(os.path.dirname(inFile))

## this allows you to view that variables in the NetCDF
## uncomment, run the above lines, then run the lines below
#ncfile = nc.Dataset(inFile, 'r')
#print(ncfile.variables.keys())

###### all below extracts metadata we need to make the raster
## opens up the NetCDF with gdal and stores the GeoMetaData
ds_gdal = gdal.Open("NETCDF:{0}:{1}".format(inFile, variable))
gt = ds_gdal.GetGeoTransform()

## extracts the x and y cell number from the NetCDF
x = ds_gdal.RasterXSize
y = ds_gdal.RasterYSize

## extracts the corner coordinates
ulx, uly = gdal.ApplyGeoTransform(gt, 0, 0)
lrx, lry = gdal.ApplyGeoTransform(gt, x, y)

## extracts the cellsizes, the last one comes out negative so
## has to be made into a positive
cellsizex, cellsizey = gt[1], (gt[5]*-1)

## gives the x and y mins (0) and maxes (from above) for the raster
xcellmin=0
xcellmax=x
ycellmin=0
ycellmax=y

## plots the variabl into a numpy array
plotarray = np.array(ds_gdal.GetRasterBand(endSlice).ReadAsArray())

## removes all ice less than 0.1 m thick
plotarray2 = plotarray[plotarray < 0.1] = 0

## provide visual representation in the plot console area
plt.imshow(plotarray)

## translates the numpy array into a raster (.tif)
def array2raster(newRasterfn,rasterOrigin,pixelWidth,pixelHeight,array):
    cols = array.shape[1]
    rows = array.shape[0]
    originX = rasterOrigin[0]
    originY = rasterOrigin[1]
    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(newRasterfn, cols, rows, 1, gdal.GDT_Float32)
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(array)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromEPSG(32717) ## this is where you put your spatial reference - find out the EPSG number for your study site
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()


def main(newRasterfn,rasterOrigin,pixelWidth,pixelHeight,array):
    reversed_arr = array[::-1] ## reverse array so the tif looks like the array
    array2raster(newRasterfn,rasterOrigin,pixelWidth,pixelHeight,reversed_arr) ## convert array to raster


if __name__ == "__main__":
    rasterOrigin = (ulx,lry)
    pixelWidth, pixelHeight = cellsizex, cellsizey
    newRasterfn = rasterName
    array = plotarray

    main(newRasterfn,rasterOrigin,pixelWidth,pixelHeight,array)

print('\nYour NetCDF slice has been extracted')
print('\nIgnore the warning above, I do not know how to remove them')