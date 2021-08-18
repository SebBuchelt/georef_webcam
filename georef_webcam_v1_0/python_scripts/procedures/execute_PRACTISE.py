#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
#############################################################################################################
Created on Thu May 07 2020
Last edited on Tue Jun 29 2021

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
%   Name:       procedures/execute_PRACTISE.py
%   Purpose:    Execute PRACTISE software to georeference image
%   Comment:    This file contains the functions, which download, edit and 
%               execute the PRACTISE script in Octave.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#############################################################################################################
"""


###############################################################################
#################### function to downlaod PRACTISE from git ######ä############
# input:
#       - octave_dir: directory, where PRACTISE package will be stored.
###############################################################################
def dowmload_PRACTISE(octave_dir):
    # import required libraries
    import os, shutil, tempfile, git
    
    ##### download PRACTISE from git repository and save it to octave_dir
    print ('\nDownload PRACTISE package from git... ')
    t = tempfile.mkdtemp()
    git.Repo.clone_from('https://github.com/shaerer/PRACTISE.git', t, branch='master', depth=1)
    shutil.move(os.path.join(t, 'PRACTISE_v2_1'), octave_dir)
    #shutil.rmtree(t)
    print ('Download finished')
    
    ##### comment unnecessary lines in PRACTISE execution code
    with open(os.path.join(octave_dir,'PRACTISE.m'), 'r') as octave_file:
        PRACTISE_input_main = octave_file.readlines()
    l = list(range(1761,1799))
    l.extend(list(range(2487,2492)))
    l.extend([1835])
    for i in l:
        PRACTISE_input_main[i] = '%'+PRACTISE_input_main[i]
        
    ##### edit the style of the octave DEM point projection image
    PRACTISE_input_main[1815] = "            set(figure4, 'NumberTitle', 'off', 'Name', 'Projection Result');\n"
    PRACTISE_input_main[1834] = "            plot(rgbimage(3,(rgbimage(8,:)>=0)), rgbimage(4,(rgbimage(8,:)>=0)), '.', 'Color', [1 0 0], 'MarkerSize', cs_MarkSiz)\n"
    PRACTISE_input_main[1836] = "            Leg=legend('DEM point');\n"
    
    ##### insert a line into header, mentioning, that file was edited by georef_webcam script
    PRACTISE_input_main.insert(33, "%       automatically edited by georef_webcam by Sebastian Buchelt (University of Würzburg, 15/06/2020)\n")
        
    ##### save edited file as new PRACTISE procedure file
    with open(os.path.join(octave_dir,'PRACTISE.m'), 'w') as octave_file:
        for line in PRACTISE_input_main:
            octave_file.write(line) 
            
################################### end #######################################
###############################################################################
    

###############################################################################
############## function to execute PRACTISE projection procedure ##############
# input:
#       - prac_input_file: file name of PRACTISE input file containing information
#                   about parameters and directories to DEM, image, gcp file.
#       - out_dir: directory, where output of PRACTISE and georef_webcam will be stored in subfolders.
#       - name_of_run: name for projection run to recognize output.
###############################################################################

def run_PRACTISE(prac_input_file, run_name, out_dir, gcp):
    # import required libraries and submodules of georef_webcam
    import os, subprocess, time, platform
    import modules.aux_functions as aux_func
    
    ##### get path to PRACTISE software
    code_dir = os.getcwd()
    code_dir = code_dir.split('georef_webcam_v1_0')
    octave_dir = os.path.join(code_dir[0], 'georef_webcam_v1_0', 'PRACTISE_v2_1')    
    
    ##### if path to PRACTISE does not exist, download it from git repository
    if not os.path.exists(octave_dir):
        dowmload_PRACTISE(octave_dir)
    
    ##### write directory to input file in that octave file, which calls input file from the PRACTISE execution
    with open(os.path.join(octave_dir,'Input_PRACTISE.m'), 'r') as octave_file:
        PRACTISE_input_main = octave_file.readlines()
    PRACTISE_input_main = aux_func.edit_octave_file(PRACTISE_input_main, 19, "'"+aux_func.dir_for_octave(prac_input_file)+"'")
    with open(os.path.join(octave_dir,'Input_PRACTISE.m'), 'w') as octave_file:
        for line in PRACTISE_input_main:
            octave_file.write(line) 
            
    ############### start PRACTISE projection run #############################
    python_wd = os.getcwd()     # save current working directory
    os.chdir(octave_dir)        # set wd to directory of PRACTISE scripts
    
    
    ##### call PRACTISE script as subprocess
    #       and print its messages to console 
    print('\nstart ' + run_name +' of PRACTISE...')
    print('this may take some minutes, depending on the size of the DEM file and the complexity of the projection procedure')
    
    if gcp: octave_cmd = 'octave PRACTISE.m --interactive --gui'
    else: octave_cmd = 'octave PRACTISE.m'
    with subprocess.Popen(octave_cmd, shell = True,stdout=subprocess.PIPE, bufsize=1, universal_newlines=True) as p:
            for line in p.stdout:
                print(line, end='') # process line here
    
    ##### print message, that run is finished & reset wd
    print('\n'+str(run_name) + ' of PRACTISE is finished')
    os.chdir(python_wd)
    ############### end PRACTISE projection run ###############################
    
################################### end #######################################
###############################################################################
