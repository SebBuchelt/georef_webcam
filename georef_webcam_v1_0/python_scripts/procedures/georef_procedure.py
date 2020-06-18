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
%   Name:       procedures/georef_procedure.py
%   Purpose:    Run whole georeferencing procedure
%   Comment:    This file contains the main execution function of georef_webcam
%               starting with the collection of parameters, continuing with 
%               passing them to PRACTISE and finally producing the results.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#############################################################################################################
"""

###############################################################################
################## function to run georeferencing procedure ###################
# input:
#       - in_dir: directory, where the DEM file, the camera image and the gcp file (optional) are stored.
#                   The files can be stored in separate subdirectories.
#       - out_dir: directory, where output of PRACTISE and georef_webcam will be stored in subfolders.
#       - name_of_run (optional): define a name for projection run to recognize output (default: test_run).
#       - view: if set False, octave image file with projection result of PRACTISE will not be plotted after executing PRACTISE.
###############################################################################
def georef_webcam (in_dir, out_dir, name_of_run = "test_run", view = True):
    # import required libraries and submodules of georef_webcam
    import modules.aux_functions as aux_func
    import procedures.collect_projection_parameters as collect_params
    import procedures.edit_projection_parameters as edit_params
    import procedures.write_PRACTISE_inputfile as prac_input
    import procedures.execute_PRACTISE as exe_prac
    import procedures.results as proj_results
    import json
    
    ##### create or read dictionary with projection parameters
    if(aux_func.check_input("Do you want to create a new set of projection parameters?")):
        dict_file = collect_params.create_dict(in_dir, out_dir, name_of_run)
    else:
        print("Find existing json dataset...")
        json_file = aux_func.select_file(in_dir, 'json', name = 'dict')
        with open(json_file) as read_file:
            dict_file = json.load(read_file)
        dict_file['path'] = out_dir
        
    ##### possibility to edit projection parameters
    if(aux_func.check_input("Do you want to edit the projection parameters?")):
        dict_file, name_of_run = edit_params.edit_parameters(dict_file, in_dir, name_of_run)
    out_dir = dict_file['path']        # path to store PRACTISE output
         
    ############### start PRACTISE projection calculation #####################
    while True:
        ##### write parameters from dict into PRACTISE input file
        prac_input_file = prac_input.create_input(dict_file, name_of_run)
        
        ##### call PRACTISE and calculate the prepared projection
        exe_prac.run_PRACTISE(prac_input_file, name_of_run, out_dir)
        
        ##### show octave image file with projection result of PRACTISE 
        if view:
            proj_results.show_result(out_dir, name_of_run)
        
        ##### extract optimized projection parameters of GCP optimization and store them in json-file (optional)
        old_dict = False
        if not (dict_file['gcp_file']==None):
            print("Projection parameters have been optimized with GCP optimisation")
            if(aux_func.check_input("Do you want to extract optimized projection parameters and store them in a dict file?")):
                old_dict = dict_file
                dict_file, name_of_run = proj_results.extract_params(dict_file, name_of_run, in_dir)
            
        # decide, how to continue
        print("Projection has been executed. \nWhat do you want to do next?")
        next_step = aux_func.select_choices(['end procedure', 'edit projection input parameters and repeat projection procedure', 'produce georef_webcam output'])[0]
        
        ##### option 1: edit projection parameters and rerun projection procedure in PRACTISE
        if(next_step == 'edit projection input parameters and repeat projection procedure'):
            if old_dict:
                print("Which parameters do you want to edit?")
                edit_file = aux_func.select_choices(['optimized parameters', 'original parameters'])[0]
                if (edit_file == 'original parameters'):
                    dict_file = old_dict
            dict_file, name_of_run = edit_params.edit_parameters(dict_file, in_dir, name_of_run)
            if not aux_func.check_input("Do you want to rerun projection with adjusted parameters?"):
                break
            out_dir = dict_file['path']        # path to store PRACTISE output
            
        ##### option 2: end program directly
        elif(next_step == 'end procedure'):
            break
            
        ##### option 3: produce georef_webcam output (coordinate rasters, mask, projected image)
        elif(next_step == 'produce georef_webcam output'):
            proj_results.calc_result(dict_file, name_of_run)
            print('Producing of results sucessfully finished')
            break
    
    print('End of programm')
    ############### end of PRACTISE projection calculation ####################

################################### end #######################################
###############################################################################