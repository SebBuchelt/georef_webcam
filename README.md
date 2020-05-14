# georef_webcam <img width="429" align="right" src="https://github.com/SebBuchelt/aux_data/blob/master/hintereisferner_webcam.jpg"> <br /> <br /> <img src="https://github.com/SebBuchelt/aux_data/blob/master/compare.gif" width="420" > 


### Python toolbox to georeference webcam images 
- <p style="color:red"> Currently under major revision! </p>
- **Maintainer**: Sebastian Buchelt
- **Citation**: Buchelt, S. (2018-): georef_webcam 0.0.1, https://github.com/SebBuchelt/georef_webcam.
- **License**: CC-BY-NC-SA 4.0

## Overview

`georef_webcam` is a console-based python tool in early development stage. It provides a script to georeference webcam images without accurate knowlegde about needed input parameters.
This script enables the user to georeference images based on rough estimations about camera position, system parameters & looking direction. <br /> <br />
The standard approaches use in-situ measured Ground Control Points (GCPs) for accurate geolocation.
Here they can be derived using unique morphological features (edges) in the Field of View (FOV) or exact location of clearly visible man-made structures within the FOV.

#### Requirements
Please look in `requirements.txt` to see, which python libraries are required for the  `georef_webcam` package.
It is also mandatory to download `Octave`, as the core projection procedure is running on Matlab scripts from [PRACTISE package](https://github.com/shaerer/PRACTISE).
Additionally, you also need `QGIS` Version 3.0 or higher. So far this tool has only been tested in Ubuntu 16.04 & 18.04. For Windows no guarantee for functionality can be given.
<br /> <br />

## Getting started
#### The following description gives a short idea, how the procedure works and which steps you need to follow to get a good georeferencing result.
Download package to the directory you like.
Before starting the execution of the script, you should have the webcam image & the DEM file available for processing. <br />
<br />

### Start procedure
The script georef_webcam.py requires only one input parameter: <br />
- `out_dir`: directory, where all output will be stored in several subfolders
- optional: `dem_subfolder` define name of subfolder for DEM
 
```bash
$ source activate ‘conda_environment’
$ cd /path/to/package/
$ python python_scripts/georef_webcam.py /path/where/output/will/be/stored
```

First you are asked to download or copy DEM file to the given directory (unless it is already there):
```bash
…
DEM data is not available!
Please put DEM data in following folder:
‘subfolder/for/dem’

…
```
Then the needed Octave package PRACTISE V2.1 is downloaded and the program starts to acquire the needed parameters. <br />
If you are using a webcam image from the webpage [foto-webcam.eu](https://www.foto-webcam.eu), the camera metadata provided by the website can be used. Otherwise mandatory parameters are asked to be defined via console input.

**Needed parameters:**
- camera name 
- name for output subfolder
- camera position (lat & lon or Easting & Northing)
- camera altitude (derived from DEM) & height above ground
- looking direction of camera or position of target
- camera system parameters: focal length, sensor width & height

Please make rough estimates for these parameters or look them up online.


After that you are asked to download or copy the webcam image file to the given directory:
```bash
…
Please add webcam image to the following folder:
‘subfolder/for/webcam/image’
Is the image there now? y/n
…
```

Then parameters are provided to PRACTISE to execute projection. As the script of PRACTISE hasn't been changed, some windows will pop up and close during the execution.
```bash
start first run of PRACTISE…
this may take up to 15-30 minutes, depending on the size of the DEM file and the complexity of the projection procedure
```
<br />

### Result first run
The script opens an octave window showing the position of the projected DEM points in the image plane. You can check how accurate your first estimates were and decide if you want to adjust the input parameters (usually horizontal & vertical looking direction of the camera) to improve the projection result. Otherwise the program will proceed with the next step.
<p align="center"><img width="90%" src="https://github.com/SebBuchelt/aux_data/blob/master/offset_wArrows.png"></p>
<p align="center"><sub>Figure 1: Octave window with result of first projection shows a systematic offset of the projected points towards the upper right. <br />
To move projection points rightwards, direction angle must be decreased. To move points upwards, target point height or pitch angle must be decreased. </sub></p>
<br />

### Second step – Edge delineation for GCPs
In the next step, edges in the image as well as morphologic edges in the DEM panorama will be calculated.
Once this is finished the edge layers are opened in a QGIS project. You are asked, if panoramic edges are too small. In that case the layer will be fast recalculated and plotted bigger.
You can now start to draw GCPs based on the morphological features in the image.
As the position of reference points is needed once for the DEM feature and once for the same feature in the image, you need to create always 2 points:
- one at the edge feature in the image (name: e.g. p1_img, p2_img, rightpeak_img)
- & one at the same feature in the viewshed (name: p1_view, p2_view, rightpeak_view)

**Please consider: The paired GCPs must have the corresponding same prefix in the name! So please check names!**

<p align="center"><img width="90%" src="https://github.com/SebBuchelt/aux_data/blob/master/Edges.jpg"></p>
<p align="center"><sub>Figure 2: Webcam image overlayed with the image edges (green) and the panoramic edges (red). 
The paired acquisition of GCPs can be seen as well. </sub></p>
<br>

After deriving GCPs from morphological features, you can also add GCPs manually to the acquired list. 
Therefore, you need to add the coordinate position of the feature & then add the row/col position of this feature in the image when opened with QGIS.
<p align="center"><img height="250"  src="https://github.com/SebBuchelt/aux_data/blob/master/golf_google.png">       <img src="https://github.com/SebBuchelt/aux_data/blob/master/golf_webcam.png" height="250" ></p>
<p align="center"><sub>Figure 3: Feature found in Google Maps and in webcam (Source: <a href="https://maps.google.de"> Google Maps</a> & <a href="https://www.foto-webcam.eu"> foto-webcam.eu</a>) </sub></p>
<br />

### Second projection – GCP correction
After providing GCPs for the Optimisation of the Projection, the script asks, whether value ranges for projection parameters should be adjusted or kept at default. Default values are shown here:

| Parameter | Range |
| -------------- | --------- |
| camera_east | +-50m|
| camera_north | +-50m |
| camera_altitude | +-50m |
| roll_angle | +-3° |
| target_east | +-100m |
| target_north | +-100m |
| target_altitude | +-100m |
| focal_length | +-0.001m (=1mm) |
| sensor_height | +-0.000m |
| sensor_width | +-0.000m |

Then the Second Projection with GCP correction is executed in PRACTISE. 
```bash
start GCP correction run No1 of PRACTISE…
this may take up to 15-30 minutes, depending on the size of the DEM file and the complexity of the projection procedure
```
<br />

### Result second run
The script opens a QGIS project showing the image and the location of the corrected DEM points. There you can check, how accurate the projection with GCP correction was & decide if you want to run the GCP with new parameters again. If you want to rerun, you have the possibility to change the GCPs (add new or delete wrong ones, moving inaccurate ones) and, if you want, you can also adjust the possible value range of the projection parameters (see Table above). <br /> 
If you are convinced with the result, you can decide to continue with the following step.
<br /><br />

### Points for Sensor Distortion Adjustment – Polynomial Fitting 

<figure> <img align="right" width="40%" src="https://github.com/SebBuchelt/aux_data/blob/master/fitting3.png"></figure>

Similar to deriving GCPs, the fitting points are created always paired. 
First you need to create a point at the location of a remarkable DEM point (p_old). Then you create another point at the position, where the DEM point should be located in reality (p_real). So again you have two points: 
- one at the current position of a DEM point in the image (name: e.g. p1_old, p2_old, rightpeak_old)
- & one at the feature in the image, where this DEM point should be in reality (name: p1_real, p2_real, rightpeak_real)

**Please consider:  The paired Fitting points must have the corresponding same prefix in the name! So please check names!**

Once acquiring fitting points is finished, the polynomial fitting in column direction is applied. You can again check the fitting in the QGIS project, which is opening. If you want to adjust or improve the fitting, you can change the fitting points & rerun it. So far there is no possibility to change the degree of the polynomial fitting function.
Once your result is finally accurate enough for your purposes, you can move on to the last step.
<br /><br />

### Calculation of final results
In this step no further input is needed. The script interpolates the world coordinate position for each image pixel. There is also a mask generated, which excludes the area above the skyline and areas with high uncertainty along the edges in the panoramic view.

## Resulting Output

<p align="center"><img width="90%" src="https://github.com/SebBuchelt/aux_data/blob/master/Projected_points.jpg"></p>
<p align="center"><sub>Figure 4: Final result: DEM points projected to image plane. From this, coordinate values for each pixel are interpolated. </sub></p>
<br>

- the original image
- three tif-files with the size of the image giving the easting, northing & altitude of each pixel
- one tif-file containing the mask layer
- shp-file with the corresponding fitted points

The results can be found in the following directory:
`/path_you_gave_at_beginning/subfolder_for_webcam/results_final`

## Outlook 
So far only one function `georef_webcam.py` is provided in this package. Soon other features will be available like projecting georeferenced images to UTM or lat/lon coordinates or projection of training polygons & points drawn in image to UTM or lat/lon coordinates. It is also planned to provide a tool to register webcam images to each other to avoid projection procedure for every single image.

<p align="center"><img width="90%" src="https://github.com/SebBuchelt/aux_data/blob/master/hintereisferner_webcam.jpg"></p>
<p align="center"><sub>Figure 5: Used webcam image. </sub></p>
<br>
<p align="center"><img width="90%" src="https://github.com/SebBuchelt/aux_data/blob/master/compare.gif"></p>
<p align="center"><sub>Figure 6: Animation showing Sentinel-2 image overlayed with projected webcam image. </sub></p>
<br>

# References
This work is primarily based on the [PRACTISE software](https://github.com/shaerer/PRACTISE).
- Härer, S., Bernhardt, M., and Schulz, K.: PRACTISE: PRACTISE V.2.1. Zenodo, doi:10.5281/zenodo.35646, 2015.
- Härer, S., Bernhardt, M., and Schulz, K.: PRACTISE – Photo Rectification And ClassificaTIon SoftwarE (V.2.1), Geosci. Model Dev., 9, 307-321, doi:10.5194/gmd-9-307-2016, 2016.

I also want to give special thanks to Gerhard Keuschnig & Florian Radlherr from [foto-webcam.eu](https://www.foto-webcam.eu), who provide a great system for high-resolution webcam images. All images used here are provided by their website.
