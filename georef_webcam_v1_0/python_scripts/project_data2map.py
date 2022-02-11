#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
#############################################################################################################
Created on Mon Jun 08 2020
Last edited on Fri Feb 11 2022

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
%   Name:       project_data2map.py
%   Purpose:    Project images and other data to map coordinates or image plane
%   Comment:    This file is executed from command line and projects any data 
%               in the size of the image to map coordinates or raster data from 
%               map coordinates to image plane. Also shp-files can be projected
%               in both directions.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#############################################################################################################
"""    


# import required libraries
import gdal, argparse, os, sys
from osgeo.gdalconst import GA_ReadOnly
import procedures.project2map as proj_map

# create parser with needed and optional input variables
parser = argparse.ArgumentParser(description='Project Webcam Image to CRS of DEM')
parser.add_argument(dest='coord_dir', type=str, help='directory to mask and coordinate raster layers')
parser.add_argument(dest='file_or_folder', type=str, help='single file or extension of image file (jpg, png, tif, ...)')
parser.add_argument(dest='out_dir', type=str, help='add directory, where projected images should be stored')
parser.add_argument("-ex","--extension", type=str, help='add directory, if several coregistered images should be projected', default = 'tif')
parser.add_argument('-px','--pixel_size', type=float, help='spatial resolution of projected map', default = 1)
parser.add_argument("-fill","--fill_nodata", type=int, default=0, help='add, if resulting gaps should be filled using close-range interpolation (gdal_fillnodata), value gives pixel range of gap filling')
parser.add_argument("-i","--to_image_view", help='add, if geotiff or shp should be projected from map coordinates into image plane', action="store_true")
parser.add_argument("-shp","--project_shp", help='add, if a shp-file should be projected', action="store_true")

# get arguments from parser
args = parser.parse_args()

# check, if files exist
if not os.path.isdir(args.coord_dir):
    print("Error: Directory to Coordinate Rasters and Mask does not exist")
    sys.exit()
if not os.path.isfile(args.file_or_folder):
    file_extension = args.extension
    image_folder = args.file_or_folder
    filename = None
    file = False
#    if args.image_folder == None:
#        args.image_folder = input("'filename_or_extension' is not a file. \nHence, a directory to data, which should be projected, is required. \nPlease enter directory, where images are stored:\n")
#    if not os.path.isdir(args.image_folder):
#        print("Error: Image Directory or Image File does not exist")
#        sys.exit()
else: 
    filename = args.file_or_folder
    file_extension = os.path.splitext(filename)[1][1:]
    image_folder = None
    file = True
        
# get crs information...
with open(os.path.join(args.coord_dir, 'dem_file.txt'), 'r') as output:
    DemDs = gdal.Open(output.readlines()[0], GA_ReadOnly)
    pj_DEM=DemDs.GetProjection()    
    
# run projection procedure
if args.project_shp:
    print ("Running shp-file projection...")
    if args.to_image_view:
        print ("Projecting shp to image plane...")
    proj_map.project_geometry(args.coord_dir, pj_DEM, args.file_or_folder, args.out_dir, file, args.to_image_view)     
elif args.to_image_view:
    print ("Projecting tif-file to image plane...")
    proj_map.project_to_image_plane(args.coord_dir, args.file_or_folder, args.out_dir, file)
else:
    print ("Projecting data to map...")
    if file_extension == 'tif':
        proj_map.project_tif(args.coord_dir, float(args.pixel_size), pj_DEM, args.file_or_folder, args.out_dir, args.fill_nodata, file)
    else:
        proj_map.project_image(args.coord_dir, float(args.pixel_size), pj_DEM, image_folder, file_extension, filename, args.out_dir, args.fill_nodata, data =True)
