#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
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
%   Name:       modules/aux_collect_params.py
%   Purpose:    Aux Functions to collect and calculate parameters for PRACTISE
%   Comment:    This file contains auxiliary functions to collect and calculate
%               projection parameters for the dictionary created in 
%               georef_webcam.
%
%   Overview:   print_dict: prints dict to console as table
%               add2dict: edits/changes/overwrites values in an existing 
%                       dictionary
%               select_dem_file: selects DEM file from given directory and 
%                       converts it into PRACTISE readable format
%               define_position: creates a point including CRS information and 
%                       coordinate location (used to define camera & target)
%               project_point: runs projection procedure needed for the 
%                       following two functions
%               coordinates_2dem_crs: projects a point coordinate to DEM CRS
%               coordinates_from_dem_crs_to_original_crs: reprojects a point 
%                       coordinate from the DEM CRS back to the original used
%                       input CRS
%               get_height: extracts value at a defined location from DEM file
%               calc_height_or_offset: define vertical position of camera or 
%                       target by absolute height or offset above ground
%               calc_target_from_lookdir: calculates target location from a 
%                       given camera position, looking direction and distance
%               orientation_angle: defines aux variable orientation angle (yaw)
%               calc_orientation: calculates orientation angle from given
%                       camera & target position
%               calc_vertical_params: calculates all other parameters defining 
%                       the vertical orientation
%               define_vertical_orientation: function to define vertical
%                       orientation
%               change_vertical_orientation: function to change vertical
%                       orientation parameters
%               set_optimisation_boundaries: set or edit optimization 
%                       boundaries for GCP optimization in PRACTISE
%               get_distance_tc: calculates distance between camera and target
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

