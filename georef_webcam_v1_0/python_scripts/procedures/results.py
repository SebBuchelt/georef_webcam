#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
#############################################################################################################
Created on Fri May 08 2020
Last edited on Mon Jun 15 2020

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
%   Name:       procedures/results.py
%   Purpose:    generate output from results provided by PRACTISE
%   Comment:    This file contains the functions, which generate the output of 
%               the georef_webcam package. The data is extracted from the 
%               PRACTISE results and converted into more userfriendly style.
%
%   Overview:   show_result: shows octave file with DEM points projected into
%                       image plane
%               extract_params: extracts projection parameters after GCP 
%                       optimization and stores them in json-file
%               calc_results: calculates georef_webcam output from PRACTISE 
%                       results (coordinate rasters, mask, projected image)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#############################################################################################################
"""


###############################################################################
### function to plot octave file with DEM points projected into image plane ###
# input:
#       - out_dir: directory, where output of PRACTISE is stored in subfolder.
#       - run_name: name for projection run to recognize output file of PRACTISE.
###############################################################################
def show_result(out_dir, run_name):
    # import required libraries and submodules of georef_webcam
    import os, subprocess, time, platform
    import modules.aux_results as aux_res
    
    # select octave fig file, which should be plotted
    selected_file = aux_res.select_PRACTISE_files(out_dir, run_name, '_auto.ofig')
    
    ##### write file with octave commands to open that figure
    with open(os.path.join(out_dir,'run_image.m'), 'w') as octave_file:
        octave_file.write('graphics_toolkit ("fltk")\n')
        if(platform.system()=='Windows'):
            octave_file.write('hgload("'+'/'.join(str(selected_file).split('\\'))+'")\n') 
        else:
            octave_file.write('hgload("'+selected_file+'")\n') 
        octave_file.write('waitforbuttonpress()')
    
    ##### open figure with octave (execution depends on platform: Windows or Linux)
    if(platform.system()=='Windows'):
        os.chdir(out_dir)
        subprocess.Popen("octave --force-gui run_image.m", shell = True,stdout=subprocess.PIPE)
    else:
        subprocess.Popen(["octave",os.path.join(out_dir,'run_image.m')],stdout=subprocess.PIPE)
    time.sleep(5) # wait 5 s until execution continues
################################### end #######################################
###############################################################################
    
    
###############################################################################
###### function to extract optimized projection parameters after GCP run ######
# input:
#       - input_dict: dictionary, which should be adjusted with optimized parameters.
#       - run_name: name for projection run to recognize output file of PRACTISE.
#       - in_dir: directory, where generated dictionary is stored as json file.
###############################################################################
def extract_params(input_dict, run_name, in_dir=False):
    # import required libraries and submodules of georef_webcam
    import os, json
    import modules.aux_results as aux_res
    import modules.aux_functions as aux_func
    import procedures.collect_projection_parameters as collect_params
    
    # select octave file, which contains information about optimized projection parameters
    result_file = aux_res.select_PRACTISE_files(input_dict['path'], run_name, '_proj.mat')
    
    ##### Extract information from PRACTISE output
    print("Extract information from PRACTISE output...")
    with open(result_file, 'r') as output:
        result_output = output.readlines()
    # Extract parameters
    pos_E = aux_res.get_data_from_PRACTISE(result_output, 5)
    pos_N = aux_res.get_data_from_PRACTISE(result_output, 6)
    offset = aux_res.get_data_from_PRACTISE(result_output, 23)
    roll_ang = aux_res.get_data_from_PRACTISE(result_output, 28, single_value = True)[0]
    foc_len = aux_res.get_data_from_PRACTISE(result_output, 33, single_value = True)[0]*1000
    sen_width = aux_res.get_data_from_PRACTISE(result_output, 104, single_value = True)[0]*1000
    sen_height = aux_res.get_data_from_PRACTISE(result_output, 99, single_value = True)[0]*1000
    buf = aux_res.get_data_from_PRACTISE(result_output, 240, single_value = True)[0]
    cam_pos = (pos_E[0], pos_N[0])
    tar_pos = (pos_E[1], pos_N[1])
    
    ##### Create new dictionary 
    new_dict = collect_params.write_dict(input_dict['image_file'], input_dict['dem_file'], cam_pos, tar_pos, 
                          offset[0], offset[1], input_dict['path'], roll_angle = roll_ang, 
                          focal_length = foc_len, sensor_width = sen_width, sensor_height = sen_height, 
                          buffer = buf, cam_epsg = input_dict['var_add']['camera_epsg'])
    
    ##### keep old GCPs, if wanted
    if aux_func.check_input("Do you want to keep the Ground Control Points for further processing?"):
        new_dict['gcp_file'] = input_dict['gcp_file']
        new_dict['var_add']['opt_boundaries'] = input_dict['var_add']['opt_boundaries']
        
    ##### store result in json-file, if wanted
    if aux_func.check_input("Do you want to save extracted dictionary with optimzed parameters as new json-file?"):
        run_name = input('Old filename: '+ run_name + ' \nPlease enter a new filename: \n')
    	##### write resulting dict to json file
        if not in_dir:
            in_dir = input('Please enter a directory, where json-file should be stored: \n')
        print('\n\nCollected parameters are stored in json file:')
        print(os.path.join(in_dir,run_name+".json"))
        jsonfile = json.dumps(new_dict)
        f = open(os.path.join(in_dir,run_name+".json"),"w")
        f.write(jsonfile)
        f.close()
    
    # return the created dictionary and new name of run to main procedure
    return new_dict, run_name
################################### end #######################################
###############################################################################
    

###############################################################################
####### function to calculate georef_webcam output from PRACTISE results ######
# input:
#       - input_dict: dictionary used for the georeferencing procedure.
#       - run_name: name for projection run to recognize output file of PRACTISE.
###############################################################################
def calc_result(input_dict, run_name):
    # import required libraries and submodules of georef_webcam
    import os, shutil
    import numpy as np
    import modules.aux_functions as aux_func
    import modules.aux_results as aux_res

    # create directory for georef_webcam results
    output_dir = os.path.join(input_dict['path'], 'georef_result', run_name)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # select octave file, which contains PRACTISE georeferencing results
    result_file = aux_res.select_PRACTISE_files(input_dict['path'], run_name, '_proj.mat')
    
    ############### Extract information from PRACTISE output ##################
    print("Extract information from PRACTISE output...")
    # read mat-file
    with open(result_file, 'r') as output:
        result_output = output.readlines()
    # get number of columns and no of rows of image
    rows = int(result_output[109])
    cols = int(result_output[114])
    # get position in image of all projected DEM points
    img_col = aux_res.get_data_from_PRACTISE(result_output, 167)
    img_row = aux_res.get_data_from_PRACTISE(result_output, 168)
    points = [(int(img_row[pt]), int(img_col[pt])) for pt in range(len(img_col))]
    # create interpolation grid 
    interpolation_grid = np.mgrid[0:rows, 0:cols]
    
    ############### calculate results #########################################
    ##### decide, which results should be produced
    print("Which results should be produced?")
    selected_results = aux_func.select_choices(['rasters with easting and northing coordinate + mask', '+ altitude raster', 
                                                '+ distance to camera', '+ projected image', 'all results'], True)
    
    ##### interpolate coordinate rasters
    print('Start interpolation of coordinates rasters ...')
    # select interpolation style: nearest neighbor or bilinear
    print('How do you want to interpolate the coordinate rasters? Nearest neighbor or Bilinear?')
    interpolate = aux_func.select_choices(['nearest', 'linear'])[0]
    # interpolate coordinate (E & N) rasters
    east_raster = aux_res.interpolate_raster(aux_res.get_data_from_PRACTISE(result_output, 135), points, interpolation_grid, output_dir, "east_raster.tif", interpolation_type = interpolate)
    north_raster = aux_res.interpolate_raster(aux_res.get_data_from_PRACTISE(result_output, 136), points, interpolation_grid, output_dir, "north_raster.tif", interpolation_type = interpolate)
    # interpolate altitude raster (optional)
    if (set(['+ altitude raster', 'all results']).intersection(selected_results)):
        alt_raster = aux_res.interpolate_raster(aux_res.get_data_from_PRACTISE(result_output, 137), points, interpolation_grid, output_dir, "alt_raster.tif", interpolation_type = interpolate)
        del alt_raster
    
    ##### copy image to output directory and save directory to dem for prj information
    shutil.copy2(input_dict['image_file'], output_dir)
    with open(os.path.join(output_dir,'dem_file.txt'), 'w') as dem_file:
        dem_file.write(input_dict['dem_file'])
    
    ##### generate mask to filter areas above skyline
    # calculate distance to DEM points in image plane to get skyline
    dist_pts_raster = aux_res.calculate_distance_raster(points, interpolation_grid, output_dir)
    # create mask
    aux_res.create_mask(dist_pts_raster, output_dir)
    
    ##### calculate distance to camera (optional)
    #           edges in panoramic view can be derived from that
    if (set(['+ distance to camera', 'all results']).intersection(selected_results)):
        pos_E = aux_res.get_data_from_PRACTISE(result_output, 5)
        pos_N = aux_res.get_data_from_PRACTISE(result_output, 6)
        cam_pos = (pos_E[0], pos_N[0])
        dist_raster = np.sqrt((east_raster-cam_pos[0])**2+(north_raster-cam_pos[1])**2)
        aux_res.write_array_as_geotiff(dist_raster, output_dir, "dist_raster.tif")
    
    ##### project image to map
    if (set(['+ projected image', 'all results']).intersection(selected_results)):
        aux_res.call_project_image(input_dict, output_dir)

################################### end #######################################
###############################################################################