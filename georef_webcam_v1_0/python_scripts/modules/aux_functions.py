#!/usr/bin/env python3

# -*- coding: utf-8 -*-
"""
#############################################################################################################
Created on Wed May 6 2020
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
%   Name:       modules/aux_functions.py
%   Purpose:    Auxiliary Functions for georef_webcam package
%   Comment:    This file contains general auxiliary functions for the
%               georef_webcam package.
%
%   Overview:   check_input: creates Yes/No-Questionaire
%               select_choices: creates multiple/single-choice questionaire
%               edit_octave_file: edits parameter values in PRACTISE input file
%               dir_for_octave: converts directory strings in octave readable
%                       format
%               print_subprocess_messages: prints subprocess_messages to 
%                       command prompt
%               select_file: searches for all files with specific file ending
%                       in given directories and all subdirectories. Returns  
%                       the filename, if only one exists, or gives option to  
%                       select one filename from list.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#############################################################################################################
"""

############### create Yes/No - Questionaire and return True/False as output ################################
# input:
#       - question: string with question to ask (like: "Do you want to continue procedure?")
def check_input(question):
    parameter = input(question + '  y/n \n')
    if(parameter=='y'):
        parameter=True
        print ('Yes\n')
    else: 
        parameter=False
        print ('No\n')
    return parameter
#############################################################################################################



############### select various choices from a list of options - single and multiple choice possible #########
# input:
#       - list_of_choices: list of strings with options to select
#       - multiple_choice: if True, allows to select multiple options; otherwise only one choice van be selected
def select_choices(list_of_choices, multiple_choice=False):
    # define aux variables
    selected_choices=''
    i=0
    
    ##### show options
    print("Please select out of the following options:")
    for f in list_of_choices:
        print( str(i) + ': '+ f)
        i=i+1
    
    ##### explain multiple choice
    if multiple_choice:
        print("Multiple options can be selected. In this case please, separate them by comma like this: '0, 2, 3'")
        
    ##### collect selected choices from input
    while(selected_choices==''):
        selected_choices = input("Which of the options do you want to choose? \n")
        
    ##### read selected choices into new list
    if multiple_choice:
        file_list=[list_of_choices[int(x)] for x in selected_choices.split(',')]
        print("'"+"', '".join(file_list)+"' are selected")
    else:
        file_list = [list_of_choices[int(selected_choices)]]
        print("'"+str(file_list[0])+"' is selected")
    # return list of selections to main procedure
    return file_list
#############################################################################################################



############### edit line in octave input file for PRACTISE #################################################
# input:
#       - octave_txt: txt-file as list of strings (one string for each line in txt file)
#       - line: selected line to be edited
#       - input_value: new value to be inserted
def edit_octave_file(octave_txt, line, input_value):
    # get parameter name from octave file (e.g. "height")
    param = octave_txt[line].split('=')[0]   
    # get comment from octave file (e.g. "This is the height of the camera above ground")
    comment = octave_txt[line].split(';')[1]   
    # insert new value between parameter and comment
    new_line = '='.join([param,input_value])
    new_line = ';'.join([new_line, comment])
    # => newline example: "height = [input_value]; This is the height of the camera above ground"
    octave_txt[line] = new_line
    #return edited octave txt file to main procedure
    return octave_txt
#############################################################################################################



############### change directory description to octave readable #############################################
# input:
#       - directory_name: directory, which should be converted
def dir_for_octave(directory_name):
    return '\\'.join(directory_name.split('/'))
#############################################################################################################



############### print output messages of subprocess while running ###########################################
# input:
#       - process: process currently executed (e.g. PRACTISE run)
def print_subprocess_messages(process):
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print (output.strip())
#############################################################################################################



############### select a file with specific file ending in given directories ################################
# input:
#       - in_dir: directory or list of directories to search through
#       - extension: file extension to look for
#       - sub_dir: if set, only a specific subdirectory will be screened
#       - name: aux variable to clarify in questionaire at the end, which data is looked for
def select_file(in_dir, extension, sub_dir = False, name = 'DEM'):
    # import required libraries
    import os, sys
    # if selected, search only in specific subdirectory for files
    if sub_dir:
        in_dir = os.path.join(in_dir, sub_dir)
        
    # convert in_dir to list, if needed
    if type(in_dir) == str:
        in_dir = [in_dir]
    # get base directory of all input directories
    base_dir = os.path.dirname(os.path.commonprefix(in_dir))
    
    ##### collect all files with specific file ending in given directories
    file_list = []
    for folder in in_dir:
        for r, d, f in os.walk(folder):
            for file in f:
                if file.endswith(extension):
                    file_list.append(os.path.join(r, file))
    file_list = [os.path.relpath(f, base_dir) for f in file_list]
    
    ##### if no file could be found, end program
    if len(file_list) == 0:
        print("No file with this file extension ("+ extension +") could be found.")
        print('Stop programm')
        sys.exit() 
    ##### if several possible files exist, choose:
    if not (len(file_list)==1):
        print("Which of the files is the " + name + " file, you want to use?")
        file_list = select_choices(file_list)
    selected_file = os.path.join(base_dir,file_list[0])
    
    # return selected or detected file to main procedure
    return selected_file
#############################################################################################################