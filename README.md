# georef_webcam <img width="429" align="right" src="https://github.com/SebBuchelt/aux_data/blob/master/hintereisferner_webcam.jpg"> <br /> <br /> <img src="https://github.com/SebBuchelt/aux_data/blob/master/compare.gif" width="420" > 

<img width="300" align="left" src="https://github.com/SebBuchelt/aux_data/blob/master/Revision.png">
<br /> <br />

### Python toolbox to georeference webcam images 
- **Maintainer**: Sebastian Buchelt
- **Citation**: Buchelt, S. (2020-): georef_webcam 0.0.2, https://github.com/SebBuchelt/georef_webcam.
- **License**: CC-BY-NC-SA 4.0

## Overview

`georef_webcam` is a python package in development stage. It provides functionalities to georeference camera images without accurate knowlegde about needed input parameters.
This script enables the user to georeference images based on rough estimations about camera position, system parameters & looking direction. <br /> 
Additionally, Ground Control Points (GCPs) can be added to optimize the projection parameters for a better accuracy in geolocation. <br /> <br /> 
`georef_webcam` uses the Matlab scripts of the [`PRACTISE` package](https://github.com/shaerer/PRACTISE) to run the projection procedure. Based on its output, `georef_webcam` generates tif-files in the size of the original image with the coordinate position (Easting & Northing) of each pixel. Furthermore, a mask layer is generated to filter areas above the skyline. Based on those, a projected map of the camera image is produced.

#### Requirements
Please look in `requirements.txt` to see, which python libraries are required for the  `georef_webcam` package.
It is also mandatory to download `Octave`, as the core projection procedure is running on Matlab scripts from [`PRACTISE` package](https://github.com/shaerer/PRACTISE). `PRACTISE` is automatically downloaded by `georef_webcam`. <br />
So far this tool has been tested in Ubuntu 16.04, 18.04 & Windows 10. For Windows no guarantee for full functionality can be given.
<br /> <br />

## Getting started
#### The following description gives a short idea, how the procedure works and which steps you need to follow to get a good georeferencing result.
Download package to the directory you like.
Before starting the execution of the script, you should have the webcam image & the DEM file available for processing. <br />
<br />

The script georef_webcam.py requires only two input parameter: <br />
- `in_dir`: directory, where DEM, camera image and optionally gcp file are stored (can contain data in separate subdirectories).
- `out_dir`: directory, where output of `PRACTISE` and `georef_webcam` will be stored in subfolders.
- `name_of_run` (optional): define a name for projection run to recognize output (default: test_run). <br />
<br />

### Start georef_webcam:
1. Activate environment 
2. start script:
```bash
$ cd /path/to/georef_webcam/
$ cd /python_scripts/
$ python georef_webcam.py in_dir out_dir [-n name_of_run]
```

### Parameter collection:
Two options: <br />
If dictionary with projection parameters has been produced previously, these parameters can be read from json-file and edited. Otherwise new dictionary will be created:
```ba
Do you want to create a new set of projection parameters?  y/n
```
Result is stored as json-file under `in_dir/name_of_run.json`. <br />
**For further details about projection parameters and their definition, see [Parameters.md](https://github.com/SebBuchelt/georef_webcam/blob/master/Parameters.md).**

### Projection
Parameters are taken from dictionary and passed to `PRACTISE`, which is then executed. 
Afterwards, DEM points projected into image plane are plotted in Octave window and can be checked. Then you can decide between the following options:
```ba
Projection has been executed. 
What do you want to do next?
Please select one of the following options:
0: end procedure
1: edit projection input parameters and repeat projection procedure
2: produce georef_webcam output

Which of the options do you want to choose? 
```
- `0`: ends program
- `1`: edits projection parameters, stores in new json file (optionally) and then repeats the projection.
- `2`: moves on to output generation

### Output generation
The following output is produced and stored in `outdir/georef_result/name_of_run/` (_italic files are optional_):
- the original image
- `east_raster` & `north_raster`: two tif-files with the size of the image giving the easting, northing coordinate of each pixel
- _`alt_raster`: tif-file with altitude of each image pixel_
- _`dist_raster`: tif-file with distance of each image pixel to camera location_
- _`mask`: tif-file containing the mask layer_
- _`image_name_map.tif`: projected map of the camera image_

## Output examples
<p align="center"><img width="45%" src="https://github.com/SebBuchelt/aux_data/blob/master/Easting.jpg"> <img width="45%" src="https://github.com/SebBuchelt/aux_data/blob/master/Northing.jpg"> </p>
<p align="center"><sub>Figure 4: Final result: Coordinate rasters. </sub></p>
<br>

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

I also want to give special thanks to Gerhard Keuschnig & Florian Radlherr from [foto-webcam.eu](https://www.foto-webcam.eu), who provide a great system for high-resolution webcam images. The images used here are provided by their website.
