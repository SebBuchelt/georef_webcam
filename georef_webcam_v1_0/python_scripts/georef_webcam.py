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
%   Name:       georef_webcam.py
%   Purpose:    georef_webcam Version 1.0
%   Comment:    This file is executed from command line to georeference oblique
%               camera images in complex terrain without accurate knowlegde 
%               about the required input parameters.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#############################################################################################################
"""    

############ functionality to call georef_webcam from command line ############

# import required libraries
import argparse
import procedures.georef_procedure as georef

# create parser  with needed and optional input variables
parser = argparse.ArgumentParser(description='Script to georeference webcam images')
parser.add_argument(dest='in_dir', type=str, help='directory containing input')
parser.add_argument(dest='out_dir', type=str, help='output directory')
parser.add_argument("-n", "--name_of_run", type = str, help='naming of PRACTISE run', default='test_run')
parser.add_argument("-no_view","--no_view", help="add, if intermediate projection result should not be shown in Octave", action="store_true")
parser.add_argument("-gcp","--gcp_correction", help="add, if interactive gcp correction is executed (only needed in Windows)", action="store_true")
parser.add_argument("-r","--results", help="add, if only results of a specific run should be calculated", action="store_true")
args = parser.parse_args()
if args.no_view:
    view = False
else:
    view = True
    
# pass arguments to georef procedure
georef.georef_webcam(args.in_dir,args.out_dir, args.name_of_run, view, args.gcp_correction, args.results)
