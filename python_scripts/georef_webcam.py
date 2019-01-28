#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
#############################################################################################################
Buchelt, S. (2018)
georef_webcam - Python package to georeference webcam images (Version 0.0.1)

    incorporating:
	Härer, S., Bernhardt, M., and Schulz, K.: PRACTISE: PRACTISE V.2.1. Zenodo, doi:10.5281/zenodo.35646, 2015.
	
Author: 	Sebastian Buchelt
Institution: 	University of Wuerzburg - Dept. of Remote Sensing
Contact: 	https://github.com/SebBuchelt

Last edited on Thu Dec 20 2018

#############################################################################################################

"""

# load libraries
import sys, os, time
import argparse
import numpy as np
import scipy as sp
import math
from scipy.interpolate import griddata
import scipy.misc
import urllib
import json
from osgeo import ogr
from osgeo import osr
import gdal
from osgeo.gdalconst import *
import collections
import struct
import shutil
import subprocess
import tempfile
import git


########################################### parser input ####################################################
# create parser with needed and optional input variables
parser = argparse.ArgumentParser(description='Script to georeference webcam images')
parser.add_argument(dest='out_dir', type=str, help='output directory')
parser.add_argument("-dem","--dem_subfolder", help="add, if you want to specify dem subfolder (default: 'dem')")
args = parser.parse_args()


######################################## define needed functions ############################################

##### create Yes/No - Questionaire and return True/False as output
def check_input(question):
    parameter = raw_input(question)
    if(parameter=='y'):
        parameter=True
        print 'Yes'
    else: 
        parameter=False
        print 'No'
    return parameter


##### print dictionary as table
def print_dict(dictionary):
    print ('\ncurrent used input parameters:')
    for i in dictionary:
        print (str(i) + ': '+ str(dictionary[i]))
        
        
##### add coordinates of a point with its CRS to a dictionary
def define_point(dictionary, name):
    print('\n \ndefine ' + name + ' point coordinates...')
    if(name=='target'):
        manual_input = check_input("Do you want to insert target point coordinates manually? \n(if not, it will be calculated from camera position & direction angle... \ny/n \n")
    else:
        manual_input = True
    if(manual_input):
        lat_lon = check_input("Are the coordinates in lat-lon? y/n \n")
        if(lat_lon):
            epsg_val = 4326
            for k in (name + '_lat', name + '_lon'):
                dictionary[k]=None
            dictionary = edit_dict(dictionary)
        else:
            epsg_val = raw_input('Please insert EPSG-Nr. of CRS (if empty: CRS of input DEM): \n')
            print('Please write the ' + name + ' Position in UTM coordinates:')
            for k in (name + '_UTM_E', name + '_UTM_N'):
                dictionary[k]=None
            dictionary = edit_dict(dictionary)
        print_dict(dictionary)
    else:
        if not('direction_deg' in dictionary):
            dictionary['direction_deg'] = raw_input('Please enter looking direction of camera: \n')
            print_dict(dictionary)
        epsg_val = -1
    return (dictionary, epsg_val)
    

##### edit/change/overwrite values in an existing dictionary
def edit_dict(dictionary,overwrite=False, params=[False]):
    if (overwrite):
        print ("Overwriting mode: If you want to keep old value, leave input empty")
    for i in dictionary:
        if (i in params) or not (params[0]):
            if (overwrite):
                new_value = raw_input("Write value for parameter "+str(i)+" (old value: " + str(dictionary[i]) + "):  \n")
                if not(new_value==""):
                    dictionary[i] = new_value
            while (dictionary[i]==None) or (dictionary[i]==""):
                new_value = raw_input("Write value for parameter "+str(i)+":  \n")
                dictionary[i] = new_value
    print_dict(dictionary)
    return dictionary


##### transform point coordinates to a CRS of a raster file
def transform_point_raster_CRS(raster_dir, x_coord, y_coord, epsg_point):
    DemDs = gdal.Open(raster_dir, GA_ReadOnly)
    pj=DemDs.GetProjection()
    target = osr.SpatialReference()
    target.ImportFromWkt(pj)

    source = osr.SpatialReference()
    source.ImportFromEPSG(int(epsg_point))

    transform = osr.CoordinateTransformation(source, target)

    point = ogr.CreateGeometryFromWkt("POINT ("+str(x_coord)+" "+str(y_coord)+")")
    point.Transform(transform)
    return (point.GetX(), point.GetY())


##### transform target & camera position to DEM CRS
def transform_2dem_crs(dem_path,dictionary, epsg_val, name):
    if not (epsg_val == ''):
        if (int(epsg_val) == 4326):
            x_coord = dictionary[name+'_lon']
            y_coord = dictionary[name+'_lat']
        else:
            x_coord = dictionary[name+'_UTM_E']
            y_coord = dictionary[name+'_UTM_N']
            
        if not os.path.exists(dem_path):
            print("\nDEM data couldn't be found! \nPlease put DEM data in following folder:")
            print(dem_path)
            time.sleep(10)
            dem_data = check_input("Is the data there now? y/n \n")
            if not (dem_data):
                print('No DEM available. End programm')
                sys.exit()

        (UTM_E, UTM_N)=transform_point_raster_CRS(dem_path, x_coord, y_coord, epsg_val)
        dictionary[name+'_UTM_E_final'] = UTM_E
        dictionary[name+'_UTM_N_final'] = UTM_N
    else:
        dictionary[name+'_UTM_E_final'] = dictionary.pop(name+'_UTM_E')
        dictionary[name+'_UTM_N_final'] = dictionary.pop(name+'_UTM_N')
    return dictionary


##### calculate the coordinate position of camera target from direction angle
def calc_target_from_lookdir(dictionary):
    print('\ncalculate target point by using direction angle...')
    direction = float(dictionary['direction_deg'])
    if(0<=direction<45) or (315<=direction<=360):
        dy=1000
        dx=dy*math.tan(math.radians(direction))
    elif(45<=direction<135):
        dx=1000
        dy=-dx*math.tan(math.radians(direction-90))
    elif(135<=direction<225):
        dy=-1000
        dx=dy*math.tan(math.radians(direction-180))
    elif(225<=direction<315):
        dx=-1000
        dy=-dx*math.tan(math.radians(direction-270))
    else:
        print('Error: direction angle not within possible range (0, 360)')
        sys.exit()
    
    dictionary['target_UTM_E_final'] = dictionary['camera_UTM_E_final']+dx
    dictionary['target_UTM_N_final'] = dictionary['camera_UTM_N_final']+dy
    return dictionary
    

##### extract raster value at certain location & add it to dictionary
def get_height(dem,dictionary, name):
    if not os.path.exists(dem):
            print("\nDEM data couldn't be found! \nPlease put DEM data in following folder:")
            print(dem)
            time.sleep(10)
            dem_data = check_input("Is the data there now? y/n \n")
            if not (dem_data):
                print('No DEM available. End programm')
                sys.exit()
    DemDs = gdal.Open(dem, GA_ReadOnly)
    # get Projection & raster data
    gt=DemDs.GetGeoTransform()
    dem_band=DemDs.GetRasterBand(1)
    mx = dictionary[name+'_UTM_E_final']
    my = dictionary[name+'_UTM_N_final']
    px = int((mx - gt[0]) / gt[1]) #x pixel position in raster
    py = int((my - gt[3]) / gt[5]) #y pixel position in raster
    height = dem_band.ReadRaster(px,py,1,1,buf_type=gdal.GDT_UInt16) #Assumes 16 bit int aka 'short'
    height = struct.unpack('h' , height) #use the 'short' format code (2 bytes) not int (4 bytes)
    dictionary[name+'_height'] = height[0]
    return dictionary


##### calculate distance between camera & target
def get_distance_tc(dictionary):
    distance = math.sqrt((dictionary['target_UTM_E_final']-dictionary['camera_UTM_E_final'])**2+(dictionary['target_UTM_N_final']-dictionary['camera_UTM_N_final'])**2)
    return distance


##### edit line in octave input file for PRACTISE
def edit_octave_file(octave_txt, line, input_value):
    param = octave_txt[line].split('=')[0]    
    comment = octave_txt[line].split(';')[1]    
    new_line = '='.join([param,input_value])
    new_line = ';'.join([new_line, comment])
    octave_txt[line] = new_line
    return octave_txt


##### change directory description to octave readable
def dir_for_octave(directory_name):
    return '\\'.join(directory_name.split('/'))


##### print output messages of subprocess while running
def print_subprocess_messages(process):
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print output.strip()


##### calculate the minimum value within a moving window
def mw_min_numba(edge_arr, out_arr,x_win,y_win):
    xn,yn = edge_arr.shape
    for x in range(xn):
        xmin = max(0,x - x_win)
        xmax = min(xn, x + x_win + 1)
        for y in range(yn):
            ymin = max(0,y - y_win)
            ymax = min(yn, y + y_win + 1)

            out_arr[x,y] = edge_arr[xmin:xmax, ymin:ymax].min()
    return out_arr

##### calculate the maximum value within a moving window
def mw_max_numba(edge_arr, out_arr,x_win,y_win):
    xn,yn = edge_arr.shape
    for x in range(xn):
        xmin = max(0,x - x_win)
        xmax = min(xn, x + x_win + 1)
        for y in range(yn):
            ymin = max(0,y - y_win)
            ymax = min(yn, y + y_win + 1)

            out_arr[x,y] = edge_arr[xmin:xmax, ymin:ymax].max()
    return out_arr


##### calculate max-min difference within moving window (edge detection)
def mw_diff_numba(in_arr, out_arr,x_win,y_win):
    xn,yn = in_arr.shape
    for x in range(xn):
        xmin = max(0,x - x_win)
        xmax = min(xn, x + x_win + 1)
        for y in range(yn):
            ymin = max(0,y - y_win)
            ymax = min(yn, y + y_win + 1)

            out_arr[x,y] = in_arr[xmin:xmax, ymin:ymax].max() - in_arr[xmin:xmax, ymin:ymax].min()
    return out_arr


##### (calculate relative edges, by normalizing edges)
def mw_edge2(edge_arr, dist_arr, out_arr,x_win,y_win):
    xn,yn = edge_arr.shape
    for x in range(xn):
        xmin = max(0,x - x_win)
        xmax = min(xn, x + x_win + 1)
        for y in range(yn):
            ymin = max(0,y - y_win)
            ymax = min(yn, y + y_win + 1)

            out_arr[x,y] = edge_arr[x, y]/dist_arr[xmin:xmax, ymin:ymax].min()
    return out_arr


##### calculate the difference of an value from the average of a mooving window
def mw_diff_from_mean(edge_arr, out_arr,x_win,y_win):
    xn,yn = edge_arr.shape
    for x in range(xn):
        xmin = max(0,x - x_win)
        xmax = min(xn, x + x_win + 1)
        for y in range(yn):
            ymin = max(0,y - y_win)
            ymax = min(yn, y + y_win + 1)

            out_arr[x,y] = edge_arr[x, y]- edge_arr[xmin:xmax, ymin:ymax].mean()
    return out_arr


##### write output as geotiff file
def write_array_as_geotiff(array, folder, filename, codage=GDT_Float32):
    driver = gdal.GetDriverByName('GTiff')
    driver.Register()
    (rows, cols)=array.shape
    outDs = driver.Create(os.path.join(folder,filename), cols, rows, 1, codage)
    
    outBand = outDs.GetRasterBand(1)
    outBand.WriteArray(array)
    outBand.FlushCache()
    outBand = None
    
    outDs = None
    
    
########################################## main input variables #############################################
##### create & check directories:
project_data_dir = args.out_dir
if (args.dem_subfolder == None):
    dem_dir = os.path.join(project_data_dir, 'dem')
else: 
    dem_dir = os.path.join(project_data_dir, args.dem_subfolder)

code_dir = os.getcwd()
code_dir = code_dir.split('georef_webcam')
code_dir = code_dir[0]+'georef_webcam'
if not os.path.exists(code_dir):
    code_dir = raw_input('Directory to codes does not exist, please enter new directory: \n')
if not os.path.exists(code_dir):
    print('Code directory still does not exist. End programm')
    sys.exit()
octave_dir = os.path.join(code_dir, 'PRACTISE_v2_1')
if not os.path.exists(project_data_dir):
    os.makedirs(project_data_dir)
if not os.path.exists(dem_dir):
    os.makedirs(dem_dir)
dem_list = os.listdir(dem_dir)
if (len(dem_list)==0):
    print("\nDEM data is not available! \nPlease put DEM data in following folder:")
    print(dem_dir)
    time.sleep(10)
    dem_data = check_input("Is the data there now? y/n \n")
    if not (dem_data):
        print('No DEM available. End programm')
        sys.exit()
        
dem_list = os.listdir(dem_dir)
dem_ending = raw_input("Which file ending does the dem raster have? (asc or tif) \n")
dem_file =  [f for f in dem_list if (f.endswith('.'+dem_ending))]
dem_file = os.path.join(dem_dir,dem_file[0])

##### if tif, create ascii-file for octave (to be done)
if (dem_ending == 'tif'):
	dem_file_new = dem_file[0:-3]+'asc'
	subprocess.call(['gdal_translate', '-of', 'AAIGrid', dem_file, dem_file_new])
	dem_file = dem_file_new
    

    
##### Copy PRACTISE software into code subfolder
if not os.path.exists(octave_dir):
    print ('\nDownload PRACTISE package from git... ')
    t = tempfile.mkdtemp()
    git.Repo.clone_from('https://github.com/shaerer/PRACTISE.git', t, branch='master', depth=1)
    shutil.move(os.path.join(t, 'PRACTISE_v2_1'), code_dir)
    shutil.rmtree(t)
    print ('Download finished')



##### create variable names for dictionaries
var_fotoweb = ['name', 'id', 'latitude', 'longitude', 'elevation', 'direction', 'focalLen']
var_new = ['webcam_name', 'folder_name', 'camera_lat', 'camera_lon', 'elevation_cam_m', 'direction_deg', 'focalLen_mm']
var_wo = ['webcam_name', 'folder_name', 'focalLen_mm']
var_mand = ['camera_UTM_E_final', 'camera_UTM_N_final', 'target_UTM_E_final', 'target_UTM_N_final', 'camera_offset_DEM', 'target_offset_DEM', 'focalLen_mm', 'sensor_width_mm', 'sensor_height_mm']
var_opt = ['buffer', 'roll_angle']
var_bound = ['cam_east', 'cam_north', 'cam_height', 'roll_angle', 'target_east', 'target_north', 'target_height', 'focalLen_meter', 'sensor_height_meter','sensor_width_meter']
default_opt =[100, 0]






#############################################################################################################
############################################ start procedure ################################################
#############################################################################################################

#############################################################################################################
#---------------------------------------- 1. get input variables --------------------------------------------
#############################################################################################################


############################# check for metadata availability from foto-webcam.eu ###########################
foto_webcam = check_input("Is the webcam you want to georeference from foto-webcam.eu? y/n \n")

if(foto_webcam):
    metadata = check_input("Do you want to read the metadata for your station from foto-webcam.eu y/n \n")
    if(metadata):
        json_file = os.path.join(project_data_dir,"metadata_camera.txt")
        
        ##### download metadata, if it is not downloaded so far
        if not (os.path.exists(json_file)):
            print 'File has to be downloaded'
            link = 'https://www.foto-webcam.eu/webcam/include/metadata.php'
            f = urllib.urlopen(link)
            data = json.load(f)
            with open(json_file, 'w') as outfile:
                json.dump(data, outfile)
            data = None
            if not (os.path.exists(json_file)):
                print 'download failed - no access to metadata'
                sys.exit(1)
            else: 
                print 'metadata successfully downloaded'
        else: 
            print 'Metadata already downloaded'
        
        ##### get camera station names to find it in the list
        with open(json_file, 'r') as f:
            data_webcam = json.load(f)
        data_webcam = data_webcam['cams']
        names_list=list()
        for cam in data_webcam:
            names_list.append(cam['name'])
        
        ##### find camera station in list by giving name as input
        numb=0
        name_webcam=None
        while (numb<3):
            name_webcam = raw_input("Please give the name of the Webcam: \n")
            if (name_webcam in names_list):
                print('Found station: '+ name_webcam)
                break
            numb += 1
            print ('Wrong name. ' + str(3-numb) + ' tries left')
            if (numb==3):
                print('Maximum number of tries reached. End program')
                sys.exit()
        
        ##### load available metadata and copy parameters, that are of interest
        ind = names_list.index(name_webcam)
        data_station = data_webcam[ind] 
        data_used = collections.OrderedDict((k, data_station[k]) for k in var_fotoweb)
        for k in range(len(var_fotoweb)):
            data_used[var_new[k]] = data_used.pop(var_fotoweb[k])
        epsg_cam = 4326 # defines EPSG of camera location coordinates (needed later for transformation to DEM CRS)
            
        ##### show acquired metadata
        print('Parameters found: ')
        print_dict(data_used)
        
        ##### correct metadata values, if wanted
        correct_metadata = check_input("Do you want to correct the existing metadata? y/n \n")
        if(correct_metadata):
            data_used = edit_dict(data_used, overwrite=True)
            
            
################## if metadata from foto-webcam.eu is not wanted or not available: ##########################
############################### manual input of mandatory parameters ########################################
    else:
        print('Needed Parameters have to be inserted manually')
        data_used = collections.OrderedDict((k, None) for k in var_wo) 
        data_used = edit_dict(data_used)
        (data_used, epsg_cam)= define_point(data_used, 'camera')       
else:
    print('Needed Parameters have to be inserted manually')
    data_used = collections.OrderedDict((k, None) for k in var_wo)  
    data_used = edit_dict(data_used)
    (data_used, epsg_cam)= define_point(data_used, 'camera')


############################# add & calculate all additionally needed parameters ############################
    
##### add sensor size parameters manually (not available)
print('\n\nSensor size parameters are not available...')
print('keep default or look up camera type and then search online for the sensor size')
sensor_parameters = ['sensor_width_mm', 'sensor_height_mm']
sensor_default = [22.3, 14.9]
for k in range(len(sensor_parameters)):
    data_used[sensor_parameters[k]] = sensor_default[k]
data_used = edit_dict(data_used, overwrite=True, params=sensor_parameters)
    

##### if not available so far, add location of target in CRS of choice or looking direction instead of target coordinates
(data_used, epsg_tar)= define_point(data_used, 'target')

    
##### transform coordinates of camera (& target) location into CRS of DEM
print('\ntransform all coordinates into same CRS (CRS of DEM)...')

data_used = transform_2dem_crs(dem_file,data_used, epsg_cam, 'camera')
if not (epsg_tar==-1):
    data_used = transform_2dem_crs(dem_file,data_used, epsg_tar, 'target')
else:
    ##### if target point is wanted to be calculated by using the looking direction, do it here
    data_used = calc_target_from_lookdir(data_used)
    
    
##### get DEM height of camera & target position  
print('\nget camera & target height from DEM...')
data_used = get_height(dem_file, data_used, 'camera')
data_used = get_height(dem_file, data_used, 'target')
print_dict(data_used)


##### define height of camera above ground
print('\n \ndefine camera offset (default: 0) ...')
data_used['camera_offset_DEM'] = raw_input('Please insert camera height above ground: \n')
if (data_used['camera_offset_DEM']==''):
    data_used['camera_offset_DEM']=0
    
    
##### define vertical looking direction by giving a pitch angle or a vertical offset of target to camera    
print('\ndefine vertical looking direction (default: 0) ...')
vertical = check_input("Do you want to keep the horizontal looking direction? y/n \n")
data_used['height_diff_target'] = 0
data_used['pitch_angle'] = 0
if not(vertical):
    distance = int(get_distance_tc(data_used))
    pitch = check_input("Do you want to insert a pitch angle? y/n \n")
    if (pitch):
        data_used['pitch_angle'] = float(raw_input('Please insert pitch angle in degree (+ upwards/ - downwards): \n'))
        data_used['height_diff_target'] = distance*math.tan(math.radians(data_used['pitch_angle']))
    else:
        data_used['height_diff_target'] = float(raw_input('Please insert a height offset for your target \n(difference to camera height - target is '+ str(distance) + 'm away): \n'))
        data_used['pitch_angle'] = math.degrees(math.atan(data_used['height_diff_target']/distance))
data_used['target_offset_DEM'] = float(data_used['camera_height']) +float(data_used['camera_offset_DEM']) + float(data_used['height_diff_target']) - float(data_used['target_height'])



############################################## final adjustments ############################################
##### check given input variables and optionally change them (attention! no recalculation of calculated parameters)
print('Please check input variables:')
print_dict(data_used)
correct_metadata = check_input("Do you want to change the acquired values? y/n \n")
if(correct_metadata):
    data_used = edit_dict(data_used, overwrite=True)

##### check, if all obligatory parameters are given
print('\nCheck, if all mandatory input variables are existing...')
test=0
for k in var_mand:
    if not(k in data_used):
        test =+1
        data_used[k] = raw_input('Mandatory parameter ' + str(k) +' is missing. Please enter value: \n')
if(test==0):
    print ('All mandatory parameters exist')
test=None
    
##### if wanted, optional parameters can be added
add_metadata = check_input('\nDo you want to add additional parameters? y/n \nOptional parameters: \n  -' + '\n  -'.join(var_opt) + '\n')
if(add_metadata):
    for k in range(len(var_opt)):
        data_used[var_opt[k]]=default_opt[k]
    data_used = edit_dict(data_used, overwrite=True, params=var_opt)
    print_dict(data_used)
    
print('\n \nAcquiring input variables has been finished. Start passing variables to PRACTISE ...\n')
#############################################################################################################
#---------------------------------- 1. getting input variables finished -------------------------------------
#############################################################################################################




    
#############################################################################################################
#-------------------- 2. write parameters into octave file and run projection procedure ---------------------
#############################################################################################################

##### create webcam processing directories
webcam_path = os.path.join(project_data_dir,data_used['folder_name'])
image_path = os.path.join(webcam_path, 'image')
PRACTISE_Path = os.path.join(webcam_path, 'PRACTISE')
if not os.path.exists(image_path):
    os.makedirs(image_path)
    
##### ask for webcam image
print('Please add webcam image to the following folder:\n'+ image_path)
time.sleep(10)
image_data = check_input("Is the image there now? y/n \n")
if not (image_data):
    print('No image available. End programm')
    sys.exit()

# get file ending of image file
file_ending = raw_input("Which file ending does the image have? (please write without .  - default: jpg) \n")  
if (file_ending==''):
        file_ending = 'jpg'  

##### read octave PRACTISE_input file 
with open(os.path.join(code_dir,'Auxiliary_data','PRACTISE_Input_base.m'), 'r') as octave_file:
    PRACTISE_input = octave_file.readlines()

# help variables    
rerun=True
run_var=1
p_img=list()

##################################### edit parameters in input file ########################################
while (True):    
    # change camera position
    value = "["+str(data_used['camera_UTM_E_final'])+","+str(data_used['camera_UTM_N_final'])+"]"
    PRACTISE_input = edit_octave_file(PRACTISE_input, 21, value)
    
    # change target position
    value = "["+str(data_used['target_UTM_E_final'])+","+str(data_used['target_UTM_N_final'])+"]"
    PRACTISE_input = edit_octave_file(PRACTISE_input, 25, value)
    
    # change offset values position
    value = "["+str(data_used['camera_offset_DEM'])+","+str(data_used['target_offset_DEM'])+"]"
    PRACTISE_input = edit_octave_file(PRACTISE_input, 26, value)
    
    # change focal length, sensor height & width
    value = str(float(data_used['focalLen_mm'])/1000)
    PRACTISE_input = edit_octave_file(PRACTISE_input, 28, value)
    value = str(float(data_used['sensor_height_mm'])/1000)
    PRACTISE_input = edit_octave_file(PRACTISE_input, 29, value)
    value = str(float(data_used['sensor_width_mm'])/1000)
    PRACTISE_input = edit_octave_file(PRACTISE_input, 30, value)
    
    # change buffer & roll angle
    if('buffer' in data_used):
        value = str(data_used['buffer'])
        PRACTISE_input = edit_octave_file(PRACTISE_input, 23, value)
    if('roll_angle' in data_used):
        value = str(data_used['roll_angle'])
        PRACTISE_input = edit_octave_file(PRACTISE_input, 27, value)
    
    # change directories
    PRACTISE_input = edit_octave_file(PRACTISE_input, 7, "'"+dir_for_octave(dem_file)+"'")           # directory to dem file
    PRACTISE_input = edit_octave_file(PRACTISE_input, 8, "'"+dir_for_octave(PRACTISE_Path)+"\\'")   # directory to PRACTISE input & output
    PRACTISE_input = edit_octave_file(PRACTISE_input, 9, "'run"+ str(run_var) +"\\'")               # directory with input of run X
    
    # create input path for PRACTISE run
    run_path = os.path.join(PRACTISE_Path, 'run'+ str(run_var) +'')
    if not os.path.exists(run_path):
        os.makedirs(run_path)
        
    if (run_var==1):
    # define imagefile ending
        PRACTISE_input = edit_octave_file(PRACTISE_input, 11, "'."+file_ending+"'")
    # define number of run
        run_name = 'First'
    elif (run_var==2):
        run_name = 'Second'
    else:
        run_name = str(run_var)+'.'
        
    ##### check existance of webcam image
    image_name = [f for f in os.listdir(image_path) if (f.endswith(file_ending))]
    if (image_name[0]==''):
        print ('Webcam image could not be found. End programm')
        sys.exit()
    shutil.copy2(os.path.join(image_path, image_name[0]), run_path)     # copy file to PRACTISE run input folder
    
    
########################### write edited parameters in new PRACTISE_input file ##############################
    ##### create input file
    with open(os.path.join(PRACTISE_Path,'run'+ str(run_var) +'.m'), 'w') as octave_file:
        for line in PRACTISE_input:
            octave_file.write(line) 
            
    ##### write directory to input file in file, which calls input file
    with open(os.path.join(octave_dir,'Input_PRACTISE.m'), 'r') as octave_file:
        PRACTISE_input_main = octave_file.readlines()
    PRACTISE_input_main = edit_octave_file(PRACTISE_input_main, 19, "'"+dir_for_octave(run_path)+"'")
    with open(os.path.join(octave_dir,'Input_PRACTISE.m'), 'w') as octave_file:
        for line in PRACTISE_input_main:
            octave_file.write(line) 
    
########################## start first run of PRACTISE projection without GCP correction ####################
    python_wd = os.getcwd()     # save current directory
    os.chdir(octave_dir)        # set wd to directory of PRACTISE scripts
    
    
    ##### call PRACTISE script as subprocess and print its messages to console
    print('\nstart ' + run_name +' run of PRACTISE...')
    print('this may take up to 15-30 minutes, depending on the size of the DEM file and the complexity of the projection procedure')
    process1 = subprocess.Popen(['octave','PRACTISE.m'],stdout=subprocess.PIPE)
    print_subprocess_messages(process1)
    
    # first run is finished, reset wd
    print('\n'+str(run_name) + ' run of PRACTISE is finished')
    os.chdir(python_wd)
    
#############################################################################################################
#------------------------- 2. finished running PRACTISE projection procedure --------------------------------
#############################################################################################################
    
    
    
    
    
#############################################################################################################
#------------------- 3. if wanted, change first input parameters and rerun PRACTISE -------------------------
#############################################################################################################
    
    # some information to the user
    print('\nPlease check accuracy of first alignment in classification image')
    print('you can adjust the input parameters and try to improve the georectification')
    print('for this it is recommended to only change the parameters of the target location')
    print('Please consider, that there will also be further improvement steps including Ground Control Points & polynomial fitting')
    print('So the alignment should be roughly accurate (+- 50 pixel)')
    time.sleep(10)
    
#################### show projection result from PRACTISE and decide to rerun or not ########################
    ##### get folder with PRACTISE output (projected DEM pixels classified) 
    folder_result = [f for f in os.listdir(PRACTISE_Path) if 'run'+ str(run_var) +'_' in f]
    folder_result = os.path.join(PRACTISE_Path,folder_result[0])
    results = os.listdir(folder_result)
    check_image = [f for f in results if (f.endswith('_auto.ofig'))]
    check_image = os.path.join(folder_result,check_image[0])
    
    ##### create Octave file to read and open projection result
    with open(os.path.join(folder_result,'run_image.m'), 'w') as octave_file:
        octave_file.write('hgload("'+check_image+'")\n') 
        octave_file.write('waitforbuttonpress()')
    p_img.append(subprocess.Popen(["octave",os.path.join(folder_result,'run_image.m')],stdout=subprocess.PIPE))
    
    # decide, if you rerun or not
    rerun = check_input('\nDo you want to change the input parameters and run the first execution again? y/n \n')
    if not (rerun):
        break
    
################################# change input parameters, if rerun #########################################
    else:
        # help variables
        run_var +=1
        target_parameters = ['direction_deg', 'height_diff_target']
        
        # decide, if only parameters of target point should be changed or all
        target_param = check_input('Do you want to change as recommended only the target parameters (y) or all parameters(n)? \n')
        
        # change target parameters
        if (target_param):
            data_used = edit_dict(data_used,overwrite=True, params=target_parameters)
            
        # change all parameters
        else:
            data_used = edit_dict(data_used,overwrite=True, params=var_mand + var_opt + target_parameters)
        
        # adjust parameters, which are calculated from others
        data_used = calc_target_from_lookdir(data_used)
        data_used['target_offset_DEM'] = float(data_used['camera_height']) +float(data_used['camera_offset_DEM']) + float(data_used['height_diff_target']) - float(data_used['target_height'])
        print_dict(data_used)

#############################################################################################################
#-- 3. change input parameters finished, if decided to rerun PRACTISE, move back to 2. to adjust input file -
#------------------ if no additional rerun is needed, move on to 4. edge delineation ------------------------
#############################################################################################################
        
        
        
        
        
#############################################################################################################
#------------------------------ 4. calculate edges in image and in viewshed ---------------------------------
#############################################################################################################

# get path to first projection with best result
run_var = raw_input("Which run of first PRACTISE projection has the best result, which you want to continue with? \n")
folder_result = [f for f in os.listdir(PRACTISE_Path) if 'run'+ str(run_var) +'_' in f]
folder_result = os.path.join(PRACTISE_Path,folder_result[0])
results = os.listdir(folder_result)

print('\n\nStart calculation of edges...\n')
print('Calculating the edges from the projection is quite demanding. This process can take 30-35 min... \n')        
startTime=time.time()

##### create directory for results in this part
result_first_run = os.path.join(webcam_path, 'results/result'+ str(run_var))
if not os.path.exists(result_first_run):
    os.makedirs(result_first_run)
    
    
################################### read output of first projection #########################################
# get & read PRACTISE output file   
print('Read PRACTISE output file...')
result_file =  [f for f in results if (f.endswith('_proj.mat'))]
result_file = os.path.join(folder_result,result_file[0])
with open(result_file, 'r') as output:
    result_output = output.readlines()
    
# get number of columns and no of rows of image
rows = int(result_output[109])
cols = int(result_output[114])

# get projected DEM points with their attributes E,N,h & position in image
east = result_output[135].split(' ')[1:]
east = [int(pt) for pt in east]
north = result_output[136].split(' ')[1:]
north = [int(pt) for pt in north]
alt = result_output[137].split(' ')[1:]
alt = [int(pt) for pt in alt]
img_col = result_output[167].split(' ')[1:]
img_col = [float(pt) for pt in img_col]
img_row = result_output[168].split(' ')[1:]
img_row = [float(pt) for pt in img_row]

# create image position as point
points = [(int(img_row[pt]), int(img_col[pt])) for pt in range(len(img_col))]

# calculate distance to camera to derive edges later
dist = [math.sqrt((float(east[pt])-data_used['camera_UTM_E_final'])**2+(float(north[pt])-data_used['camera_UTM_N_final'])**2) for pt in range(len(img_col))]


################ interpolate input parameters for each image pixel, needed for edge calculation #############
################ (parameters: distance to camera, distance to projected points, x/y/z-position) #############
print('Start interpolation of parameters ...')
# interpolation grid 
grid_x, grid_y = np.mgrid[0:rows, 0:cols]

# interpolate
dist_raster = sp.interpolate.griddata(points, np.array(dist),(grid_x, grid_y), method='nearest')
east_raster = sp.interpolate.griddata(points, np.array(east),(grid_x, grid_y), method='nearest')
north_raster = sp.interpolate.griddata(points, np.array(north),(grid_x, grid_y), method='nearest')
alt_raster = sp.interpolate.griddata(points, np.array(alt),(grid_x, grid_y), method='nearest')

# safe result as tif-file
write_array_as_geotiff(dist_raster, result_first_run, "dist_raster.tif")
write_array_as_geotiff(east_raster, result_first_run, "east_raster.tif")
write_array_as_geotiff(north_raster, result_first_run, "north_raster.tif")
write_array_as_geotiff(alt_raster, result_first_run, "alt_raster.tif")

##### calculate distance of pixel to next projected point, needed to detect skyline
#(very time consuming, maybe easier approach possible)
print('Calculate distance to projected points. Very time consuming... ')
# reference points to calculate point distance (dont use all to save time)
ref_pts = list()
for row in range(0,rows, 4):
    for col in range(0,cols, 4):
        ref_pts.append((row, col)) 
        
points_selected =list()
subset= max(len(points)/100000,1)
for x in range(0, len(points), subset):
    points_selected.append(points[x])

# calculate minimum distance to next projected point and append to one list
dist_info = list()
for i in range(len(ref_pts)/10000+1):
    dist_info.append(sp.spatial.distance.cdist(ref_pts[i*10000:min(i*10000+10000,len(ref_pts))],points_selected, 'euclidean').min(axis=1))
dist_pts_final = dist_info[0]
for array in dist_info[1:(len(ref_pts)/10000+1)]:
    dist_pts_final = np.append(np.array(dist_pts_final),np.array(array))
   
# interpolate result to raster of image size and save it as tif-file
dist_pts = np.array(dist_raster) 
dist_pts = sp.interpolate.griddata(ref_pts, dist_pts_final,(grid_x, grid_y), method='nearest')
write_array_as_geotiff(dist_pts, result_first_run, "point_distance.tif")


######################################### start edge calculation ############################################
print('Start calculation of viewshed edges ...')

# procedure to calculate skyline
edges_dist = np.array(dist_pts)
mw_diff_numba(dist_pts, edges_dist,5,5)
edges_dist2 = np.array(dist_pts)
mw_diff_numba(edges_dist, edges_dist2,5,5)
edges_dist2_adj = np.array(edges_dist2)
mw_diff_from_mean(edges_dist2, edges_dist2_adj,25,25)

# calculate absolute edges (distmax-distmin)
edges = np.array(dist_raster)
mw_diff_numba(dist_raster, edges,5,5)
# calculate relative edges ((distmax-distmin)/distmin) to find close edges
edges2 = np.array(edges)
mw_edge2(edges, dist_raster, edges2, 5,5)

# apply filters (needed to exclude areas above skyline, areas with scarce point density close to camera)
edges_dist2_adj[dist_raster<2000] = 0
edges_dist2_adj[dist_pts>20] = 0
edges_dist2_adj[edges_dist2<0] = 0
edges[dist_pts>20]=0
edges2[dist_pts>50]=0
            
##### calculate final viewshed edges by addition of several edge layers
edges_view = edges/500+edges2*3+edges_dist2_adj

##### calculate image edges
print('Start calculation of image edges ...')
im1 = scipy.misc.imread(os.path.join(image_path, image_name[0]), True)
edges_im = np.array(im1)
mw_diff_numba(im1, edges_im,5,5)

##### calculate binary layers by applying thresholds
print('Finalize edge layers...')
edges_view_bin = np.array(edges_view)
edges_view_bin[edges_view>1.5] = 1
edges_view_bin[edges_view<=1.5] = 0
edges_im_bin = np.array(edges_im)
edges_im_bin[edges_im>50] = 1
edges_im_bin[edges_im<=50] = 0

##### decrease edge thickness to get clearer outline of edges (by applying majority filter)
edges_im_bin_final = np.array(edges_im_bin)
edges_view_bin_final = np.array(edges_view_bin)
edges_im_bin_final = mw_min_numba(edges_im_bin, edges_im_bin_final,2,2)
edges_view_bin_final = mw_min_numba(edges_view_bin, edges_view_bin_final,2,2)

##### save result as tif-files
write_array_as_geotiff(edges_view_bin_final, result_first_run, "edges_view.tif")
write_array_as_geotiff(edges_im_bin_final, result_first_run, "edges_image.tif")

endTime=time.time()
print('Duration of edge calculation: ' + str(endTime-startTime))

#############################################################################################################
#----------------------------------------- 4. end edge calculation ------------------------------------------
#############################################################################################################




#############################################################################################################
#------------------- 5. derive Ground Control Points (GCPs) from edges in projected DEM and image -----------
#############################################################################################################

####################### add files to result directory, which are needed for next steps ######################
# add webcam image
shutil.copy2(os.path.join(image_path, image_name[0]), os.path.join(result_first_run, 'image.'+file_ending)) 
# add qgz-project
shutil.copy2(os.path.join(code_dir,'Auxiliary_data','test_edges.qgz'), result_first_run)                      

##### create shapefile for Ground Control Points
driver = ogr.GetDriverByName("ESRI Shapefile")
data_source = driver.CreateDataSource(os.path.join(result_first_run,"GCPs.shp"))
srs = osr.SpatialReference()
layer = data_source.CreateLayer("gcp_layer", srs, ogr.wkbPoint)
field_name = ogr.FieldDefn("name", ogr.OFTString)
field_name.SetWidth(24)
layer.CreateField(field_name)
data_source = None

gcp_p=list()
gcp_p.append(subprocess.Popen(['qgis',os.path.join(result_first_run, 'test_edges.qgz')],stdout=subprocess.PIPE, stderr=subprocess.PIPE))
edge_test = check_input("Are the edges too small? y/n \n")
if (edge_test):
    edges_view_bin_final = np.array(edges_view_bin)
    write_array_as_geotiff(edges_view_bin_final, result_first_run, "edges_view.tif")
    

#################################### draw Ground Control Points in QGIS #####################################
print('\nPlease create points for Ground Control Point Adjustment (at least 5-6)\n')
print('Please create them always paired, one at the position of an projection edge &')
print(' one at the same edge in the image')
print('Nomenclature: ')
print('     uniqueprefix_view: position of the viewshed edge (color of edge layer: red)')
print('     uniqueprefix_img: position of same edge in image (color of image edge layer: green)')
print('      e.g.: p1_view, p1_img, p2_view, p2_img,...')

time.sleep(5)
print ('If you know coordinates of specific features in the image, you can also add these points as GCPs later')

time.sleep(10)
gcp_p=list()
gcp_p.append(subprocess.Popen(['qgis',os.path.join(result_first_run, 'test_edges.qgz')],stdout=subprocess.PIPE, stderr=subprocess.PIPE))
time.sleep(10)
#############################################################################################################
#---------------------------------- 5. end Ground Control Point (GCP) extraction ----------------------------
#############################################################################################################





#############################################################################################################
#----------- 5. check & extract GCPs from shapefile & write them into txt-file demanded by PRACTISE ---------
#############################################################################################################
# ask, if GCPs 
gcps_data = check_input("Have you created some GCPs for first correction? y/n \n")
if not (gcps_data):
    print ('No Ground Control Points have been acquired. End program')
    sys.exit()

# help variables
run_var_gcp = 0
gcp_p=list()
while (True): 
    run_var_gcp +=1
            
################### check GCP shapefile and write result into gcp.txt-file for PRACTISE #####################
    # open shp file
    shapefile = os.path.join(result_first_run,"GCPs.shp")
    driver = ogr.GetDriverByName("ESRI Shapefile")
    
    # show names of all acquired GCPs
    print ('\nThese are the acquired GCPs: ')
    dataSource = driver.Open(shapefile, 0)
    layer = dataSource.GetLayer()
    for feature in layer:
        print feature.GetField("name")
    dataSource.Destroy()
      
    # give possibility to change GCP names, if they are wrong
    gcp_names = True
    while(gcp_names):
        gcp_names = check_input("Do you want to change a name in the ? y/n \n")
        if not (gcp_names):
            break
        gcp_name = raw_input('Please enter old name: \n')
        dataSource = driver.Open(shapefile, 1)
        layer = dataSource.GetLayer()
        for feature in layer:
            if(feature.GetField("name")==gcp_name):
                feature.SetField("name",raw_input('Please enter new name: \n'))
                layer.SetFeature(feature)
        dataSource.Destroy()

    # append names of final GCPs to list
    names_list=list()
    dataSource = driver.Open(shapefile, 0)
    layer = dataSource.GetLayer()
    for feature in layer:
        names_list.append(feature.GetField("name"))
    dataSource.Destroy()
    
    ##### check, if GCP occur paired (one for the viewshed edges & one for the image edges)
    #####    if not, exclude
    print("\ncreating GCP.txt file ...")
    GCP_names = [name.split('_')[0] for name in names_list]
    unique_names = set(GCP_names)
    used_GCPs = set(GCP_names)
    for x in unique_names:
        if not(GCP_names.count(x)==2):
            print (x+ ': not correct number available => will be excluded')
            used_GCPs.remove(x)
    unique_names =None
    
    # create list for GCP txt-file
    GCP_file_list = list([['POINT_X', 'POINT_Y', 'POINT_Z', 'PIXEL_COL', 'PIXEL_ROW', 'GCPname']])
    
    ##### extract needed variables (x,y,z-coords and img column & row) & append them to created list
    for x in used_GCPs:
        dataSource = driver.Open(shapefile, 0)
        layer = dataSource.GetLayer()
        for feature in layer:
            if(feature.GetField("name")==(x+'_view')):
                coords_view = feature.GetGeometryRef().GetPoint()
            if(feature.GetField("name")==(x+'_img')):
                coords_img = feature.GetGeometryRef().GetPoint()
        dataSource.Destroy()
        (col_pos, row_pos,z) = coords_view
        alt_value = alt_raster[int(-(round(row_pos))),int(round(col_pos))]
        east_value = east_raster[int(-(round(row_pos))),int(round(col_pos))]
        north_value = north_raster[int(-(round(row_pos))),int(round(col_pos))]
        (col_pos_img, row_pos_img, z) = coords_img
        GCP_file_list.append([str(east_value), str(north_value), str(alt_value), str(int(round(col_pos_img))), str(int(-(round(row_pos_img)))), x])
    
    
###################################### if wanted, add GCPs manually #########################################
    # usually remarkable features in image, whose position can be clearly identified
    print('Possibility to add GCP coordinates manually. Use it, if you have characteristic features in image, where position can be clearly identified')
    manual_GCP = check_input('Do you want to add a GCPs manually? y/n \n')
    while (manual_GCP):
        GCP_dict = collections.OrderedDict()
        GCP_name = raw_input('Please give new GCP a name: \n')
        (GCP_dict,epsg_gcp) = define_point(GCP_dict, GCP_name)
        GCP_dict = transform_2dem_crs(dem_file,GCP_dict, epsg_gcp, GCP_name)
        GCP_dict = get_height(dem_file,GCP_dict, GCP_name)
        col_value = raw_input('Please enter col position of GCP in image (read from QGIS): \n')
        row_value = raw_input('Please enter row position of GCP in image (read from QGIS): \n')
        GCP_file_list.append([str(int(round(GCP_dict[GCP_name+'_UTM_E_final']))), str(int(round(GCP_dict[GCP_name+'_UTM_N_final']))), str(GCP_dict[GCP_name+'_height']), str(int(round(float(col_value)))), str(int(-(round(float(row_value))))), GCP_name])
        
        points_UTM = [(int(east[pt]), int(north[pt])) for pt in range(len(east))]
        closest_point = sp.spatial.distance.cdist([(float(GCP_dict[GCP_name+'_UTM_E_final']),float(GCP_dict[GCP_name+'_UTM_N_final']))], points_UTM).argmin()
        #points_UTM[closest_point]
        col_view = img_col[closest_point]
        row_view = img_row[closest_point]
        
        ##### add manually derived GCPs to GCP shapefile 
        dataSource = driver.Open(shapefile, 1)
        layer = dataSource.GetLayer()
        # create the feature
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetField('name', GCP_name+'_img')
        wkt = "POINT(%f %f)" %  (float(col_value) , float(row_value))
        point = ogr.CreateGeometryFromWkt(wkt)
        feature.SetGeometry(point)
        feature.SetFID(layer.GetFeatureCount())
        layer.CreateFeature(feature)
        feature.Destroy()
        feature = ogr.Feature(layer.GetLayerDefn())
        feature.SetField('name', GCP_name+'_view')
        wkt = "POINT(%f %f)" %  (float(col_view) , -float(row_view))
        point = ogr.CreateGeometryFromWkt(wkt)
        feature.SetGeometry(point)
        feature.SetFID(layer.GetFeatureCount())
        layer.CreateFeature(feature)
        feature.Destroy()        
        dataSource.Destroy()
        manual_GCP = check_input('Do you want to add another GCP? y/n \n')
    print('Acquiring of GCPs finished')
        
################### check GCP shapefile and write result into gcp.txt-file for PRACTISE #####################
    ##### create path for gcp.txt-file and store data 
    gcp_path = os.path.join(webcam_path, 'GCPs')
    if not os.path.exists(gcp_path):
        os.makedirs(gcp_path) 
        
    with open(os.path.join(gcp_path,data_used['folder_name']+'.gcp.txt'), 'w') as gcp_file:
        for line in GCP_file_list:
            print(line)
            gcp_file.write(' '.join(line)+'\n') 
#############################################################################################################
#----------- 5. check & extract GCPs from shapefile & write them into txt-file demanded by PRACTISE ---------
#############################################################################################################
    
    
    
    
    
#############################################################################################################
#----------- 6. write parameters into octave file and run projection procedure with GCP correction ----------
#############################################################################################################
    
    ##### read octave PRACTISE_input file 
    if (run_var_gcp==1):
        with open(os.path.join(PRACTISE_Path,'run'+ str(run_var) +'.m'), 'r') as octave_file:
            PRACTISE_input_gcp = octave_file.readlines()
    else:
        with open(os.path.join(PRACTISE_Path,'run_gcp'+ str(run_var_gcp-1) +'.m'), 'r') as octave_file:
            PRACTISE_input_gcp = octave_file.readlines()
    
    ##### if wanted, adjust possible value range of variables for Correction Optimisation
    adj_boundaries = check_input("\nDo you want to adjust the possible value range of variables for the Optimisation? y/n \n")
    if (adj_boundaries):
        boundary_values = PRACTISE_input_gcp[36]
        boundary_values = boundary_values.split('[')[1].split(']')[0].split(', ')
        boundary_dict = collections.OrderedDict((var_bound[k], boundary_values[k]) for k in range(len(boundary_values)))
        boundary_dict = edit_dict(boundary_dict, overwrite=True)
        joined_bound = ''
        joined_bound_neg = ''
        for b in var_bound:
            joined_bound = ', '.join([joined_bound,boundary_dict[b]])
            joined_bound_neg = ', -'.join([joined_bound_neg,boundary_dict[b]])
        joined_bound = joined_bound[2:]
        joined_bound_neg = joined_bound_neg[2:]
        output_boundaries = '[' + joined_bound +  ']'
        output_boundaries_neg = '[' + joined_bound_neg +  ']'
        PRACTISE_input_gcp = edit_octave_file(PRACTISE_input_gcp, 36, output_boundaries)
        PRACTISE_input_gcp = edit_octave_file(PRACTISE_input_gcp, 37, output_boundaries_neg)
    
    # create input path for PRACTISE run
    run_path = os.path.join(PRACTISE_Path, 'run_gcp'+ str(run_var_gcp))
    if not os.path.exists(run_path):
        os.makedirs(run_path)
    
    # copy needed files to PRACTISE input path
    shutil.copy2(os.path.join(image_path, image_name[0]), run_path)                     # image 
    shutil.copy2(os.path.join(gcp_path,data_used['folder_name']+'.gcp.txt'), run_path)  # gcp.txt-file 
        
    # change directory
    PRACTISE_input_gcp = edit_octave_file(PRACTISE_input_gcp, 9, "'run_gcp"+ str(run_var_gcp) +"\\'")   # directory with input of correction run X
    # add interactive GCP correction including optimisation
    PRACTISE_input_gcp = edit_octave_file(PRACTISE_input_gcp, 1, str(3))
    
    
########################### write edited parameters in new PRACTISE_input file ##############################
    ##### create input file
    with open(os.path.join(PRACTISE_Path,'run_gcp'+ str(run_var_gcp) +'.m'), 'w') as octave_file:
        for line in PRACTISE_input_gcp:
            octave_file.write(line) 
        
    ##### write directory to input file in file, which calls input file
    with open(os.path.join(octave_dir,'Input_PRACTISE.m'), 'r') as octave_file:
        PRACTISE_input_main = octave_file.readlines()
    PRACTISE_input_main = edit_octave_file(PRACTISE_input_main, 19, "'"+dir_for_octave(run_path)+"'")
    with open(os.path.join(octave_dir,'Input_PRACTISE.m'), 'w') as octave_file:
        for line in PRACTISE_input_main:
            octave_file.write(line) 
            
            
########################## start run of PRACTISE projection including GCP correction ####################
    python_wd = os.getcwd()     # save current directory
    os.chdir(octave_dir)        # set wd to directory of PRACTISE scripts
    
    
    ##### call PRACTISE script as subprocess and print its messages to console
    print('\n\nstart GCP correction run No' + str(run_var_gcp) + ' of PRACTISE...')
    print('this may take up to 15-30 minutes, depending on the size of the DEM file and the complexity of the projection procedure')
    process2 = subprocess.Popen(['octave','PRACTISE.m'],stdout=subprocess.PIPE)
    print_subprocess_messages(process2)
    
    # run with GCP correction is finished, reset wd
    print('\nGCP correction run No' + str(run_var_gcp) + ' of PRACTISE is finished')
    os.chdir(python_wd)    
    
#############################################################################################################
#---------------- 6. finished running PRACTISE projection procedure with GCP correction ---------------------
#############################################################################################################
            
            
    
    
    
#############################################################################################################
#-------- 7. check GCP correction result, decide if rerun is needed => then change input parameters ---------
#############################################################################################################
    print('\n\nPlease check, if the corrected view is giving a reasonable result')
    print('If not, consider, if it would be an improvement to increase/decrease the possible variable range or')
    print(' if changes in the GCPs (adding, deleting, moving) could improve the result')
    print('Please remember that after this step polynomial fitting will be applied for further improvement.')
    time.sleep(10)
    
########################## show projection result from PRACTISE as first check ##############################
    ##### get folder with PRACTISE output (projected DEM pixels classified) 
    folder_result = [f for f in os.listdir(PRACTISE_Path) if 'run_gcp'+ str(run_var_gcp) +'_' in f]
    folder_result = os.path.join(PRACTISE_Path,folder_result[0])
    results = os.listdir(folder_result)
    check_image = [f for f in results if (f.endswith('_auto.ofig'))]
    check_image = os.path.join(folder_result,check_image[0])
    
    ##### create Octave file to read and open projection result
#    with open(os.path.join(folder_result,'run_image.m'), 'w') as octave_file:
#        octave_file.write('hgload("'+check_image+'")\n') 
#        octave_file.write('waitforbuttonpress()')
#    p_img.append(subprocess.Popen(["octave",os.path.join(folder_result,'run_image.m')],stdout=subprocess.PIPE))
    
############################# read output of projection with GCP correction #################################
    # create directory for gcp corection results
    result_correction = os.path.join(webcam_path, 'results/result2_'+str(run_var_gcp))
    if not os.path.exists(result_correction):
        os.makedirs(result_correction)
        
    # get & read PRACTISE output file   
    result_file =  [f for f in results if (f.endswith('_proj.mat'))]
    result_file = os.path.join(folder_result,result_file[0])
    with open(result_file, 'r') as output:
        result_output = output.readlines()
        
    # get number of columns and no of rows of image
    rows = int(result_output[109])
    cols = int(result_output[114])
    
    # get projected DEM points with their attributes E,N,h & position in image
    east = result_output[135].split(' ')[1:]
    east = [int(pt) for pt in east]
    north = result_output[136].split(' ')[1:]
    north = [int(pt) for pt in north]
    alt = result_output[137].split(' ')[1:]
    alt = [int(pt) for pt in alt]
    img_col = result_output[167].split(' ')[1:]
    img_col = [float(pt) for pt in img_col]
    img_row = result_output[168].split(' ')[1:]
    img_row = [float(pt) for pt in img_row]
    points = [(int(img_row[pt]), int(img_col[pt])) for pt in range(len(img_col))]
    
    # calculate distance to camera to derive edges later
    dist = [math.sqrt((float(east[pt])-data_used['camera_UTM_E_final'])**2+(float(north[pt])-data_used['camera_UTM_N_final'])**2) for pt in range(len(img_col))]
    
############################### create a shape file with the projected points ###############################
    driver = ogr.GetDriverByName("ESRI Shapefile")
    data_source = driver.CreateDataSource(os.path.join(result_correction,"points.shp"))
    srs = osr.SpatialReference()
    layer = data_source.CreateLayer("ref_pts", srs, ogr.wkbPoint)
    
    # Add variable fields     
    layer.CreateField(ogr.FieldDefn("img_col", ogr.OFTReal))
    layer.CreateField(ogr.FieldDefn("img_row", ogr.OFTReal))
    layer.CreateField(ogr.FieldDefn("UTM_East", ogr.OFTReal))
    layer.CreateField(ogr.FieldDefn("UTM_North", ogr.OFTReal))
    layer.CreateField(ogr.FieldDefn("Elevation", ogr.OFTReal))
    layer.CreateField(ogr.FieldDefn("Distance", ogr.OFTReal))
    
    # add the attributes and features to the shapefile
    for pt in range(len(img_col)):
      # create the feature
      feature = ogr.Feature(layer.GetLayerDefn())
      # Set the attributes using the values from the delimited text file
      feature.SetField("img_col", img_col[pt])
      feature.SetField("img_row", img_row[pt])
      feature.SetField("UTM_East", east[pt])
      feature.SetField("UTM_North", north[pt])
      feature.SetField("Elevation", alt[pt])
      feature.SetField("Distance", dist[pt])
      # create the WKT & set geometry to point
      wkt = "POINT(%f %f)" %  (float(img_col[pt]) , -float(img_row[pt]))
      point = ogr.CreateGeometryFromWkt(wkt)
      feature.SetGeometry(point)
      layer.CreateFeature(feature)
      feature = None
    data_source = None
    
    
#################### open QGIS project with projected dem points colored by distance ########################
############################## as second check and decide to rerun or not ###################################
    
    ##### add needed files to result directory
    # add webcam image
    shutil.copy2(os.path.join(image_path, image_name[0]), os.path.join(result_correction, 'image.'+file_ending))
    # add QGIS project
    shutil.copy2(os.path.join(code_dir,'Auxiliary_data','check_GCP_corr.qgz'), result_correction)
    # open QGIS project
    p_img.append(subprocess.Popen(['qgis',os.path.join(result_correction, 'check_GCP_corr.qgz')],stdout=subprocess.PIPE, stderr=subprocess.PIPE))
    time.sleep(10)
    
    ##### decide, if you rerun GCP correction or not
    rerun_GCP_corr = check_input("\nDo you want to run the GCP correction again? y/n \n")
    if not (rerun_GCP_corr):
        break
    
    ##### decide, if you want to change, add or remove GCPs for next correction
    correct_GCPs=check_input("\nDo you want to check the GCPs in the shapefile? y/n \n")
    if (correct_GCPs):
        gcp_p.append(subprocess.call(['qgis',os.path.join(result_first_run, 'test_edges.qgz')],stdout=subprocess.PIPE, stderr=subprocess.PIPE))

#############################################################################################################
#------ 8. end checking of GCP correction result, if rerun is needed => move back to 5. GCP extraction ------
#---------- if no additional rerun with GCP correction is needed, move on to 9. polynomial fitting ----------
#############################################################################################################





#############################################################################################################
#--------------------------- 9. Draw Reference Points for polynomial fitting in QGIS ------------------------
#############################################################################################################
        
# get path to GCP correction with best result
run_var_gcp = raw_input("\nWhich run of the GCP correction runs has the best result, which you want to continue with? \n")
result_correction = os.path.join(webcam_path, 'results/result2_'+str(run_var_gcp))

##### add qgz-project for polynomial fitting              
shutil.copy2(os.path.join(code_dir,'Auxiliary_data','polynom_fit.qgz'), result_correction)

##### create shapefile for polynomial fitting
driver = ogr.GetDriverByName("ESRI Shapefile")
data_source = driver.CreateDataSource(os.path.join(result_correction,"poly_fit.shp"))
srs = osr.SpatialReference()
layer = data_source.CreateLayer("fit", srs, ogr.wkbPoint)
field_name = ogr.FieldDefn("name", ogr.OFTString)
field_name.SetWidth(24)
layer.CreateField(field_name)
data_source = None   


########################## draw reference points for polynomial fitting in QGIS #############################
print('\nPlease create points for Polynomial Fitting along the skyline')
print('Please create them always paired, one for the current projected position &')
print(' one for the real position of the DEM point in the image')
print('Nomenclature: ')
print('     uniqueprefix_old: current projection position')
print('     uniqueprefix_real: real position of DEM point in image')
print(' e.g: p1_old, p1_real, p2_old, p2_real,...')
time.sleep(10)
p_poly = list()
p_poly.append(subprocess.call(['qgis',os.path.join(result_correction, 'polynom_fit.qgz')],stdout=subprocess.PIPE, stderr=subprocess.PIPE))
time.sleep(5)
#############################################################################################################
#------------------------------------- 9. End Reference Points extraction -----------------------------------
#############################################################################################################




#############################################################################################################
#--- 10. check reference points, extract variables, run interpolation & correct projection point position ---
#############################################################################################################

# ask, if Reference Points for polynomial fitting do exist
fitting_data = check_input("\nHave you created some reference points for polynomial fitting? y/n \n")
if not (fitting_data):
    print ('No Reference Points have been acquired. End program')
    sys.exit()
    
while (True):
######################################### check Reference points ############################################
    # open shp file
    shapefile = os.path.join(result_correction,"poly_fit.shp")
    driver = ogr.GetDriverByName("ESRI Shapefile")
    dataSource = driver.Open(shapefile, 0)
    layer = dataSource.GetLayer()
        
    # show names of all acquired Reference points
    print ('\nThese are the acquired Fitting Points:')
    for feature in layer:
        print feature.GetField("name")
    dataSource.Destroy()
    
    # give possibility to change Reference point names, if they are wrong
    fitting_names = True
    while(fitting_names):
        fitting_names = check_input("\nDo you want to change a name in the list? y/n \n")
        if not (fitting_names):
            break
        fitting_name = raw_input('Please enter old name: \n')
        dataSource = driver.Open(shapefile, 1)
        layer = dataSource.GetLayer()
        for feature in layer:
            if(feature.GetField("name")==fitting_name):
                feature.SetField("name",raw_input('Please enter new name: \n'))
                layer.SetFeature(feature)
        dataSource.Destroy()
    
    
    # append names of final Reference Points to list
    names_list=list()
    dataSource = driver.Open(shapefile, 0)
    layer = dataSource.GetLayer()
    for feature in layer:
        names_list.append(feature.GetField("name"))
    dataSource.Destroy()
    
        
    ##### check, if Reference Points occur paired (one for the current projected location & one true location in the image)
    #####    if not, exclude
    fit_names = [name.split('_')[0] for name in names_list]
    unique_names = set(fit_names)
    used_fits = set(fit_names)
    for x in unique_names:
        if not(fit_names.count(x)==2):
            print (x+ ': not correct number available => will be excluded')
            used_fits.remove(x)
    unique_names = None

################################# extract values and run interpolation ######################################
    print("\nRun polynomial fitting and create shapefile with corrected point locations...")
    # create lists for interpolation
    col_pos_list=list()
    col_dif_list=list()
    row_dif_list=list()
    
    ##### extract needed data (column position, column & row change (projection-reality)) from shapefile
    for x in used_fits:
        dataSource = driver.Open(shapefile, 0)
        layer = dataSource.GetLayer()
        for feature in layer:
            if(feature.GetField("name")==(x+'_old')):
                coords_now = feature.GetGeometryRef().GetPoint()
            if(feature.GetField("name")==(x+'_real')):
                coords_after = feature.GetGeometryRef().GetPoint()
        dataSource.Destroy()
        (col_now, row_now,z) = coords_now
        (col_after, row_after, z) = coords_after
        col_pos_list.append(col_now)
        col_dif_list.append(col_after - col_now)
        row_dif_list.append(row_after - row_now)
     
    ##### run interpolation
    xnew = np.linspace(0, cols, num=cols+1, endpoint=True)
    p_col = np.poly1d(np.polyfit(col_pos_list, col_dif_list, 7))
    #plt.plot(col_pos_list, col_dif_list, 'ro', xnew, p_col(xnew), '-')
    p_row = np.poly1d(np.polyfit(col_pos_list, row_dif_list, 7))
    #plt.plot(col_pos_list, row_dif_list, 'ro', xnew, p_row(xnew), '-')


############# read projected point values and apply polynomial correction on row/col position ###############
    
    ##### get folder with PRACTISE output (projected DEM pixels classified) 
    folder_result = [f for f in os.listdir(PRACTISE_Path) if 'run_gcp'+ str(run_var_gcp) +'_' in f]
    folder_result = os.path.join(PRACTISE_Path,folder_result[0])
    results = os.listdir(folder_result)
    
    # get & read PRACTISE output file  
    result_file =  [f for f in results if (f.endswith('_proj.mat'))]
    result_file = os.path.join(folder_result,result_file[0])
    with open(result_file, 'r') as output:
        result_output = output.readlines()
        
    # get number of columns and no of rows of image
    rows = int(result_output[109])
    cols = int(result_output[114])
    
    # get projected DEM points
    east = result_output[135].split(' ')[1:]
    east = [int(pt) for pt in east]
    north = result_output[136].split(' ')[1:]
    north = [int(pt) for pt in north]
    alt = result_output[137].split(' ')[1:]
    alt = [int(pt) for pt in alt]
    img_col = result_output[167].split(' ')[1:]
    img_col = [float(pt) for pt in img_col]
    img_row = result_output[168].split(' ')[1:]
    img_row = [float(pt) for pt in img_row]
    points = [(int(img_row[pt]), int(img_col[pt])) for pt in range(len(img_col))]
    
    ###### calculate corrected position of projected DEM points
    img_col_new = [pt+p_col(pt) for pt in img_col]
    img_row_new = [img_row[pt]-p_row(img_col[pt]) for pt in range(len(img_col))]
    points_new = [(int(img_row_new[pt]), int(img_col_new[pt])) for pt in range(len(img_col_new))]
    
    # calculate distance to camera to derive edges mask later
    dist = [math.sqrt((float(east[pt])-data_used['camera_UTM_E_final'])**2+(float(north[pt])-data_used['camera_UTM_N_final'])**2) for pt in range(len(img_col))]
    

###################### create shp-file with corrected position of projected points ##########################
    
    ##### create a shape file with the projected points
    driver = ogr.GetDriverByName("ESRI Shapefile")
    data_source = driver.CreateDataSource(os.path.join(result_correction,"points_fitted.shp"))
    srs = osr.SpatialReference()
    layer = data_source.CreateLayer("ref_pts", srs, ogr.wkbPoint)
    
    # Add variable fields 
    layer.CreateField(ogr.FieldDefn("img_col_ne", ogr.OFTReal))
    layer.CreateField(ogr.FieldDefn("img_row_ne", ogr.OFTReal))
    layer.CreateField(ogr.FieldDefn("UTM_East", ogr.OFTReal))
    layer.CreateField(ogr.FieldDefn("UTM_North", ogr.OFTReal))
    layer.CreateField(ogr.FieldDefn("Elevation", ogr.OFTReal))
    layer.CreateField(ogr.FieldDefn("Distance", ogr.OFTReal))
    
    # add the attributes and features to the shapefile
    for pt in range(len(img_col_new)):
      # create the feature
      feature = ogr.Feature(layer.GetLayerDefn())
      # Set the attributes using the values from the delimited text file
      feature.SetField("img_col_ne", img_col_new[pt])
      feature.SetField("img_row_ne", img_row_new[pt])
      feature.SetField("UTM_East", east[pt])
      feature.SetField("UTM_North", north[pt])
      feature.SetField("Elevation", alt[pt])
      feature.SetField("Distance", dist[pt])
      # create the WKT & set geometry to point
      wkt = "POINT(%f %f)" %  (float(img_col_new[pt]) , -float(img_row_new[pt]))
      point = ogr.CreateGeometryFromWkt(wkt)
      feature.SetGeometry(point)
      layer.CreateFeature(feature)
      feature = None
    data_source = None
    print('Shapefile with corrected positions has been created')
    
################# check polynomial fitting in QGIS and decide, if fitting must run again ####################
    shutil.copy2(os.path.join(code_dir,'Auxiliary_data','check_fitting.qgz'), result_correction)
    check_fitting = check_input('Do you want to have a look at the fitted data? y/n')
    if (check_fitting):
        print('\n Please, have a look. If you want to rerun polynomial fitting again, please add/remove/change Reference points now. \n')
        p_poly.append(subprocess.Popen(['qgis',os.path.join(result_correction, 'check_fitting.qgz')],stdout=subprocess.PIPE, stderr=subprocess.PIPE))
        time.sleep(10)
        rerun_fitting = check_input('Do you want to change the reference points and run polynomial fitting again? y/n \n')
        if not (rerun_fitting):
            break
    else:
        break
#############################################################################################################
#----------------------------- 10. finish polynomial fitting of projected points ----------------------------
#############################################################################################################





#############################################################################################################
#------------ 11. create mask with viewshed edges to filter unsecure areas from webcam projection -----------
#############################################################################################################       
startTime=time.time()
# create folder with final output
result_final  = os.path.join(webcam_path, 'results_final')
if not os.path.exists(result_final):
    os.makedirs(result_final)
    
# copy relevant existing data to final folder
results = [f for f in os.listdir(result_correction) if ('points_fitted' in f)]
for filename in results:
    shutil.copy2(os.path.join(result_correction,filename), result_final)
shutil.copy2(os.path.join(image_path, image_name[0]), os.path.join(result_final, 'image.'+file_ending))

################ interpolate input parameters for each image pixel, needed for mask calculation #############
################ (parameters: distance to camera, distance to projected points, x/y/z-position) #############
print('\n\nInterpolate & Write final output (location raster & mask) in final folder...')

print('Start interpolation of parameters ...')
# interpolation grid 
grid_x, grid_y = np.mgrid[0:rows, 0:cols]

# interpolate
dist_raster = sp.interpolate.griddata(points_new, np.array(dist),(grid_x, grid_y), method='nearest')
lin_check = 'linear'
#while (True):
#    input_lin = raw_input("Do you want to use nearest neighbor interpolation (for images with many points) ('nearest') or use linear interpolation (less DEM points available) ('linear')? \n ")
#    if (input_lin=='') or (input_lin == 'nearest'): 
#        break
#    elif (input_lin == 'linear'):
#        lin_check = 'linear'
#        break
#    else:
#        print("wrong input: only 'linear' or 'nearest' possible")
east_raster = sp.interpolate.griddata(points_new, np.array(east),(grid_x, grid_y), method=lin_check)
north_raster = sp.interpolate.griddata(points_new, np.array(north),(grid_x, grid_y), method=lin_check)
alt_raster = sp.interpolate.griddata(points_new, np.array(alt),(grid_x, grid_y), method=lin_check)

# safe result as tif-file
write_array_as_geotiff(dist_raster, result_final, "dist_raster.tif")
write_array_as_geotiff(east_raster, result_final, "east_raster.tif")
write_array_as_geotiff(north_raster, result_final, "north_raster.tif")
write_array_as_geotiff(alt_raster, result_final, "alt_raster.tif")



##### calculate distance of pixel to next projected point, needed to detect skyline
#(very time consuming, maybe easier approach possible)
print('Calculate distance to projected points. Very time consuming... ')
# reference points to calculate point distance (dont use all to save time)
ref_pts = list()
for row in range(0,rows, 4):
    for col in range(0,cols, 4):
        ref_pts.append((row, col))  
        
points_selected =list()
subset= max(len(points_new)/100000,1)
for x in range(0, len(points_new), subset):
    points_selected.append(points_new[x])
    
# calculate minimum distance to next projected point and append to one list    
dist_info = list()
for i in range(len(ref_pts)/10000+1):
    dist_info.append(sp.spatial.distance.cdist(ref_pts[i*10000:min(i*10000+10000,len(ref_pts))],points_selected, 'euclidean').min(axis=1))
dist_pts_final = dist_info[0]
for array in dist_info[1:(len(ref_pts)/10000+1)]:
    dist_pts_final = np.append(np.array(dist_pts_final),np.array(array))

# interpolate result to raster of image size and save it as tif-file
dist_pts = np.array(dist_raster)
dist_pts = sp.interpolate.griddata(ref_pts, dist_pts_final,(grid_x, grid_y), method='nearest')
write_array_as_geotiff(dist_pts, result_final, "point_distance.tif")


######################################### start edge calculation ############################################
print('Start calculation of viewshed edges ...')

# procedure to calculate skyline
edges_dist = np.array(dist_pts)
mw_diff_numba(dist_pts, edges_dist,5,5)
edges_dist2 = np.array(dist_pts)
mw_diff_numba(edges_dist, edges_dist2,5,5)
edges_dist2_adj = np.array(edges_dist2)
mw_diff_from_mean(edges_dist2, edges_dist2_adj,25,25)

# calculate absolute edges (distmax-distmin)
edges = np.array(dist_raster)
mw_diff_numba(dist_raster, edges,5,5)
# calculate relative edges ((distmax-distmin)/distmin) to find close edges
edges2 = np.array(edges)
mw_edge2(edges, dist_raster, edges2, 5,5)

###### create buffers for unsecure areas in image, which should be neglected, when projection is applied ####
print('Create buffers ...')

# apply general filters (needed to exclude areas above skyline & areas with scarce point density close to camera)
edges_dist2_adj[dist_pts>20] = 0
edges[dist_pts>20]=0
edges2[dist_pts>50]=0
            
            
# create a binary layer with pronounced close edges
edges2_bin = np.array(edges2)
edges2_bin[edges2 >=0.2] = 1
edges2_bin[edges2 <0.2] = 0

# calculate minimum distance within a window as help variable for close & very close edges
dist_min = np.array(edges2_bin)
dist_min = mw_min_numba(dist_raster, dist_min, 5, 5)

# create very big buffer for very close edges
very_close_edges = np.array(edges2_bin)
very_close_edges[dist_min > 2000] = 0
very_close_edges_fil = np.array(very_close_edges)
very_close_edges_fil = mw_max_numba(very_close_edges, very_close_edges_fil, 35, 35)

# create big buffer for close edges
close_edges = np.array(edges2_bin)
close_edges[dist_min >5000] = 0
close_edges_fil = np.array(close_edges)
close_edges_fil = mw_max_numba(close_edges, close_edges_fil, 25, 25)

# create filter to exclude points very close to the skyline
edges_dist2_adj[edges_dist2_adj<0] = 0
edges_dist2_adj[dist_raster<(dist_raster.max()/4)] = 0
edges_dist2_adj[dist_pts>20] = 0
edges_dist2_adj_bin = np.array(edges_dist2_adj)
edges_dist2_adj_bin[edges_dist2_adj>3] = 1
edges_dist2_adj_bin[edges_dist2_adj<=3] = 0
edges_dist2_adj_bin_fil = np.array(edges_dist2_adj_bin)
edges_dist2_adj_bin_fil = mw_max_numba(edges_dist2_adj_bin, edges_dist2_adj_bin_fil, 5, 5)

# create filter for areas with big spatial distance in short pixel range
edges_unsecure = np.array(edges_dist2_adj_bin)
edges_unsecure = mw_diff_numba(dist_raster, edges_unsecure,5,11)

################# apply all buffers and filters create a mask layer and save it as a tif-file ###############
print('Apply filters ...')
# apply filters
mask = np.array(dist_raster)
mask[close_edges_fil==1]=0
mask[very_close_edges_fil==1]=0
mask[edges_dist2_adj_bin_fil==1]=0
mask[edges>200]=0
mask[edges_unsecure>500]=0
help_mask = np.array(dist_pts)
help_mask[dist_raster<(dist_raster.max()/4)] =0
mask[help_mask>9]=0
mask[mask>35000]=0
mask[mask>0]=1

endTime=time.time()
print('Duration of mask layer calculation: ' + str(endTime-startTime))
##### write result as tif-file
print('Write mask to tif file...')
write_array_as_geotiff(mask, result_final, "mask.tif")


DemDs = gdal.Open(dem_file, GA_ReadOnly)
pj_final=DemDs.GetProjection()

with open(os.path.join(folder_result,'projection.prj'), 'w') as proj_file:
    proj_file.write(pj_final) 

print('End of program. Completed successfully!')
#############################################################################################################
#------------------------------------------- 11. end mask creation ------------------------------------------
#############################################################################################################


#############################################################################################################
################################################ end procedure ##############################################
#############################################################################################################