#############################################################################################################
"""

############### print dictionary as table to console ########################################################
# input:
#       - dictionary: dictionary to be printed
#       - params: list of selected parameters to be printed
#       - do_return: boolean; if True, return dictionary printed rows as a list instead of direct printing it to console
def print_dict(dictionary, params =False, do_return = False):
    # if no params defined, print whole dict
    if params == False:
        params = dictionary
    # return printed dict as list to main procedure
    if(do_return):
        return_list = []
        for i in params:
            return_list.extend([str(i) + ': '+ str(dictionary[i])])
        return return_list
    # or print it directly
    else:
        for i in params:
            print (str(i) + ': '+ str(dictionary[i]))
#############################################################################################################
    
    

############### add/change/overwrite values in an existing dictionary #######################################
# input:
#       - dictionary: dictionary to be edited
#       - params: list of selected parameters to be edited
#       - values: list of values to be inserted
#       - overwrite: boolean; if True, console input overwrites existing values, unless empty input: then old value is kept
def add2dict(dictionary, params, values=False, overwrite = False):
    ##### overwriting mode
    if (overwrite):
        print ("Overwriting mode: If you want to keep old value, leave input empty")
        for i in params:
            new_value = input("Write value for parameter "+str(i)+" (old value: " + str(dictionary[i]) + "):  \n")
            if not(new_value==""):
                dictionary[i] = new_value
               
    ##### editing mode with already given values
    elif (values):
        for i in range(len(params)):
            dictionary[params[i]] = values[i]
            
    ##### add values for parameters, which are so far empty
    else:
        for i in params:
            dictionary[i]=None
            while (dictionary[i]==None) or (dictionary[i]==""):
                new_value = input("Write value for parameter "+str(i)+":  \n")
                dictionary[i] = new_value
    # return edited dictionary to main procedure
    return dictionary
#############################################################################################################



############### selection of DEM file & conversion into PRACTISE readable format ############################
# input:
#       - in_dir: directory or list of directories to search through
#       - dem_ending: DEM file extension to look for
#       - sub_dir: if set, only a specific subdirectory will be screened
def select_dem_file(in_dir, dem_ending, sub_dir = False):
    # import required libraries and submodules of georef_webcam
    import os, subprocess
    import modules.aux_functions as aux_func
    
    ##### choose DEM file with specified extension from directory
    dem_file = aux_func.select_file(in_dir, dem_ending, sub_dir)
    
    ##### confirm metric/cartesian CRS of DEM, if not reproject to a cartesian CRS of choice, preferably UTM Zone
    print(' \n\nPRACTISE requires DEM data in a cartesian/metric Coordinate Reference System, ergo geographic/lat-lon coordinates are not allowed:')
    if(aux_func.check_input("Hence, is your data in metric coordinates?")):
        print('Continue with next steps...')
    else:
        print (" \nThen you have to reproject your dem raster to a metric CRS - preferably UTM:")
        dem_file_new = os.path.join(os.path.dirname(dem_file),'reproj_'+os.path.basename(dem_file)[0:-3]+'tif')
        epsg_str = 'EPSG:'+ input("Please enter epsg-nr of your preferred CRS: \n")
        subprocess.call(['gdalwarp', '-of', 'GTiff', '-t_srs', epsg_str,  dem_file, dem_file_new])
        dem_file = dem_file_new
        
    ##### if DEM in tif format, convert to ascii-file, which is required for PRACTISE
    if not (dem_file.endswith('.asc')):
        dem_file_new = dem_file[0:-3]+'asc'
        print ('Converting into the required ASCII-Grid format...')
        subprocess.call(['gdal_translate', '-of', 'AAIGrid', '-a_nodata', '-3.402823466e+38', dem_file, dem_file_new])
        dem_file = dem_file_new
    	
    ##### decrease spatial resolution of DEM file, if you want to fasten the projection calculation
    if(aux_func.check_input("Do you want to resample your DEM data to new resolution?")):
        resolution = float(input('Which spatial resolution should the resampled DEM have? \n'))
        dem_file_new = dem_file[0:-4]+'_res' + str(int(resolution)) + '.asc'
        subprocess.call(['gdal_translate', '-of', 'AAIGrid', '-a_nodata', '-3.402823466e+38', '-tr', str(resolution), str(resolution), '-r', 'bilinear', dem_file, dem_file_new])
        dem_file = dem_file_new
        
    # return dem file name used for PRACTISE to main procedure
    return dem_file
#############################################################################################################



############### defining camera/target position #############################################################
# input:
#       - aux_dict: dictionary containing auxiliary projection variables 
#       - name: either 'camera' or 'target' to define created point
#       - edit: boolean; if True, existing coordinate values are overwritten
def define_position(aux_dict, name = 'camera', edit = False):
    # import required submodules of georef_webcam
    import modules.aux_functions as aux_func
    
    ##### create new point
    if not edit:
        if(aux_func.check_input("Is the "+name + " position known in geographic / lat-lon coordinates (y) or in cartesian coordinates (n)?")):
            aux_dict[name+'_epsg'] = str(4326)
        else:
            aux_dict[name+'_epsg'] = input('Please insert EPSG-Nr. of CRS (if empty: CRS of input DEM): \n')
       
    ##### or edit existing point coordinates
    # either lat lon coordinates
    if(aux_dict[name+'_epsg'] == str(4326)):
        aux_dict = add2dict(aux_dict, [name+'_longitude', name+'_latitude'],overwrite=edit)
        aux_dict[name+'_x'] = aux_dict[name+'_longitude']
        aux_dict[name+'_y'] = aux_dict[name+'_latitude']
    # or Easting & Northing coordinates
    else:
        aux_dict = add2dict(aux_dict, [name+'_Easting', name+'_Northing'],overwrite=edit)
        aux_dict[name+'_x'] = aux_dict[name+'_Easting']
        aux_dict[name+'_y'] = aux_dict[name+'_Northing']
    
    # return new dictionary to main procedure
    return aux_dict
#############################################################################################################



############### transform point coordinates from input CRS to CRS of a raster file or vice versa ############
# input:
#       - raster_dir: directory to raster dataset
#       - x_coord: x coordinate of point
#       - y_coord: y coordinate of point
#       - epsg_point: epsg nr of CRS of point
#       - reverse: boolean; if True, point coordinate is projected from raster CRS to CRS of EPSG number
def project_point(raster_dir, x_coord, y_coord, epsg_point, reverse = False):
    # import required libraries
    import gdal
    from osgeo import ogr, osr
    from osgeo.gdalconst import GA_ReadOnly
    
    ##### get CRS from DEM and of input coordinates
    DemDs = gdal.Open(raster_dir, GA_ReadOnly)
    pj=DemDs.GetProjection()
    target = osr.SpatialReference()
    source = osr.SpatialReference()

    ##### define projection direction (to or from DEM CRS)
    if not reverse:
        target.ImportFromWkt(pj)
        source.ImportFromEPSG(int(epsg_point))
    else:
        target.ImportFromEPSG(int(epsg_point))
        source.ImportFromWkt(pj)

    ##### project coordinates
    transform = osr.CoordinateTransformation(source, target)
    point = ogr.CreateGeometryFromWkt("POINT ("+str(x_coord)+" "+str(y_coord)+")")
    point.Transform(transform)
    # return projected coordinated to main procedure
    return (point.GetX(), point.GetY())
#############################################################################################################



############### project target & camera position to DEM CRS #################################################
# input:
#       - aux_dict: dictionary containing auxiliary projection variables 
#       - dem_path: directory to DEM file
#       - name: either 'camera' or 'target' to define projected point
def coordinates_2dem_crs(aux_dict, dem_path, name = 'camera'):
    ##### if same CRS as DEM, copy original coordinate values
    if (aux_dict[name+'_epsg'] == ''):
        return (aux_dict[name+'_x'], aux_dict[name+'_y'])
    ##### else: project coordinate values to DEM CRS
    else: 
        return project_point(dem_path, aux_dict[name+'_x'], aux_dict[name+'_y'], aux_dict[name+'_epsg'])
#############################################################################################################



############### transform target & camera position from DEM CRS to input CRS ################################
# input:
#       - dictionary: dictionary containing all projection parameters
#       - name: either 'camera' or 'target' to define projected point
#       - epsg: boolean; if True, camera epsg is also used for target point 
#                   (only use in cases, when no epsg for target is selected)
def coordinates_from_dem_crs_to_original_crs(dictionary, name = 'camera', epsg = False):
    # copy camera epsg to target
    if (epsg):
        dictionary['var_add'][name+'_epsg'] = dictionary['var_add']['camera_epsg']
    ##### if point epsg is same as DEM, just copy variable values
    if (dictionary['var_add'][name+'_epsg'] == ''):
        dictionary['var_add'] = add2dict(dictionary['var_add'], [name+'_Easting', name+'_Northing'], values = [dictionary[name+'_DEMCRS_E'], dictionary[name+'_DEMCRS_N']])
        dictionary['var_add'] = add2dict(dictionary['var_add'], [name+'_x', name+'_y'], values = [dictionary[name+'_DEMCRS_E'], dictionary[name+'_DEMCRS_N']])
    ##### else: project coordinate values to original input CRS
    else:
        reproj = project_point(dictionary['dem_file'], dictionary[name+'_DEMCRS_E'], dictionary[name+'_DEMCRS_N'], dictionary['var_add'][name+'_epsg'], reverse = True)
        dictionary['var_add'] = add2dict(dictionary['var_add'], [name+'_x', name+'_y'], values = reproj)
        if(dictionary['var_add'][name+'_epsg'] == str(4326)):
            dictionary['var_add'] = add2dict(dictionary['var_add'], [name+'_longitude', name+'_latitude'], values = reproj)
        else:
            dictionary['var_add'] = add2dict(dictionary['var_add'], [name+'_Easting', name+'_Northing'], values = reproj)
    
    # return new dictionary to main procedure
    return dictionary
#############################################################################################################
    


############### extract dem raster value at certain location & add it to dictionary #########################
# input:
#       - dictionary: dictionary containing all parameters (point location, DEM file directory)
#       - name: either 'camera' or 'target' to define point
def get_height(dictionary, name = 'camera'):
    # import required libraries
    import gdal, struct
    from osgeo.gdalconst import GA_ReadOnly
    
    ##### open DEM file and get projection information
    DemDs = gdal.Open(dictionary['dem_file'], GA_ReadOnly)
    gt=DemDs.GetGeoTransform()
    dem_band=DemDs.GetRasterBand(1)
    
    ##### identify pixel position of point in raster
    mx = float(dictionary[name+'_DEMCRS_E'])
    my = float(dictionary[name+'_DEMCRS_N'])
    px = int(round((mx - gt[0]) / gt[1])) #x pixel position in raster
    py = int(round((my - gt[3]) / gt[5])) #y pixel position in raster
    
    ##### collect height value (if outside of extent, return: 0)
    if(px>=0 and px<dem_band.ReadAsArray().shape[0] and py>=0 and py<dem_band.ReadAsArray().shape[1]):
        height = dem_band.ReadRaster(px,py,1,1,buf_type=gdal.GDT_UInt16) #Assumes 16 bit int aka 'short'
        height = struct.unpack('h' , height) #use the 'short' format code (2 bytes) not int (4 bytes)
    else:
        print(name + " point is outside of DEM raster extent.\nThe DEM height is artificially set to 0")
        print("Please check your coordinates to confirm if input was correct.")
        height = [0]
    # return height value to main procedure
    return height[0]
#############################################################################################################



############### define vertical position of camera or target point ##########################################
# input:
#       - dictionary: dictionary containing all parameters (point location, DEM file directory)
#       - name: either 'camera' or 'target' to define point
#       - offset_or_height:     0: choose option
#                               1: change offset above ground and derive absolute height from it
#                               2: change absolute height and derive offset above ground from it
#       - edit: either 'camera' or 'target' to define point
#       - edit: boolean; if True, either:
#                   offset_or_height==1: offset above ground is kept and absolute height is adjusted to new point location dem height
#                   offset_or_height==2: absolute height is kept and offset above ground is adjusted to new point location dem height
#       - overwrite: boolean; if True, existing values are overwritten, unless empty input: then old value is kept
def calc_height_or_offset(dictionary, name = 'camera', offset_or_height = 0, edit = False, overwrite = False):
    # import required submodules of georef_webcam
    import modules.aux_functions as aux_func
    
    ##### get DEM height at point
    dem_height = get_height(dictionary, name)
    dictionary['var_add'][name+'_DEM_height'] = dem_height
    print("The DEM height at the " + name + " location is: "+str(int(dem_height))+ 'm')
    
    ##### select, whether to define offset above ground or absolute height
    if (offset_or_height==0):
        if(aux_func.check_input("Do you want to insert offset above ground (y) or use absolute height (n) instead?")):
            offset_or_height=1
        else:
            offset_or_height=2
    
    ##### keep, overwrite or create offset above ground and then derive absolute height from it
    if(offset_or_height==1):
        if not edit:
            if overwrite:
                dictionary = add2dict(dictionary, [name+'_offset'], overwrite = True)
            else:
                dictionary[name+'_offset'] = input("Please enter offset above ground: \n")
        dictionary['var_add'][name+'_DEMCRS_Z'] = dem_height + float(dictionary[name+'_offset'])
        
    ##### or keep, overwrite or create absolute height and then derive offset above ground from it
    if(offset_or_height==2):
        if not edit:
            if overwrite:
                dictionary = add2dict(dictionary, [name+'_offset'], overwrite = True)
            else:
                dictionary['var_add'][name+'_DEMCRS_Z'] = input('Please enter absolute height of '+ name+ ': \n')
        dictionary[name+'_offset'] = float(dictionary['var_add'][name+'_DEMCRS_Z']) - dem_height
        
    # return new dictionary to main procedure
    return dictionary
#############################################################################################################



############### calculate the coordinate offset of target from direction angle ##############################
# input:
#       - direction: orientation / yaw angle
#       - distance: distance between camera and target (default: 1000m)
def calc_target_from_lookdir(direction, distance = 1000):
    # import required libraries
    import math, sys
    ##### calculate coordinate offset
    if(0<=direction<45) or (315<=direction<=360):
        dy=distance*math.cos(math.radians(direction))
        dx=dy*math.tan(math.radians(direction))
    elif(45<=direction<135):
        dx=distance*math.sin(math.radians(direction))
        dy=-dx*math.tan(math.radians(direction-90))
    elif(135<=direction<225):
        dy=distance*math.cos(math.radians(direction))
        dx=dy*math.tan(math.radians(direction-180))
    elif(225<=direction<315):
        dx=distance*math.sin(math.radians(direction))
        dy=-dx*math.tan(math.radians(direction-270))
    else:
        print('Error: direction angle not within possible range (0, 360)')
        sys.exit()      
    # return offset to main procedure
    return dx, dy
#############################################################################################################
    


############### define orientation / yaw angle ##############################################################
# input:
#       - dictionary: dictionary containing all projection parameters
def orientation_angle(dictionary):
    ##### collect orientation angle
    print('Orientation angle is required: North: 0/360°, East: 90°, South: 180°, West: 270°')
    print('Possible value range: 0-360°')
    dictionary['var_add']['yaw_angle_deg'] = input("Please insert yaw or orientation angle [°]: \n ")
    ##### derive target point location from it
    dx,dy = calc_target_from_lookdir(float(dictionary['var_add']['yaw_angle_deg']))
    dictionary['target_DEMCRS_E'] =  float(dictionary['camera_DEMCRS_E']) + dx
    dictionary['target_DEMCRS_N'] =  float(dictionary['camera_DEMCRS_N']) + dy
    # return new dictionary to main procedure
    return dictionary
#############################################################################################################
    


############### derive orientation / yaw angle from target and camera location ##############################
# input:
#       - dictionary: dictionary containing all projection parameters
def calc_orientation (dictionary):
    # import required libraries
    import math
    ##### calculate orientation angle from coordinate offset
    dx = float(dictionary['target_DEMCRS_E']) -  float(dictionary['camera_DEMCRS_E'])
    dy = float(dictionary['target_DEMCRS_N']) -  float(dictionary['camera_DEMCRS_N'])
    if (dy>0):
        if(dx>0):
            return math.degrees(math.atan(float(dx)/float(dy)))
        else:
            return math.degrees(math.atan(float(dx)/float(dy))) + 360
    if (dy<0):
            return (math.degrees(math.atan(float(dx)/float(dy))) + 180)
    if (dy==0):
        if(dx>0):
            return 90
        else:
            return 270
#############################################################################################################
  
    
    
############### calculate other vertical orientation parameters from given input ############################
# input:
#       - dictionary: dictionary containing all projection parameters
#       - offset: boolean; if False, all other parameters are calculated from target offset above ground
#       - z: boolean; if False, all other parameters are calculated from absolute target height
#       - pitch: boolean; if False, all other parameters are calculated from pitch angle
#       - height_diff: boolean; if False, all other parameters are calculated from height difference between target and camera
def calc_vertical_params(dictionary, offset=True, z=True, pitch = True, height_diff=True):
    # import required libraries
    import math
    
    ##### get DEM height at target point
    dem_height = get_height(dictionary, name='target')
    dictionary['var_add']['target_DEM_height'] = dem_height
    
    ##### calculate remaining parameters
    if (pitch==False) and height_diff:
        # derive height difference from pitch angle
        dictionary['var_add']['height_diff_target_cam'] = float(dictionary['var_add']['distance'])*math.tan(math.radians(float(dictionary['var_add']['pitch_angle_deg'])))
        height_diff=False
    if(z):
        if(height_diff):
            # derive absolute target height and height difference from target offset
            dictionary['var_add']['target_DEMCRS_Z'] = dem_height + float(dictionary['target_offset'])
            dictionary['var_add']['height_diff_target_cam'] = float(dictionary['var_add']['target_DEMCRS_Z']) - float(dictionary['var_add']['camera_DEMCRS_Z'])
        elif(offset):
            # derive absolute target height and target offset from height difference
            dictionary['var_add']['target_DEMCRS_Z'] = float(dictionary['var_add']['camera_DEMCRS_Z']) + float(dictionary['var_add']['height_diff_target_cam'])
            dictionary['target_offset'] = dictionary['var_add']['target_DEMCRS_Z'] - dem_height
    else:
        # derive height difference and target offset from absolute target height
        dictionary['var_add']['height_diff_target_cam'] = float(dictionary['var_add']['target_DEMCRS_Z']) - float(dictionary['var_add']['camera_DEMCRS_Z'])
        dictionary['target_offset'] = float(dictionary['var_add']['target_DEMCRS_Z']) - dem_height
    if pitch:
        # derive pitch angle from height difference
        dictionary['var_add']['pitch_angle_deg'] = math.degrees(math.atan(float(dictionary['var_add']['height_diff_target_cam'])/float(dictionary['var_add']['distance'])))
    
    # return new dictionary to main procedure
    return dictionary
#############################################################################################################



############### define vertical orientation #################################################################
# input:
#       - dictionary: dictionary containing all projection parameters
#       - bool_target: boolean; if True, target point approach is used
#               then an additional option exists: the camera offset can be reused as target offset
def define_vertical_orientation(dictionary, bool_target):
    # import required submodules of georef_webcam
    import modules.aux_functions as aux_func
    
    ##### create options, how to generate pitch angle, transverse looking angle
    choices_list = []
    if (bool_target):
        dictionary['target_offset'] = dictionary['camera_offset']
        choices_list.extend(['reuse or adjust camera offset above ground for target'])
    choices_list.extend(['use horizontal pitch angle (pitch = 0°)', 'insert another pitch angle', 
                         'insert height difference between target and camera', 'use target offset above ground',
                         'use absolute target height'])
    
    ##### select choice
    print("Please define yaw/transverse looking angle...")
    print("This angle defines, whether the camera is looking horizontally, upwards or downwards.")
    print("Several options to calculate yaw exist:")
    choice = aux_func.select_choices(choices_list)[0]
    
    ##### execute choice
    if(choice == 'reuse or adjust camera offset above ground for target'):
        dictionary = add2dict(dictionary, ['target_offset'], overwrite=True)
        dictionary = calc_vertical_params(dictionary, offset = False)
    elif(choice == 'use horizontal pitch angle (pitch = 0°)'): 
        dictionary['var_add']['pitch_angle_deg'] =  0
        dictionary = calc_vertical_params(dictionary, pitch = False)
    elif(choice == 'insert another pitch angle'):
        dictionary['var_add']['pitch_angle_deg'] = input("Please insert pitch angle [°]: \n")
        dictionary = calc_vertical_params(dictionary, pitch = False)
    elif(choice == 'insert height difference between target and camera'):
        print("distance from camera to target is: "+ str(dictionary['var_add']['distance']))
        dictionary['var_add']['height_diff_target_cam'] = input("Please insert the height difference between target and camera in m: \n")
        dictionary = calc_vertical_params(dictionary, height_diff = False)
    elif(choice == 'use target offset above ground'):
        calc_height_or_offset(dictionary, name = 'target', offset_or_height = 1)
        dictionary = calc_vertical_params(dictionary, offset = False)
    elif(choice == 'use absolute target height'):
        calc_height_or_offset(dictionary, name = 'target', offset_or_height = 2)
        dictionary = calc_vertical_params(dictionary, offset = False)
    
    # return new dictionary to main procedure
    return dictionary
#############################################################################################################



############### edit vertical orientation ###################################################################
# input:
#       - dictionary: dictionary containing all projection parameters
def change_vertical_orientation(dictionary):
    # import required submodules of georef_webcam
    import modules.aux_functions as aux_func
    
    ##### create and select options, how to edit the vertical looking direction
    choices_list = ['keep current pitch angle', 'edit pitch angle', 'change height difference between target and camera',
                    'edit absolute target height', 'edit target offset above ground']
    choice = aux_func.select_choices(choices_list)[0]
    
    ##### execute choice
    if(choice == 'keep current pitch angle'): 
        dictionary = calc_vertical_params(dictionary, pitch = False)
    elif(choice == 'edit pitch angle'):
        dictionary['var_add'] = add2dict(dictionary['var_add'], ['pitch_angle_deg'], overwrite = True)
        dictionary = calc_vertical_params(dictionary, pitch = False)
    elif(choice == 'change height difference between target and camera'):
        dictionary['var_add'] = add2dict(dictionary['var_add'], ['height_diff_target_cam'], overwrite=True)        
        dictionary = calc_vertical_params(dictionary, height_diff = False)
    elif(choice == 'edit absolute target height'):
        dictionary['var_add'] = add2dict(dictionary['var_add'], ['target_DEMCRS_Z'], overwrite=True)        
        dictionary = calc_vertical_params(dictionary, z = False)
    elif(choice == 'edit target offset above ground'):
        dictionary = calc_vertical_params(dictionary, pitch = False)
        dictionary = add2dict(dictionary, ['target_offset'], overwrite=True)        
        dictionary = calc_vertical_params(dictionary, offset = False)

    # return new dictionary to main procedure
    return dictionary
#############################################################################################################



############### set boundaries for GCP optimisation #########################################################
# input:
#       - opt_dictionary: dictionary containing all optimization boundaries; 
#               if opt_dictionary == None:  a new dictionary with default values is generated
def set_optimisation_boundaries(opt_dictionary=None):
    # import required libraries
    import collections
    
    ##### define optimization variables and default values
    bound_params = ['cam_east', 'cam_north', 'cam_height', 'roll_angle', 'target_east', 'target_north', 'target_height', 'focalLen_meter', 'sensor_height_meter','sensor_width_meter']
    bound_values = [50, 50, 50, 3, 100, 100, 100, 0.00010, 0, 0]
        
    ##### create new dictionary or edit existing values
    if opt_dictionary == None:
        opt_dictionary = collections.OrderedDict()
        opt_dictionary = add2dict(opt_dictionary, bound_params, values = bound_values)
    else:
        opt_dictionary = add2dict(opt_dictionary, bound_params, overwrite = True)
    #return dictionary with new or edited optimization boundaries to main procedure
    return opt_dictionary
#############################################################################################################
    

    
############### calculate distance between camera & target ##################################################
# input:
#       - dictionary: dictionary containing all projection parameters (target and camera location)
def get_distance_tc(dictionary):
    # import required libraries
    import math
    # calculate distance
    distance = math.sqrt((dictionary['target_DEMCRS_E']-dictionary['camera_DEMCRS_E'])**2+
                         (dictionary['target_DEMCRS_N']-dictionary['camera_DEMCRS_N'])**2)
    # return distance value to main procedure
    return distance
#############################################################################################################
