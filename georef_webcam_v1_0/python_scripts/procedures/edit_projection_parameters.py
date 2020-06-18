#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
#############################################################################################################
Created on Mon May 11 2020
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
%   Name:       procedures/edit_projection_parameters.py
%   Purpose:    Edit parameters in dictionary for image projection
%   Comment:    This file contains the function, which edits the parameters 
%               inside an existing dictionary; If one parameter is changed all 
%               depending parameters are changed accordingly.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#############################################################################################################
"""

###############################################################################
#################### function to edit projection parameters ###################
# input:
#       - input_dict: dictionary, which should be edited.
#       - in_dir: directory, where the resulting json-file will be stored in.
#       - name_of_run: define a name for projection run to recognize output.
###############################################################################
def edit_parameters(input_dict, in_dir, name_of_run):
    # import required libraries and submodules of georef_webcam
    import json, os
    import modules.aux_functions as aux_func
    import modules.aux_collect_params as aux_collect
    
    # decide, which parameters should be changed
    edit_all = False
    print ("Which input parameters should be changed?")
    edit_choices = aux_func.select_choices(['input files (e.g. image, dem, gcp)', 'camera position', 
                    'camera orientation', 'sensor parameters', 'further projection parameters (roll angle & buffer range)', 
                    'gcp optimisation boundaries (add or change)', 'all of them'], True)
    if('all of them' in edit_choices):
        edit_all = True
    
    ############### edit input files (DEM, image, gcp file) ###################
    if('input files (e.g. image, dem, gcp)' in edit_choices) or edit_all:
        input_dict = aux_collect.add2dict(input_dict, ['dem_file', 'image_file', 'gcp_file'], overwrite = True)
    
    ############### edit camera position ######################################
    ##### edit camera coordinate location
    if('camera position' in edit_choices) or edit_all:
        print ("In which CRS do you want to change the camera position?")
        CRS_choices = aux_func.select_choices(['original CRS', 'DEM CRS'])[0]
        # either in original input CRS
        if (CRS_choices == 'original CRS'):
            input_dict['var_add'] = aux_collect.define_position(input_dict['var_add'], edit = True)
            coordinates_cam = aux_collect.coordinates_2dem_crs(input_dict['var_add'], input_dict['dem_file'])
            d_x = float(coordinates_cam[0]) - float(input_dict['camera_DEMCRS_E'])
            d_y = float(coordinates_cam[1]) - float(input_dict['camera_DEMCRS_N'])
            input_dict['camera_DEMCRS_E']=coordinates_cam[0]
            input_dict['camera_DEMCRS_N']=coordinates_cam[1]
        # or in CRS of DEM data
        else:
            coordinates_cam_old = (input_dict['camera_DEMCRS_E'], input_dict['camera_DEMCRS_N'])
            input_dict = aux_collect.add2dict(input_dict, ['camera_DEMCRS_E', 'camera_DEMCRS_N'], overwrite = True)
            d_x = float(input_dict['camera_DEMCRS_E']) - float(coordinates_cam_old[0])
            d_y = float(input_dict['camera_DEMCRS_N']) - float(coordinates_cam_old[1])
            input_dict = aux_collect.coordinates_from_dem_crs_to_original_crs(input_dict)
            
        # adjust target coordinate location accordingly
        input_dict['target_DEMCRS_E']=input_dict['target_DEMCRS_E'] + d_x
        input_dict['target_DEMCRS_N']=input_dict['target_DEMCRS_N'] + d_y
        input_dict = aux_collect.coordinates_from_dem_crs_to_original_crs(input_dict, name = 'target')
        
        ##### edit camera height or offset
        print ("How do you want to adjust camera height?")
        height_choices = aux_func.select_choices(['keep original offset above ground', 'keep original absolute height', 'Insert new value'])[0]
        if (height_choices == 'keep original offset above ground'):
            input_dict = aux_collect.calc_height_or_offset(input_dict, offset_or_height = 1, edit = True)
        elif (height_choices == 'keep original absolute height'):
            input_dict = aux_collect.calc_height_or_offset(input_dict, offset_or_height = 2, edit = True)
        else:
            input_dict = aux_collect.calc_height_or_offset(input_dict, overwrite = True)
        input_dict = aux_collect.calc_vertical_params(input_dict, pitch = False, height_diff=False)
        
    ############### edit camera orientation ###################################
    if('camera orientation' in edit_choices) or edit_all:
        ##### edit horizontal orientation (Yaw angle or target coordinate location)
        print ("How do you want to adjust camera orientation angles?")
        print ("Yaw Angle / Horizontal Looking Direction:")
        yaw_choices = aux_func.select_choices(['no change', 'change yaw angle', 'change target position'])[0]
        # edit yaw angle
        if (yaw_choices == 'change yaw angle'):
            input_dict['var_add'] = aux_collect.add2dict(input_dict['var_add'], ['yaw_angle_deg'], overwrite = True)
            dx,dy = aux_collect.calc_target_from_lookdir(float(input_dict['var_add']['yaw_angle_deg']),distance = input_dict['var_add']['distance'])
            input_dict['target_DEMCRS_E'] =  float(input_dict['camera_DEMCRS_E']) + dx
            input_dict['target_DEMCRS_N'] =  float(input_dict['camera_DEMCRS_N']) + dy
            input_dict = aux_collect.coordinates_from_dem_crs_to_original_crs(input_dict, name = 'target')
        # edit target position
        if (yaw_choices == 'change target position'):
            print ("In which CRS do you want to change the target position?")
            CRS_choices = aux_func.select_choices(['original CRS', 'DEM CRS'])[0]
            # either in original input CRS
            if (CRS_choices == 'original CRS'):
                input_dict['var_add'] = aux_collect.define_position(input_dict['var_add'], name = 'target', edit = True)
                coordinates_tar = aux_collect.coordinates_2dem_crs(input_dict['var_add'], input_dict['dem_file'], name = 'target')
                input_dict['target_DEMCRS_E']=coordinates_tar[0]
                input_dict['target_DEMCRS_N']=coordinates_tar[1]
            # or in CRS of DEM data
            else:
                input_dict = aux_collect.add2dict(input_dict, ['target_DEMCRS_E', 'target_DEMCRS_N'], overwrite = True)
                input_dict = aux_collect.coordinates_from_dem_crs_to_original_crs(input_dict, name = 'target')
            input_dict['var_add']['yaw_angle_deg'] = aux_collect.calc_orientation(input_dict)
        # aux: recalc distance
        input_dict['var_add']['distance'] = aux_collect.get_distance_tc(input_dict)
                
        ##### edit vertical orientation of the camera using pitch angle, height difference or height of target point
        print ("Pitch Angle / Vertical Looking Direction:")
        print ("How do you want to adjust this orientation angle?")
        input_dict = aux_collect.change_vertical_orientation(input_dict)
            
    ############### edit sensor parameters ####################################
    if('sensor parameters' in edit_choices) or edit_all:
        input_dict = aux_collect.add2dict(input_dict, ['sensor_width_mm', 'sensor_height_mm', 'focalLen_mm'], overwrite = True)
            
    ############### edit roll angle and buffer range ##########################
    if('further projection parameters (roll angle & buffer range)' in edit_choices) or edit_all:
        input_dict = aux_collect.add2dict(input_dict, ['roll_angle_deg', 'buffer_around_camera_m'], overwrite = True)
        
    ############### add or edit gcp optimisation boundaries ###################
    if('gcp optimisation boundaries (add or change)' in edit_choices) or edit_all:
        if not 'opt_boundaries' in input_dict['var_add']:
            input_dict['var_add']['opt_boundaries'] = aux_collect.set_optimisation_boundaries()
            print('optimisation boundaries have been added')
            print('Optimization Boundaries:')
            aux_collect.print_dict(input_dict['var_add']['opt_boundaries'])
            edit = aux_func.check_input("Do you want to edit them?")
        else:
            print('Optimization Boundaries:')
            aux_collect.print_dict(input_dict['var_add']['opt_boundaries'])
            edit=True
        if edit:
            input_dict['var_add']['opt_boundaries'] = aux_collect.set_optimisation_boundaries(input_dict['var_add']['opt_boundaries'])
            
    ############### write edited dict to new json file (optional) #############
    if aux_func.check_input("Do you want to save edited dictionary as new json-file?"):
        name_of_run = input('Old filename: '+ name_of_run + ' \nPlease enter a new filename: \n')
    	##### write resulting dict to json file
        print('\n\nCollected parameters are stored in json file:')
        print(os.path.join(in_dir,name_of_run+".json"))
        jsonfile = json.dumps(input_dict)
        f = open(os.path.join(in_dir,name_of_run+".json"),"w")
        f.write(jsonfile)
        f.close()
    
    # return edited dict and new name of run to main procedure
    return input_dict, name_of_run

################################### end #######################################
###############################################################################
