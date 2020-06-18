#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
#############################################################################################################
Created on Thu May 07 2020
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
%   Name:       procedures/collect_projection_parameters.py
%   Purpose:    Collect parameters for image projection and store results
%   Comment:    This file contains the function, which collects and calculates 
%               the parameters required for the projection procedure in 
%               PRACTISE, stores them in a json-file and returns the created 
%               dictionary to the main procedure.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#############################################################################################################
"""

###############################################################################
################## function to collect projection parameters ##################
# input:
#       - in_dir: directory, where the DEM file, the camera image and the the gcp file (optional) are stored.
#                   The files can be stored in separate subdirectories. The resulting json-file will be stored
#                   in this directory as well.
#       - out_dir: directory, where output of PRACTISE and georef_webcam will be stored in subfolders.
#       - name_of_run: define a name for projection run to recognize output.
###############################################################################
def create_dict(in_dir, out_dir, name_of_run):
    # import required libraries and submodules of georef_webcam
    import collections, json, os
    import modules.aux_functions as aux_func
    import modules.aux_collect_params as aux_collect
     
    ##### create dictionary with parameters required for PRACTISE
    var_mand = ['path', 'image_file', 'dem_file', 'gcp_file', 'camera_DEMCRS_E', 'camera_DEMCRS_N', 'camera_offset', 
                'target_DEMCRS_E', 'target_DEMCRS_N', 'target_offset', 'roll_angle_deg', 
                'focalLen_mm', 'sensor_width_mm', 'sensor_height_mm', 'buffer_around_camera_m', 'var_add']
    input_dict = collections.OrderedDict((k, None) for k in var_mand)
    input_dict['var_add'] = collections.OrderedDict()
    
    ##### add existing default values
    sensor_parameters = ['sensor_width_mm', 'sensor_height_mm', 'focalLen_mm', 'roll_angle_deg', 'buffer_around_camera_m', 'camera_offset', 'target_offset']
    sensor_default = [22.3, 14.9, 14.0, 0.0, 100.0, 0, 0]
    input_dict = aux_collect.add2dict(input_dict, sensor_parameters, sensor_default)

    ############### define directories to output & input ######################
    # path to store PRACTISE output
    input_dict['path'] = out_dir        
    
    # select image file, which should be projected
    image_ending = input("Which file extension does the image have? (write extension without .) \n")
    input_dict['image_file'] = aux_func.select_file(in_dir, image_ending, name = 'image')
    print('Selected image: ', input_dict['image_file'])
    
    # select DEM used for projection
    dem_ending = input("Which file extension does the DEM raster have? (write extension without .) \n")
    input_dict['dem_file'] = aux_collect.select_dem_file(in_dir, dem_ending)
    print('Selected DEM file: ', input_dict['dem_file'])
    
    ############### define camera location ####################################
    # coordinates of camera position
    input_dict['var_add'] = aux_collect.define_position(input_dict['var_add'])
    coordinates_cam = aux_collect.coordinates_2dem_crs(input_dict['var_add'], input_dict['dem_file'])
    input_dict['camera_DEMCRS_E']=coordinates_cam[0]
    input_dict['camera_DEMCRS_N']=coordinates_cam[1]
    
    # camera height or offset
    input_dict = aux_collect.calc_height_or_offset(input_dict)
    
    ############### define camera orientation #################################
    if(aux_func.check_input("Do you want to insert target point coordinates (y) or use orientation angle (n) instead?")):
        ##### target point approach
        target = True
        input_dict['var_add'] = aux_collect.define_position(input_dict['var_add'], name = 'target')
        coordinates_tar = aux_collect.coordinates_2dem_crs(input_dict['var_add'], input_dict['dem_file'], name = 'target')
        input_dict['target_DEMCRS_E']=coordinates_tar[0]
        input_dict['target_DEMCRS_N']=coordinates_tar[1]
        input_dict['var_add']['yaw_angle_deg'] = aux_collect.calc_orientation(input_dict)
    else:
        ##### orientation angle approach
        input_dict = aux_collect.orientation_angle(input_dict)
        input_dict = aux_collect.coordinates_from_dem_crs_to_original_crs(input_dict, name = 'target', epsg = True)
        target = False
        
    # aux: calculate distance between camera and target
    input_dict['var_add']['distance'] = aux_collect.get_distance_tc(input_dict)
    
    ##### define vertical oriantation of the camera using pitch angle, height difference or height of target point
    input_dict = aux_collect.define_vertical_orientation(input_dict, target)

    ############### edit or add further parameters if wanted ##################
    ##### roll angle, camera system parameters and buffer range
    print('Further variables have been predefined, but can be adjusted now.')
    print('(The predefined value of each parameter is showm behind it.)\n')
    choice_list = ['edit none of them']
    choice_list.extend(aux_collect.print_dict(input_dict, ['roll_angle_deg', 'sensor_width_mm', 
                        'sensor_height_mm','focalLen_mm','buffer_around_camera_m'], do_return = True))
    additional_params = aux_func.select_choices(choice_list, multiple_choice=True)
    if not(additional_params[0]=='edit none of them'):
        additional_params=[x.split(':')[0] for x in additional_params]
        
        ##### edit roll angle, if wanted
        if('roll_angle_deg' in additional_params):
            print("\n\nAdjust roll angle...")
            input_dict=aux_collect.add2dict(input_dict,['roll_angle_deg'], overwrite=True)
        
        ##### define camera system parameters
        cam_param = set(['sensor_width_mm', 'sensor_height_mm', 'focalLen_mm']).intersection(additional_params)
        if cam_param:
            print("\n\nAdjust camera system parameters... ")
            input_dict=aux_collect.add2dict(input_dict,cam_param, overwrite=True)
        
        ##### adjust buffer
        if('buffer_around_camera_m' in additional_params):
            print("\n\nAdjust remaining projection parameter (buffer)... \nDefault value:")
            input_dict=aux_collect.add2dict(input_dict,['buffer_around_camera_m'], overwrite=True)
        
    ############### add GCP file for projection optimisation if available #####
    if(aux_func.check_input("Do you have GCPs available to run the DDS optimisation in PRACTISE?")):
        # select gcp file
        input_dict['gcp_file'] = aux_func.select_file(in_dir, 'gcp.txt', name = 'GCP')
        
        # add and adjust optimization boundaries, if wanted
        input_dict['var_add']['opt_boundaries'] = aux_collect.set_optimisation_boundaries()
        print('Optimization Boundaries:')
        aux_collect.print_dict(input_dict['var_add']['opt_boundaries'])
        if(aux_func.check_input("Do you want to adjust the optimisation boudaries?")):
            input_dict['var_add']['opt_boundaries'] = aux_collect.set_optimisation_boundaries(input_dict['var_add']['opt_boundaries'])
        

	############### write resulting dict to json file #########################
    print('\n\nCollected parameters are stored in json file:')
    print(os.path.join(in_dir,name_of_run+".json"))
    jsonfile = json.dumps(input_dict)
    f = open(os.path.join(in_dir,name_of_run+".json"),"w")
    f.write(jsonfile)
    f.close()
    
    # return dictionary to main procedure
    return input_dict

################################### end #######################################
###############################################################################
    


###############################################################################
#### function to collect mandatory projection parameters directly via input ###
###############################################################################
def write_dict(image, dem, camera_pos, target_pos, offset_camera, offset_target, PRACTISE_dir,
               roll_angle = 0, focal_length = 14, sensor_width = 14, sensor_height = 22, buffer = 100, json_filename = False, gcp = None, edit_boundaries=False, cam_epsg = ''):
    # import libraries and submodules of georef_webcam
    import collections, json
    import modules.aux_collect_params as aux_collect
     
    ##### create dictionary with parameters required for PRACTISE
    var_mand = ['path', 'image_file', 'dem_file', 'gcp_file', 'camera_DEMCRS_E', 'camera_DEMCRS_N', 'camera_offset', 
                'target_DEMCRS_E', 'target_DEMCRS_N', 'target_offset', 'roll_angle_deg', 
                'focalLen_mm', 'sensor_width_mm', 'sensor_height_mm', 'buffer_around_camera_m', 'var_add']
    input_dict = collections.OrderedDict((k, None) for k in var_mand)
    input_dict['var_add'] = collections.OrderedDict()
    
    ##### create dict from passed input parameters
    input_dict = aux_collect.add2dict(input_dict, var_mand, 
        values=[PRACTISE_dir, image, dem, gcp, camera_pos[0], camera_pos[1], offset_camera, 
                target_pos[0], target_pos[1], offset_target, roll_angle, focal_length, 
                sensor_width, sensor_height, buffer, collections.OrderedDict()])
    
    ##### calculate additional optional parameters to make editing of parameters possible
    print('calculate additional optional parameters...')
    input_dict['var_add']['camera_epsg']=cam_epsg
    input_dict = aux_collect.coordinates_from_dem_crs_to_original_crs(input_dict)
    input_dict = aux_collect.coordinates_from_dem_crs_to_original_crs(input_dict, name = 'target', epsg = True)
    input_dict = aux_collect.calc_height_or_offset(input_dict, offset_or_height=1, edit = True)
    input_dict['var_add']['yaw_angle_deg'] = aux_collect.calc_orientation(input_dict)
    input_dict['var_add']['distance'] = aux_collect.get_distance_tc(input_dict)
    input_dict = aux_collect.calc_vertical_params(input_dict, offset = False)

    # add and adjust optimization boundaries, if wanted
    if not (gcp == None):
        input_dict['var_add']['opt_boundaries'] = aux_collect.set_optimisation_boundaries()
        if (edit_boundaries):
            print('Optimization Boundaries:')
            aux_collect.print_dict(input_dict['var_add']['opt_boundaries'])
            input_dict['var_add']['opt_boundaries'] = aux_collect.set_optimisation_boundaries(input_dict['var_add']['opt_boundaries'])
        
    ############### write resulting dict to json file (optional) ##############
    if (json_filename):
        print('\n\nCollected parameters are stored in json file:')
        print(json_filename)
        jsonfile = json.dumps(input_dict)
        f = open(json_filename,"w")
        f.write(jsonfile)
        f.close()
        
    # return created dictionary to main procedure
    return input_dict
    
################################### end #######################################
###############################################################################