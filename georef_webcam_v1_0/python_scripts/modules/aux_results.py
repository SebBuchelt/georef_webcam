#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
#############################################################################################################
Created on Mon May 11 2020
Last edited on Tue Jun 16 2020

Author: Sebastian Buchelt

/******************************************************************************
 *                                                                            *
 *   This program is public software; It is distributed under the the terms   *
 *   of the Creative Commons Attribution-NonCommercial-ShareAlike 4.0         *
 *   International Public License as published by the Creative Commons        *
 *   Corporation; either version 4 of the License, or (at your option) any    *
 *   later version.                                                           *
 *                                                                            *
 ******************************************************************************/
 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%   Name:       modules/aux_results.py
%   Purpose:    Auxiliary Functions to produce georef_webcam results
%   Comment:    This file contains auxiliary functions to read PRACTISE output
%               and produce the results provided by georef_webcam.
%
%   Overview:   select_PRACTISE_files: selects PRACTISE output file from given 
%                       directory and PRACTISE execution run
%               get_data_from_PRACTISE: reads data from octave mat-files
%               write_array_as_geotiff: exports an array as a geotiff (used to 
%                       generate coordinate and mask rasters)
%               interpolate_raster: interpolates coordinate arrays from
%                       projected DEM points
%               calculate_distance_raster: calculates distance of image pixel 
%                       to closest projected DEM pixel (needed for mask layer)
%               create_mask: generates mask to filter area above skyline
%               call_project_image: calls image projection procedure
%               read_png: aux function to read png data into array
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#############################################################################################################
"""

############### select octave file with specific file ending in given directory from a predefined run #######
# input:
#       - in_dir: directory or list of directories to search through
#       - run_name: only subdirectories containing this specific run_name will be screened
#       - file_ending: file extension to look for
def select_PRACTISE_files(in_dir, run_name, file_ending):
    # import required libraries and submodules of georef_webcam
    import os
    import modules.aux_functions as aux_func
    
    ###### create list of available subdirectories & select octave file with specified extension from directory list
    folders = [os.path.join(in_dir, 'PRACTISE',f) for f in os.listdir(os.path.join(in_dir, 'PRACTISE')) if ('output_'+run_name in f)]
    selected_file = aux_func.select_file(folders, file_ending, name = 'octave')
    # return selected octave file to main procedure
    return selected_file
#############################################################################################################



############### read PRACTISE output data from octave mat-file ##############################################
# input:
#       - PRACTISE_result: PRACTISE_result txt-file as list of strings (one string for each line in txt file)
#       - line: selected line to be read
#       - single_value: set True, if only a single value is stored in this line
#               otherwise function extracts a list of values separated by empty spaces
def get_data_from_PRACTISE(PRACTISE_result, line, single_value = False):
    # import required libraries
    import numpy as np
    
    ##### import single value or list of values and convert them to float
    if single_value:
        data = [PRACTISE_result[line]]
        
    else:
        data = PRACTISE_result[line].split(' ')[1:]
    data = [float(pt) for pt in data]
    # return extracted data as array to main procedure
    return np.array(data)
#############################################################################################################



############### write raster as tif-file (e.g. coordinate rasters, mask,...) ################################
# input:
#       - array: data array to be exported
#       - out_dir: out_dir to store data
#       - filename: name of tif-file to store data
def write_array_as_geotiff(array, out_dir, filename):
    # import required libraries
    import gdal, os

    ##### create tif-file 
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    (rows, cols)=array.shape
    outDs = driver.Create(os.path.join(out_dir,filename), cols, rows, 1, gdal.GDT_Float32)
    
    ##### write data into tif-file
    outBand = outDs.GetRasterBand(1)
    outBand.WriteArray(array)
    outBand.FlushCache()
    outBand = None
    outDs = None
#############################################################################################################
   
    
    
############### interpolate raster from projected DEM point information #####################################
# input:
#       - data: data to be interpolated
#       - points: location of the point in the grid
#       - interpolation_grid: grid to which the data is interpolated
#       - out_dir: out_dir to store data
#       - filename: name of tif-file to store data
#       - interpolation_type: way to interpolate data: 'nearest': Nearest Neighbour; 'linear': Bilinear
def interpolate_raster(data, points, interpolation_grid, out_dir, filename, interpolation_type = 'nearest'):
    # import required libraries
    from scipy.interpolate import griddata
    ##### interpolate raster and save interpolated array in tif-file
    raster = griddata(points, data, (interpolation_grid[0], interpolation_grid[1]), method=interpolation_type)
    write_array_as_geotiff(raster, out_dir, filename)
    # return array with interpolated data to main procedure
    return raster
#############################################################################################################
    


############### calculates distance of image pixel to closest projected DEM pixel (needed for mask layer) ###
# input:
#       - points: location of the point in the grid
#       - interpolation_grid: grid for which the distance to the closest point is calculated
#       - out_dir: out_dir to store data
def calculate_distance_raster(points, interpolation_grid, out_dir):
    # import required libraries
    import numpy as np
    from scipy.spatial.distance import cdist
    
    ##### calculate distance of pixel to next projected point, needed to detect skyline
    #(very time consuming, maybe easier approach possible)
    print('Calculate distance to projected points. Very time consuming... ')
    # reference points to calculate point distance (dont use all of them to save time)
    rows, cols = interpolation_grid[0].shape
    ref_pts = list()
    for row in range(0,rows, 4):
        for col in range(0,cols, 4):
            ref_pts.append((row, col)) 
            
    points_selected =list()
    subset = max(len(points)/100000,1)
    for x in range(0, len(points), subset):
        points_selected.append(points[x])
    
    ##### calculate minimum distance to next projected point and append to one list
    dist_info = list()
    for i in range((int(len(ref_pts)/5000+1))):
        dist_info.append(cdist(ref_pts[i*5000:min(i*5000+5000,len(ref_pts))],points_selected, 'euclidean').min(axis=1))
    dist_pts_final = dist_info[0]
    for array in dist_info[1:int((len(ref_pts)/5000+1))]:
        dist_pts_final = np.append(np.array(dist_pts_final),np.array(array))
       
    ##### interpolate result to raster of image size and save it as tif-file    
    dist_pts = interpolate_raster(np.array(dist_pts_final), np.array(ref_pts), interpolation_grid, out_dir, "aux_DEMptDist.tif", interpolation_type='nearest')
    # return array with distance information to main procedure
    return dist_pts
#############################################################################################################



############### create mask layer to filter areas above skyline #############################################
# input:
#       - dist_pts_raster: array with information about distance to next projected DEM point
#       - interpolation_grid: grid for which the distance to the closest point is calculated
#       - out_dir: output directory to store data
def create_mask(dist_pts_raster, out_dir):
    # import required libraries
    import numpy as np
    
    ##### generate mask from distance raster 
    # (if distance to next DEM point less than 10 image pixels, all areas below are not sky)
    print('Generate mask...')
    mask = np.array(dist_pts_raster)
    rows, cols = dist_pts_raster.shape
    for col in range(0,cols):
        row_lim = False
        for row in range(0,rows):
            if(row_lim):
                mask[row,col]=1
            elif(dist_pts_raster[row, col]>9):
                mask[row,col]=0
            else:
                mask[row,col]=1
                row_lim = True
    
    ##### export result to tif file
    write_array_as_geotiff(mask, out_dir, "mask.tif")
#############################################################################################################



############### call procedure to project image to map coordinates ##########################################
# input:
#       - dictionary: dictionary to be used to get dem and image data
#       - out_dir: output directory to store projected map
def call_project_image(dictionary, out_dir):
    # import required libraries and submodules of georef_webcam
    import gdal
    from osgeo.gdalconst import GA_ReadOnly
    import procedures.project2map as proj_map
    
    ##### get CRS from DEM file
    print('Project image to map coordinates...')
    DemDs = gdal.Open(dictionary['dem_file'], GA_ReadOnly)
    pj_DEM=DemDs.GetProjection()    

    ##### define resolution and start projection
    resolution = float(input('Which spatial resolution should the projected image have? \n'))
    proj_map.project_image(out_dir, resolution, pj_DEM, image_file = dictionary['image_file'])
#############################################################################################################



############### read RGB data from png-file into array ######################################################
# input:
#       - filename: name of png-file
def read_png(filename):
    # import required
    import os, subprocess, time, platform
    import numpy as np
    
    ##### create and call external py-function to read png data into numpy array and 
    #       store data in temporary np-file
    exe_file = os.path.splitext(filename)[0]+'_exe.py'
    numpy_file = os.path.splitext(filename)[0]+'.npy'
    with open(exe_file, 'w') as f:
        f.write('import os\n')
        f.write('from PIL import Image\n')
        f.write('import numpy as np\n')
        f.write('np.save("'+numpy_file+'", np.array(Image.open("'+filename+'")))')
    if(platform.system()=='Windows'):
        os.chdir(os.path.dirname(filename))
        subprocess.Popen("python "+exe_file, shell = True,stdout=subprocess.PIPE)
    else:
        subprocess.Popen(["python",exe_file],stdout=subprocess.PIPE)
    time.sleep(5)
    
    ##### read data from temporary numpy file and then remove temporary files
    data = np.load(numpy_file)
    os.remove(exe_file)
    os.remove(numpy_file)
    
    # return array with png data to main procedure
    return data
#############################################################################################################