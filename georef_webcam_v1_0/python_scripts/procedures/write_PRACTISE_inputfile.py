#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
#############################################################################################################
Created on Wed May 06 2020
Last edited on Wed Jun 23 2021

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
%   Name:       procedures/write_PRACTISE_inputfile.py
%   Purpose:    Create input file for PRACTISE procedure
%   Comment:    This file contains the function, which creates the octave file 
%               containing the projection parameters handed to PRACTISE.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#############################################################################################################
"""


###############################################################################
############## function to create input file for PRACTISE procedure ###########
# input:
#       - input_dict: dictionary, which should be edited.
#       - name_of_run: define a name for projection run to recognize output.
#               sub_directory with this name will be created in input_dict['path'] 
#               to store input image and gcp for PRACTISE.
###############################################################################
def create_input(input_dict, name_of_run):
    # import required libraries and submodules of georef_webcam
    import os, shutil
    import modules.aux_functions as aux_func
    
    ##### get empty PRACTISE input file from aux-file folder
    code_dir = os.getcwd()
    code_dir = code_dir.split('georef_webcam_v1_0')
    code_dir = code_dir[0]+'georef_webcam_v1_0'   
    file_name = 'Input_PRACTISE.m'
    aux_file = []
    for r, d, f in os.walk(os.path.join(code_dir, 'python_scripts')):
        for file in f:
            if file_name in file:
                aux_file.append(os.path.join(r, file))

    ##### read octave PRACTISE_input file 
    with open(aux_file[0], 'r') as octave_file:
        PRACTISE_input = octave_file.readlines()

    ############### insert parameters in input file ###########################
    # insert camera position
    value = "["+str(input_dict['camera_DEMCRS_E'])+","+str(input_dict['camera_DEMCRS_N'])+"]"
    PRACTISE_input = aux_func.edit_octave_file(PRACTISE_input, 21, value)
    
    # insert target point position
    value = "["+str(input_dict['target_DEMCRS_E'])+","+str(input_dict['target_DEMCRS_N'])+"]"
    PRACTISE_input = aux_func.edit_octave_file(PRACTISE_input, 25, value)
    
    # insert height offset values for camera and target
    value = "["+str(input_dict['camera_offset'])+","+str(input_dict['target_offset'])+"]"
    PRACTISE_input = aux_func.edit_octave_file(PRACTISE_input, 26, value)
    
    # insert focal length, sensor height & width
    value = str(float(input_dict['focalLen_mm'])/1000)
    PRACTISE_input = aux_func.edit_octave_file(PRACTISE_input, 28, value)
    value = str(float(input_dict['sensor_height_mm'])/1000)
    PRACTISE_input = aux_func.edit_octave_file(PRACTISE_input, 29, value)
    value = str(float(input_dict['sensor_width_mm'])/1000)
    PRACTISE_input = aux_func.edit_octave_file(PRACTISE_input, 30, value)
    
    # insert buffer range & roll angle
    value = str(input_dict['buffer_around_camera_m'])
    PRACTISE_input = aux_func.edit_octave_file(PRACTISE_input, 23, value)
    value = str(input_dict['roll_angle_deg'])
    PRACTISE_input = aux_func.edit_octave_file(PRACTISE_input, 27, value)
    
    ##### insert directories to files
    # directory to dem file:
    value =  "'"+aux_func.dir_for_octave(input_dict['dem_file'])+"'"
    PRACTISE_input = aux_func.edit_octave_file(PRACTISE_input, 7,value)   
    # define working directory of PRACTISE, where it stores input & output 
    value = "'"+aux_func.dir_for_octave(os.path.join(input_dict['path'], 'PRACTISE'))+"\\'"
    PRACTISE_input = aux_func.edit_octave_file(PRACTISE_input, 8, value)   
    # subdirectory where input by PRACTISE is copied to (e.g. image & GCP file)
    PRACTISE_input = aux_func.edit_octave_file(PRACTISE_input, 9, "'"+ str(name_of_run) +"\\'")
    # insert image file extension, so that PRACTISE recognizes the image
    file_name, file_extension = os.path.splitext(input_dict['image_file'])
    PRACTISE_input = aux_func.edit_octave_file(PRACTISE_input, 11, "'"+file_extension+"'")
    
    ##### create directory for PRACTISE input and copy required files to there
    # create directory
    if not os.path.exists(os.path.join(input_dict['path'], 'PRACTISE', str(name_of_run))):
        os.makedirs(os.path.join(input_dict['path'], 'PRACTISE', str(name_of_run)))
    # copy image into this directory
    shutil.copy2(os.path.join(input_dict['image_file']), os.path.join(input_dict['path'], 'PRACTISE', str(name_of_run)))
    
    # edit gcp optimization boundary parameters and add gcp.txt-file, if wanted
    if not (input_dict['gcp_file']==None):
        PRACTISE_input = aux_func.edit_octave_file(PRACTISE_input, 1, str(3))
        # copy gcp.txt file into input directory
        shutil.copy2(os.path.join(input_dict['gcp_file']), os.path.join(input_dict['path'], 'PRACTISE', str(name_of_run)))
        joined_bound = ''
        joined_bound_neg = ''
        for b in input_dict['var_add']['opt_boundaries']:
            joined_bound = ', '.join([joined_bound,str(input_dict['var_add']['opt_boundaries'][b])])
            joined_bound_neg = ', -'.join([joined_bound_neg,str(input_dict['var_add']['opt_boundaries'][b])])
        joined_bound = joined_bound[2:]
        joined_bound_neg = joined_bound_neg[2:]
        output_boundaries = '[' + joined_bound +  ']'
        output_boundaries_neg = '[' + joined_bound_neg +  ']'
        PRACTISE_input = aux_func.edit_octave_file(PRACTISE_input, 36, output_boundaries)
        PRACTISE_input = aux_func.edit_octave_file(PRACTISE_input, 37, output_boundaries_neg)
        
    
############### save edited PRACTISE_input file with new parameters ###########
    with open(os.path.join(input_dict['path'], 'PRACTISE',str(name_of_run) +'.m'), 'w') as octave_file:
        for line in PRACTISE_input:
            octave_file.write(line) 
            
    # return file name of input file (without .m file extension as PRACTISE does not need it)
    return os.path.join(input_dict['path'], 'PRACTISE', str(name_of_run))

################################### end #######################################
###############################################################################
